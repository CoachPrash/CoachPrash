"""Renderer for parametric and polar curve diagrams."""
import numpy as np
from sympy import Symbol, lambdify, pi
from sympy.parsing.sympy_parser import parse_expr
from .style import *

t_sym = Symbol('t')
theta_sym = Symbol('theta')


def render(entry, output_dir):
    """Render a parametric or polar curve."""
    params = entry['params']
    fig, ax = create_figure()

    curve_type = params.get('type', 'parametric')

    if curve_type == 'parametric':
        _render_parametric(ax, params)
    elif curve_type == 'polar':
        fig, ax = plt.subplots(figsize=FIG_SIZE, subplot_kw={'projection': 'polar'})
        fig.patch.set_facecolor(BG_COLOR)
        _render_polar(ax, params)

    add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path


def _render_parametric(ax, params):
    """Render a parametric curve x(t), y(t)."""
    p = params.get('parametric', {})
    x_expr_str = p.get('x_expr', 'cos(t)')
    y_expr_str = p.get('y_expr', 'sin(t)')
    t_range = p.get('t_range', [0, '2*pi'])

    # Parse range (may contain pi)
    t_start = float(parse_expr(str(t_range[0])))
    t_end = float(parse_expr(str(t_range[1])))

    t_vals = np.linspace(t_start, t_end, 500)

    x_expr = parse_expr(x_expr_str, local_dict={'t': t_sym})
    y_expr = parse_expr(y_expr_str, local_dict={'t': t_sym})

    x_func = lambdify(t_sym, x_expr, modules=['numpy'])
    y_func = lambdify(t_sym, y_expr, modules=['numpy'])

    x_vals = np.array(x_func(t_vals), dtype=float)
    y_vals = np.array(y_func(t_vals), dtype=float)

    ax.plot(x_vals, y_vals, color=PRIMARY, linewidth=2, zorder=3)

    # Add direction arrows
    n_arrows = params.get('n_arrows', 5)
    arrow_indices = np.linspace(0, len(t_vals)-2, n_arrows, dtype=int)
    for idx in arrow_indices:
        dx = x_vals[idx+1] - x_vals[idx]
        dy = y_vals[idx+1] - y_vals[idx]
        ax.annotate('', xy=(x_vals[idx+1], y_vals[idx+1]),
                   xytext=(x_vals[idx], y_vals[idx]),
                   arrowprops=dict(arrowstyle='->', color=SECONDARY, lw=1.5))

    # Mark start/end
    ax.plot(x_vals[0], y_vals[0], 'o', color=SUCCESS, markersize=8,
           label='Start', zorder=5)
    ax.plot(x_vals[-1], y_vals[-1], 's', color=SECONDARY, markersize=8,
           label='End', zorder=5)

    ax.set_xlabel('x', fontsize=LABEL_SIZE)
    ax.set_ylabel('y', fontsize=LABEL_SIZE)
    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)
    ax.set_aspect('equal', adjustable='datalim')
    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')


def _render_polar(ax, params):
    """Render a polar curve r(theta)."""
    p = params.get('polar', {})
    r_expr_str = p.get('r_expr', '1 + cos(theta)')
    theta_range = p.get('theta_range', [0, '2*pi'])

    theta_start = float(parse_expr(str(theta_range[0])))
    theta_end = float(parse_expr(str(theta_range[1])))

    theta_vals = np.linspace(theta_start, theta_end, 500)

    r_expr = parse_expr(r_expr_str, local_dict={'theta': theta_sym})
    r_func = lambdify(theta_sym, r_expr, modules=['numpy'])
    r_vals = np.array(r_func(theta_vals), dtype=float)

    ax.plot(theta_vals, r_vals, color=PRIMARY, linewidth=2, zorder=3)

    # Shade region if requested
    if params.get('shade', False):
        ax.fill(theta_vals, r_vals, alpha=0.2, color=ACCENT, zorder=2)

    # Shade between two polar curves
    if 'polar2' in params:
        p2 = params['polar2']
        r2_expr = parse_expr(p2['r_expr'], local_dict={'theta': theta_sym})
        r2_func = lambdify(theta_sym, r2_expr, modules=['numpy'])
        r2_vals = np.array(r2_func(theta_vals), dtype=float)
        ax.plot(theta_vals, r2_vals, color=SECONDARY, linewidth=2, zorder=3)
        ax.fill_between(theta_vals, r_vals, r2_vals, alpha=0.2, color=ACCENT, zorder=2)

    ax.set_facecolor(BG_COLOR)

    # Show only every other radial tick label to prevent overlap
    for i, label in enumerate(ax.get_yticklabels()):
        if i % 2 == 1:
            label.set_visible(False)
