import re
import os
from markupsafe import Markup


def register_bucket_filter(app):
    """Register a Jinja2 filter that converts data-bucket-key attributes to presigned URLs."""

    @app.template_filter('resolve_bucket_keys')
    def resolve_bucket_keys(html_string):
        """Replace <img data-bucket-key='...' /> with presigned URLs from Railway Bucket."""
        if not html_string or 'data-bucket-key' not in html_string:
            return html_string

        # Only attempt if bucket is configured
        if not os.environ.get('AWS_ENDPOINT_URL'):
            return html_string

        from app.utils.storage import get_presigned_url

        def replace_key(match):
            key = match.group(1)
            try:
                url = get_presigned_url(key)
                return f'src="{url}"'
            except Exception:
                return f'src="" alt="Image unavailable"'

        result = re.sub(r"data-bucket-key=['\"]([^'\"]+)['\"]", replace_key, html_string)
        return Markup(result)
