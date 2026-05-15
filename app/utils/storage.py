import os
import boto3
from botocore.config import Config


def _get_client():
    """Get an S3 client configured for Railway Storage Bucket."""
    endpoint = os.environ.get('AWS_ENDPOINT_URL')
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

    if not all([endpoint, access_key, secret_key]):
        raise RuntimeError(
            'Railway Bucket not configured. Set AWS_ENDPOINT_URL, '
            'AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY.'
        )

    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version='s3v4'),
    )


def _bucket_name():
    name = os.environ.get('AWS_S3_BUCKET_NAME')
    if not name:
        raise RuntimeError('AWS_S3_BUCKET_NAME env var not set.')
    return name


def upload_file(file_obj, key, content_type=None):
    """Upload a file-like object to the bucket."""
    client = _get_client()
    extra = {}
    if content_type:
        extra['ContentType'] = content_type
    client.upload_fileobj(file_obj, _bucket_name(), key, ExtraArgs=extra)
    return key


def get_presigned_url(key, expires_in=3600):
    """Generate a presigned URL for a bucket object (default 1hr expiry)."""
    client = _get_client()
    return client.generate_presigned_url(
        'get_object',
        Params={'Bucket': _bucket_name(), 'Key': key},
        ExpiresIn=expires_in,
    )


def delete_file(key):
    """Delete a file from the bucket."""
    client = _get_client()
    client.delete_object(Bucket=_bucket_name(), Key=key)


def list_files(prefix=''):
    """List files in the bucket under a prefix."""
    client = _get_client()
    result = client.list_objects_v2(Bucket=_bucket_name(), Prefix=prefix)
    files = []
    for obj in result.get('Contents', []):
        files.append({
            'key': obj['Key'],
            'size': obj['Size'],
            'last_modified': obj['LastModified'],
        })
    return files
