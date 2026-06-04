"""Renderer for shaded region diagrams (area under/between curves)."""
import numpy as np
from sympy import Symbol
from sympy.parsing.sympy_parser import parse_expr
from sympy import lambdify
from .style import *

x_sym = Symbol('x')


def _eval_expr(expr_str, x_vals):
    """Parse and evaluate expression, broadcasting constants to array shape."""
    expr = parse_expr(expr_str, local_dict={'x': x_sym})
    f = lambdify(x_sym, expr, modules=['numpy'])
    y = np.array(f(x_vals), dtype=float)
    # Broadcast scalar constants to match x_vals shape
    if y.ndim == 0:
        y = np.full_like(x_vals, float(y))
    y[~np.isfinite(y)] = np.nan
    return y


def render(entry, output_dir):
    """Render a shaded region diagram."""
    params = entry['params']
    fig, ax = create_figure()

    x_range = params.get('x_range', [-5, 5])
    y_range = params.get('y_range', [-5, 5])

    x_vals = np.linspace(x_range[0], x_range[1], 1000)
    functions = params.get('functions', [])

    y_arrays = []
    for i, func in enumerate(functions):
        color = func.get('color', COLORS[i % len(COLORS)])
        label = func.get('label', func.get('expr', ''))
        y = _eval_expr(func['expr'], x_vals)
        y_arrays.append(y)
        ax.plot(x_vals, y, color=color, linewidth=2, label=label, zorder=3)

    # Shade the region
    shade_x = params.get('shade_x_range', x_range)
    shade_mask = (x_vals >= shade_x[0]) & (x_vals <= shade_x[1])
    x_shade = x_vals[shade_mask]

    if params.get('shade_between') and len(y_arrays) >= 2:
        # Area between two curves
        y1_shade = y_arrays[0][shade_mask]
        y2_shade = y_arrays[1][shade_mask]
        ax.fill_between(x_shade, y1_shade, y2_shade,
                       alpha=0.3, color=ACCENT, zorder=2)
    elif len(y_arrays) >= 1:
        # Area under single curve (above x-axis)
        y_shade = y_arrays[0][shade_mask]
        y_base = params.get('shade_base', 0)
        ax.fill_between(x_shade, y_base, y_shade,
                       alpha=0.3, color=ACCENT, zorder=2)

    # Draw shade boundaries
    ax.axvline(x=shade_x[0], color='gray', linestyle=':', linewidth=1, zorder=2)
    ax.axvline(x=shade_x[1], color='gray', linestyle=':', linewidth=1, zorder=2)

    ax.set_xlim(x_range)
    ax.set_ylim(y_range)
    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)

    if any(f.get('label') for f in functions):
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

    add_title(ax, params.get('title', ''))

    # Add a/b labels on x-axis
    ax.annotate(f'a={shade_x[0]}', xy=(shade_x[0], 0), fontsize=TICK_SIZE,
               ha='center', va='top', xytext=(0, -15), textcoords='offset points')
    ax.annotate(f'b={shade_x[1]}', xy=(shade_x[1], 0), fontsize=TICK_SIZE,
               ha='center', va='top', xytext=(0, -15), textcoords='offset points')

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path
