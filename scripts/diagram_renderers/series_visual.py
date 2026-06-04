"""Renderer for series and Taylor polynomial visualizations."""
import numpy as np
from sympy import Symbol, lambdify, series, sin, cos, exp, ln, factorial
from sympy.parsing.sympy_parser import parse_expr
from .style import *

x_sym = Symbol('x')

# Map common function names
FUNC_MAP = {
    'sin(x)': sin(x_sym),
    'cos(x)': cos(x_sym),
    'exp(x)': exp(x_sym),
    'ln(1+x)': ln(1 + x_sym),
    'e**x': exp(x_sym),
}


def render(entry, output_dir):
    """Render a series visualization."""
    params = entry['params']
    fig, ax = create_figure()

    vis_type = params.get('type', 'taylor')

    if vis_type == 'taylor':
        _render_taylor(ax, params)
    elif vis_type == 'partial_sum':
        _render_partial_sums(ax, params)
    elif vis_type == 'convergence':
        _render_convergence(ax, params)
    else:
        _render_taylor(ax, params)

    add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path


def _render_taylor(ax, params):
    """Render Taylor polynomial approximations overlaid on original function."""
    func_str = params.get('function', 'sin(x)')
    center = params.get('center', 0)
    degrees = params.get('degrees', [1, 3, 5])
    x_range = params.get('x_range', [-6, 6])

    # Get sympy expression
    if func_str in FUNC_MAP:
        expr = FUNC_MAP[func_str]
    else:
        expr = parse_expr(func_str, local_dict={'x': x_sym})

    x_vals = np.linspace(x_range[0], x_range[1], 500)

    # Plot original function
    f = lambdify(x_sym, expr, modules=['numpy'])
    y_orig = f(x_vals)
    ax.plot(x_vals, y_orig, color=PRIMARY, linewidth=2.5, label=f'f(x) = {func_str}', zorder=10)

    # Plot Taylor polynomials
    poly_colors = [ACCENT, SUCCESS, SECONDARY, '#7C3AED', '#0891B2']
    for i, deg in enumerate(degrees):
        taylor = series(expr, x_sym, center, n=deg+1).removeO()
        t_func = lambdify(x_sym, taylor, modules=['numpy'])
        y_taylor = t_func(x_vals)

        # Clip Taylor values to reasonable range
        y_range_val = max(abs(np.nanmin(y_orig)), abs(np.nanmax(y_orig))) * 2
        y_taylor = np.clip(y_taylor, -y_range_val, y_range_val)

        color = poly_colors[i % len(poly_colors)]
        ax.plot(x_vals, y_taylor, '--', color=color, linewidth=1.5,
               label=f'T_{deg}(x)', alpha=0.8, zorder=5+i)

    # Mark center point
    center_y = float(f(center))
    ax.plot(center, center_y, 'o', color=PRIMARY, markersize=8, zorder=11)

    y_lim = max(abs(np.nanmin(y_orig)), abs(np.nanmax(y_orig))) * 1.5
    ax.set_ylim(-y_lim, y_lim)
    ax.set_xlim(x_range)

    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)
    ax.legend(fontsize=LABEL_SIZE - 3, loc='best')


def _render_partial_sums(ax, params):
    """Render partial sums of a series converging to a value."""
    terms = params.get('n_terms', 20)
    series_type = params.get('series_type', 'geometric')

    if series_type == 'geometric':
        r = params.get('ratio', 0.5)
        partial = [sum(r**k for k in range(n+1)) for n in range(terms)]
        limit = 1 / (1 - r) if abs(r) < 1 else None
        title_suffix = f'r = {r}'
    elif series_type == 'alternating':
        partial = [sum((-1)**k / (k+1) for k in range(n+1)) for n in range(terms)]
        limit = np.log(2)
        title_suffix = 'alternating harmonic'
    else:
        partial = list(range(terms))
        limit = None
        title_suffix = ''

    n_vals = list(range(len(partial)))
    ax.stem(n_vals, partial, linefmt='-', markerfmt='o', basefmt='none')
    ax.scatter(n_vals, partial, color=PRIMARY, s=30, zorder=5)

    if limit is not None:
        ax.axhline(y=limit, color=SECONDARY, linestyle='--', linewidth=1.5,
                  label=f'Limit = {limit:.4f}')
        ax.legend(fontsize=LABEL_SIZE - 2)

    ax.set_xlabel('n', fontsize=LABEL_SIZE)
    ax.set_ylabel('S_n', fontsize=LABEL_SIZE)


def _render_convergence(ax, params):
    """Render interval of convergence visualization."""
    center = params.get('center', 0)
    radius = params.get('radius', 3)

    ax.axhline(y=0, color='black', linewidth=2)

    # Draw interval
    ax.plot([center - radius, center + radius], [0, 0],
           color=PRIMARY, linewidth=6, alpha=0.3, zorder=3)

    # Endpoints
    left_open = params.get('left_open', True)
    right_open = params.get('right_open', True)

    for x, is_open in [(center - radius, left_open), (center + radius, right_open)]:
        if is_open:
            ax.plot(x, 0, 'o', markersize=12, markerfacecolor='white',
                   markeredgecolor=PRIMARY, markeredgewidth=2, zorder=5)
        else:
            ax.plot(x, 0, 'o', markersize=12, markerfacecolor=PRIMARY,
                   markeredgecolor=PRIMARY, zorder=5)

    # Center
    ax.plot(center, 0, 'o', markersize=8, color=SECONDARY, zorder=5)
    ax.annotate(f'c = {center}', xy=(center, 0), xytext=(0, 20),
               textcoords='offset points', fontsize=ANNOTATION_SIZE,
               ha='center', color=SECONDARY)

    # Labels
    ax.annotate(f'R = {radius}', xy=(center, 0), xytext=(0, -25),
               textcoords='offset points', fontsize=ANNOTATION_SIZE,
               ha='center')

    ax.set_xlim(center - radius - 2, center + radius + 2)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_xlabel('x', fontsize=LABEL_SIZE)
