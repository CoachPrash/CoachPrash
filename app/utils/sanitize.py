import nh3

ALLOWED_TAGS = {
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr',
    'strong', 'em', 'b', 'i', 'u', 'sub', 'sup', 'code', 'pre',
    'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody',
    'tr', 'th', 'td', 'blockquote', 'div', 'span',
    'figure', 'figcaption',
}

ALLOWED_ATTRS = {
    'a': {'href', 'title', 'target'},
    'img': {'src', 'alt', 'title', 'data-bucket-key', 'loading', 'width', 'height'},
    'div': {'class'},
    'span': {'class'},
    'code': {'class'},
    'pre': {'class'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
}


def sanitize_html(raw):
    """Sanitize HTML content, stripping dangerous tags like <script> while
    preserving educational content markup (headings, lists, images, code blocks,
    callout divs, etc.)."""
    if not raw:
        return raw
    return nh3.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
