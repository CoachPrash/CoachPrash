"""Renderer for concept diagrams (MVT, IVT, EVT, Squeeze, Riemann sums, etc.)."""
import numpy as np
from sympy import Symbol, lambdify
from sympy.parsing.sympy_parser import parse_expr
from .style import *

x_sym = Symbol('x')


def _eval(expr_str, x_vals):
    expr = parse_expr(expr_str, local_dict={'x': x_sym})
    f = lambdify(x_sym, expr, modules=['numpy'])
    return np.array(f(x_vals), dtype=float)


def _render_riemann(ax, params, riemann_type):
    """Render Riemann sum rectangles."""
    func_str = params['function']
    a, b = params['a'], params['b']
    n = params.get('n', 4)

    x_plot = np.linspace(a - 0.5, b + 0.5, 500)
    y_plot = _eval(func_str, x_plot)
    ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2, zorder=4)

    dx = (b - a) / n
    for i in range(n):
        x_left = a + i * dx
        x_right = x_left + dx

        if riemann_type == 'riemann_left':
            h = float(_eval(func_str, np.array([x_left]))[0])
        elif riemann_type == 'riemann_right':
            h = float(_eval(func_str, np.array([x_right]))[0])
        elif riemann_type == 'riemann_mid':
            h = float(_eval(func_str, np.array([(x_left + x_right) / 2]))[0])
        elif riemann_type == 'riemann_trap':
            h_left = float(_eval(func_str, np.array([x_left]))[0])
            h_right = float(_eval(func_str, np.array([x_right]))[0])
            # Draw trapezoid
            trap_x = [x_left, x_left, x_right, x_right]
            trap_y = [0, h_left, h_right, 0]
            ax.fill(trap_x, trap_y, alpha=0.3, color=ACCENT, edgecolor=PRIMARY, linewidth=1, zorder=3)
            continue

        rect = plt.Rectangle((x_left, 0), dx, h,
                            facecolor=ACCENT, edgecolor=PRIMARY,
                            alpha=0.3, linewidth=1, zorder=3)
        ax.add_patch(rect)


def _render_mvt(ax, params):
    """Render Mean Value Theorem illustration."""
    func_str = params['function']
    a, b = params['a'], params['b']

    x_plot = np.linspace(a - 0.5, b + 0.5, 500)
    y_plot = _eval(func_str, x_plot)
    ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2, zorder=4, label='f(x)')

    # Secant line
    fa = float(_eval(func_str, np.array([a]))[0])
    fb = float(_eval(func_str, np.array([b]))[0])
    secant_slope = (fb - fa) / (b - a)
    secant_y = fa + secant_slope * (x_plot - a)
    ax.plot(x_plot, secant_y, '--', color=SECONDARY, linewidth=1.5,
            label='Secant line', zorder=3)

    # Find c where f'(c) = secant slope (approximate)
    from sympy import diff
    expr = parse_expr(func_str, local_dict={'x': x_sym})
    fprime = diff(expr, x_sym)
    f_prime = lambdify(x_sym, fprime, modules=['numpy'])
    x_search = np.linspace(a + 0.01, b - 0.01, 1000)
    slopes = f_prime(x_search)
    c_idx = np.argmin(np.abs(slopes - secant_slope))
    c = x_search[c_idx]
    fc = float(_eval(func_str, np.array([c]))[0])

    # Tangent line at c
    tangent_y = fc + secant_slope * (x_plot - c)
    ax.plot(x_plot, tangent_y, '--', color=SUCCESS, linewidth=1.5,
            label=f'Tangent at c={c:.1f}', zorder=3)

    # Mark points
    ax.plot([a, b, c], [fa, fb, fc], 'o', color=PRIMARY, markersize=7, zorder=5)
    ax.annotate(f'a={a}', xy=(a, fa), xytext=(-15, 10), textcoords='offset points',
               fontsize=ANNOTATION_SIZE)
    ax.annotate(f'b={b}', xy=(b, fb), xytext=(5, 10), textcoords='offset points',
               fontsize=ANNOTATION_SIZE)
    ax.annotate(f'c', xy=(c, fc), xytext=(5, -15), textcoords='offset points',
               fontsize=ANNOTATION_SIZE, color=SUCCESS, fontweight='bold')

    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')


def _render_ivt(ax, params):
    """Render Intermediate Value Theorem illustration."""
    func_str = params['function']
    a, b = params['a'], params['b']

    x_plot = np.linspace(a - 0.5, b + 0.5, 500)
    y_plot = _eval(func_str, x_plot)
    ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2, zorder=4)

    fa = float(_eval(func_str, np.array([a]))[0])
    fb = float(_eval(func_str, np.array([b]))[0])

    # Target value between fa and fb
    target = params.get('target', (fa + fb) / 2)
    ax.axhline(y=target, color=ACCENT, linestyle='--', linewidth=1.5,
              label=f'y = {target}', zorder=3)

    # Find intersection
    x_fine = np.linspace(a, b, 1000)
    y_fine = _eval(func_str, x_fine)
    c_idx = np.argmin(np.abs(y_fine - target))
    c = x_fine[c_idx]

    ax.plot([a, b], [fa, fb], 'o', color=PRIMARY, markersize=7, zorder=5)
    ax.plot(c, target, 'o', color=SECONDARY, markersize=8, zorder=5)
    ax.axvline(x=c, color=SECONDARY, linestyle=':', linewidth=1, alpha=0.5)

    ax.annotate(f'f(a)={fa:.1f}', xy=(a, fa), xytext=(-15, 10), textcoords='offset points',
               fontsize=ANNOTATION_SIZE)
    ax.annotate(f'f(b)={fb:.1f}', xy=(b, fb), xytext=(5, 10), textcoords='offset points',
               fontsize=ANNOTATION_SIZE)
    ax.annotate(f'c', xy=(c, target), xytext=(5, -15), textcoords='offset points',
               fontsize=ANNOTATION_SIZE, color=SECONDARY, fontweight='bold')
    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')


def _render_evt(ax, params):
    """Render Extreme Value Theorem illustration."""
    func_str = params['function']
    a, b = params['a'], params['b']

    x_plot = np.linspace(a, b, 500)
    y_plot = _eval(func_str, x_plot)
    ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2, zorder=4)

    # Find global max and min on [a,b]
    max_idx = np.argmax(y_plot)
    min_idx = np.argmin(y_plot)

    ax.plot(x_plot[max_idx], y_plot[max_idx], 'v', color=SECONDARY, markersize=10,
           zorder=5, label=f'Max = {y_plot[max_idx]:.1f}')
    ax.plot(x_plot[min_idx], y_plot[min_idx], '^', color=SUCCESS, markersize=10,
           zorder=5, label=f'Min = {y_plot[min_idx]:.1f}')

    # Mark endpoints
    ax.plot([x_plot[0], x_plot[-1]], [y_plot[0], y_plot[-1]], 'o',
           color=PRIMARY, markersize=7, zorder=5)

    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')


def _render_squeeze(ax, params):
    """Render Squeeze Theorem illustration."""
    functions = params.get('functions', [])
    x_range = params.get('x_range', [-2, 2])

    x_plot = np.linspace(x_range[0], x_range[1], 500)

    colors_list = [SUCCESS, PRIMARY, SECONDARY]
    labels = ['g(x) (lower)', 'f(x)', 'h(x) (upper)']

    for i, func in enumerate(functions):
        y = _eval(func['expr'], x_plot)
        label = func.get('label', labels[i] if i < len(labels) else '')
        color = func.get('color', colors_list[i % len(colors_list)])
        ax.plot(x_plot, y, color=color, linewidth=2, label=label, zorder=3+i)

    # Mark squeeze point
    squeeze_x = params.get('squeeze_at', 0)
    ax.axvline(x=squeeze_x, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')


def render(entry, output_dir):
    """Render a concept diagram."""
    params = entry['params']
    fig, ax = create_figure()

    diagram_type = params.get('type', '')

    if diagram_type.startswith('riemann_'):
        _render_riemann(ax, params, diagram_type)
    elif diagram_type == 'mvt':
        _render_mvt(ax, params)
    elif diagram_type == 'ivt':
        _render_ivt(ax, params)
    elif diagram_type == 'evt':
        _render_evt(ax, params)
    elif diagram_type == 'squeeze':
        _render_squeeze(ax, params)
    else:
        # Generic: just plot the function with any special markers
        func_str = params.get('function', 'x')
        x_range = params.get('x_range', [-5, 5])
        x_plot = np.linspace(x_range[0], x_range[1], 500)
        y_plot = _eval(func_str, x_plot)
        ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2, zorder=3)

    x_range = params.get('x_range', ax.get_xlim())
    y_range = params.get('y_range', None)
    if isinstance(x_range, list):
        ax.set_xlim(x_range[0] - 0.5, x_range[-1] + 0.5)
    if y_range:
        ax.set_ylim(y_range)

    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)

    add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path
