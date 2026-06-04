"""Renderer for function graph diagrams."""
import numpy as np
from sympy import sympify, lambdify, Symbol, Piecewise, oo
from sympy.parsing.sympy_parser import parse_expr
from .style import *

x_sym = Symbol('x')
t_sym = Symbol('t')


def _safe_eval(expr_str, x_vals):
    """Parse a sympy expression and evaluate over x_vals, handling discontinuities."""
    # Support both x and t as the independent variable
    if 't' in expr_str and 'x' not in expr_str:
        var = t_sym
        local = {'t': t_sym}
    else:
        var = x_sym
        local = {'x': x_sym}
    expr = parse_expr(expr_str, local_dict=local)
    f = lambdify(var, expr, modules=['numpy'])
    y_vals = np.array(f(x_vals), dtype=float)
    # Broadcast scalar constants to match x_vals shape
    if y_vals.ndim == 0:
        y_vals = np.full_like(x_vals, float(y_vals))
    # Replace inf/nan with nan for clean plotting
    y_vals[~np.isfinite(y_vals)] = np.nan
    return y_vals


def render(entry, output_dir):
    """Render a function graph from manifest entry params."""
    params = entry['params']
    fig, ax = create_figure()

    x_range = params.get('x_range', [-5, 5])
    y_range = params.get('y_range', [-5, 5])

    x_vals = np.linspace(x_range[0], x_range[1], 1000)

    # Plot functions
    functions = params.get('functions', [])
    for i, func in enumerate(functions):
        color = func.get('color', COLORS[i % len(COLORS)])
        label = func.get('label', None)
        y_vals = _safe_eval(func['expr'], x_vals)

        # Clip to y_range to avoid visual artifacts
        y_vals_clipped = np.where(
            (y_vals > y_range[1] * 1.5) | (y_vals < y_range[0] * 1.5),
            np.nan, y_vals
        )

        # For piecewise/discontinuous functions, detect jumps and break the line
        dy = np.abs(np.diff(y_vals_clipped))
        # Use median-based threshold: a jump is any step >> typical step size
        median_dy = np.nanmedian(dy[dy > 0]) if np.any(dy > 0) else 1
        threshold = max(median_dy * 20, 0.5)
        jumps = np.where(dy > threshold)[0]
        y_plot = y_vals_clipped.copy()
        for j in jumps:
            y_plot[j] = np.nan

        ax.plot(x_vals, y_plot, color=color, linewidth=2, label=label, zorder=3)

    # Draw asymptotes
    for asym in params.get('asymptotes', []):
        if asym['type'] == 'vertical':
            ax.axvline(x=asym['value'], color=SECONDARY, linestyle='--',
                      linewidth=1.5, alpha=0.7, zorder=2)
        elif asym['type'] == 'horizontal':
            ax.axhline(y=asym['value'], color=SECONDARY, linestyle='--',
                      linewidth=1.5, alpha=0.7, zorder=2)

    # Draw points (open circles = holes, filled = actual values)
    for pt in params.get('points', []):
        if pt['style'] == 'open':
            ax.plot(pt['x'], pt['y'], 'o', markersize=8, markerfacecolor='white',
                   markeredgecolor=PRIMARY, markeredgewidth=2, zorder=5)
        elif pt['style'] == 'filled':
            ax.plot(pt['x'], pt['y'], 'o', markersize=8, markerfacecolor=PRIMARY,
                   markeredgecolor=PRIMARY, markeredgewidth=2, zorder=5)

    # Add annotations
    for ann in params.get('annotations', []):
        ax.annotate(ann['text'], xy=tuple(ann['xy']),
                   fontsize=ANNOTATION_SIZE, color=TEXT_COLOR,
                   ha='center', va='bottom',
                   xytext=(0, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9C4',
                            edgecolor='#F59E0B', alpha=0.9))

    ax.set_xlim(x_range)
    ax.set_ylim(y_range)
    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)

    if any(f.get('label') for f in functions):
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

    add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path
