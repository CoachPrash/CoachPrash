"""Color utility for theme palette derivation.

Given 4 seed colors (primary, secondary, accent, bg), derives the full
set of 13 CSS custom properties used across CoachPrash.
"""

import colorsys


def hex_to_rgb(hex_str):
    """Convert '#RRGGBB' to (r, g, b) floats 0-1."""
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    """Convert (r, g, b) floats 0-1 to '#RRGGBB'."""
    return '#{:02X}{:02X}{:02X}'.format(
        int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
    )


def hex_to_hsl(hex_str):
    """Convert '#RRGGBB' to (h, s, l) where h is 0-360, s and l are 0-1."""
    r, g, b = hex_to_rgb(hex_str)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l


def hsl_to_hex(h, s, l):
    """Convert (h 0-360, s 0-1, l 0-1) to '#RRGGBB'."""
    h_norm = h / 360.0
    s = max(0, min(1, s))
    l = max(0, min(1, l))
    r, g, b = colorsys.hls_to_rgb(h_norm, l, s)
    return rgb_to_hex(r, g, b)


def lighten(hex_str, amount):
    """Lighten a color by blending toward white. amount 0-1."""
    r, g, b = hex_to_rgb(hex_str)
    r = r + (1 - r) * amount
    g = g + (1 - g) * amount
    b = b + (1 - b) * amount
    return rgb_to_hex(r, g, b)


def desaturate(hex_str, amount):
    """Reduce saturation by amount (0-1)."""
    h, s, l = hex_to_hsl(hex_str)
    s = s * (1 - amount)
    return hsl_to_hex(h, s, l)


def derive_palette(primary, secondary, accent, bg):
    """Derive full 13-variable CSS palette from 4 seed colors.

    Returns dict with keys matching CSS custom property names (without --).
    """
    r, g, b = hex_to_rgb(accent)
    accent_r = int(round(r * 255))
    accent_g = int(round(g * 255))
    accent_b = int(round(b * 255))

    text_secondary = desaturate(lighten(primary, 0.35), 0.4)

    return {
        'primary': primary,
        'secondary': secondary,
        'accent': accent,
        'bg': bg,
        'card_bg': '#FFFFFF',
        'text': primary,
        'text_secondary': text_secondary,
        'success': '#2D8659',
        'danger': '#DC3545',
        'border': lighten(primary, 0.82),
        'sidebar_bg': primary,
        'sidebar_text': 'rgba(255,255,255,0.9)',
        'sidebar_hover_bg': f'rgba({accent_r},{accent_g},{accent_b},0.2)',
    }


def palette_to_css_vars(palette):
    """Convert palette dict to CSS custom property declarations."""
    mapping = {
        'primary': '--primary',
        'secondary': '--secondary',
        'accent': '--accent',
        'bg': '--bg',
        'card_bg': '--card-bg',
        'text': '--text',
        'text_secondary': '--text-secondary',
        'success': '--success',
        'danger': '--danger',
        'border': '--border',
        'sidebar_bg': '--sidebar-bg',
        'sidebar_text': '--sidebar-text',
        'sidebar_hover_bg': '--sidebar-hover-bg',
    }
    lines = []
    for key, css_var in mapping.items():
        lines.append(f'    {css_var}: {palette[key]};')
    return '\n'.join(lines)
