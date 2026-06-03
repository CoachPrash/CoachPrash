import os
import re
import logging
import requests

logger = logging.getLogger(__name__)

API_URL = 'https://api.onecompiler.com/v1/run'
TIMEOUT = 15  # seconds for the HTTP request (OneCompiler handles execution timeout)
MAX_CODE_LENGTH = 5000

# Patterns that indicate potentially dangerous Java code
FORBIDDEN_PATTERNS = [
    r'\bRuntime\s*\.\s*getRuntime\b',
    r'\bProcessBuilder\b',
    r'\bSystem\s*\.\s*exit\b',
    r'\bjava\.io\.File\b',
    r'\bjava\.nio\b',
    r'\bjava\.net\b',
    r'\bjava\.lang\.reflect\b',
    r'\bClass\s*\.\s*forName\b',
    r'\bClassLoader\b',
    r'\bThread\s*\.\s*sleep\s*\(\s*\d{5,}',  # sleep > 10s
]


class OneCompilerError(Exception):
    pass


class CodeTooLongError(OneCompilerError):
    pass


class ForbiddenCodeError(OneCompilerError):
    pass


class QuotaExceededError(OneCompilerError):
    pass


def _get_api_key():
    key = os.environ.get('ONECOMPILER_API_KEY')
    if not key:
        raise OneCompilerError('ONECOMPILER_API_KEY environment variable not set')
    return key


def check_forbidden(source_code):
    for pattern in FORBIDDEN_PATTERNS:
        match = re.search(pattern, source_code)
        if match:
            raise ForbiddenCodeError(
                f'Forbidden code pattern detected: {match.group()}'
            )


def execute_java(source_code, stdin=''):
    """Execute Java code via OneCompiler API.

    Returns dict with keys: stdout, stderr, status, error,
    compilation_time, execution_time.
    """
    if len(source_code) > MAX_CODE_LENGTH:
        raise CodeTooLongError(
            f'Code exceeds {MAX_CODE_LENGTH} character limit '
            f'({len(source_code)} chars)'
        )

    check_forbidden(source_code)

    payload = {
        'language': 'java',
        'stdin': stdin,
        'files': [
            {
                'name': 'Solution.java',
                'content': source_code,
            }
        ],
    }

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': _get_api_key(),
        'User-Agent': 'CoachPrash/1.0',
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.Timeout:
        raise OneCompilerError('Code execution timed out')
    except requests.RequestException as e:
        logger.exception('OneCompiler API request failed')
        raise OneCompilerError(f'API request failed: {e}')

    data = resp.json()

    if data.get('error') == 'E002':
        raise QuotaExceededError('OneCompiler API quota exceeded')

    return {
        'stdout': (data.get('stdout') or '').rstrip('\n'),
        'stderr': data.get('stderr') or '',
        'status': data.get('status', 'failed'),
        'error': data.get('exception') or data.get('error') or '',
        'compilation_time': data.get('compilationTime', 0),
        'execution_time': data.get('executionTime', 0),
    }
