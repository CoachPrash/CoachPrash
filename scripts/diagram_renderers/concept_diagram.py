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


def _render_unit_circle(ax, params):
    """Render unit circle with special angles and (cos, sin) labels."""
    ax.set_aspect('equal')
    ax.grid(False)

    # Draw circle
    theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(theta), np.sin(theta), color=PRIMARY, linewidth=2, zorder=3)

    # Axes
    ax.axhline(y=0, color='black', linewidth=0.8, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.8, zorder=1)

    # Special angles
    special = params.get('angles', [
        0, np.pi/6, np.pi/4, np.pi/3, np.pi/2,
        2*np.pi/3, 3*np.pi/4, 5*np.pi/6, np.pi,
        7*np.pi/6, 5*np.pi/4, 4*np.pi/3, 3*np.pi/2,
        5*np.pi/3, 7*np.pi/4, 11*np.pi/6,
    ])

    angle_labels = {
        0: '0', np.pi/6: r'$\frac{\pi}{6}$', np.pi/4: r'$\frac{\pi}{4}$',
        np.pi/3: r'$\frac{\pi}{3}$', np.pi/2: r'$\frac{\pi}{2}$',
        2*np.pi/3: r'$\frac{2\pi}{3}$', 3*np.pi/4: r'$\frac{3\pi}{4}$',
        5*np.pi/6: r'$\frac{5\pi}{6}$', np.pi: r'$\pi$',
        7*np.pi/6: r'$\frac{7\pi}{6}$', 5*np.pi/4: r'$\frac{5\pi}{4}$',
        4*np.pi/3: r'$\frac{4\pi}{3}$', 3*np.pi/2: r'$\frac{3\pi}{2}$',
        5*np.pi/3: r'$\frac{5\pi}{3}$', 7*np.pi/4: r'$\frac{7\pi}{4}$',
        11*np.pi/6: r'$\frac{11\pi}{6}$',
    }

    show_coords = params.get('show_coordinates', True)

    for a in special:
        cx, cy = np.cos(a), np.sin(a)
        ax.plot(cx, cy, 'o', color=SECONDARY, markersize=5, zorder=5)
        # Radial line
        ax.plot([0, cx], [0, cy], color='#94A3B8', linewidth=0.5, zorder=2)

        # Label position (push outward)
        offset = 1.35 if show_coords else 1.2
        lx, ly = offset * cx, offset * cy
        closest = min(angle_labels.keys(), key=lambda k: abs(k - a))
        if abs(closest - a) < 0.01:
            label = angle_labels[closest]
            if show_coords:
                coord_str = f'({cx:.2g}, {cy:.2g})'
                label = f'{label}\n{coord_str}'
            ax.text(lx, ly, label, fontsize=7, ha='center', va='center',
                    color=TEXT_COLOR)

    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.8, 1.8)
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([-1, 0, 1])


def _render_end_behavior(ax, params):
    """Render 2x2 grid showing polynomial end behavior cases."""
    ax.axis('off')
    ax.grid(False)
    fig = ax.get_figure()
    fig.clear()

    cases = [
        ('Even degree, positive LC', 'x**4', [-2, 2], r'$a_n > 0$, even'),
        ('Even degree, negative LC', '-x**4', [-2, 2], r'$a_n < 0$, even'),
        ('Odd degree, positive LC', 'x**3', [-2, 2], r'$a_n > 0$, odd'),
        ('Odd degree, negative LC', '-x**3', [-2, 2], r'$a_n < 0$, odd'),
    ]

    for i, (title, expr_str, xr, subtitle) in enumerate(cases):
        sub_ax = fig.add_subplot(2, 2, i + 1)
        x_plot = np.linspace(xr[0], xr[1], 200)
        y_plot = _eval(expr_str, x_plot)
        sub_ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2)
        sub_ax.axhline(y=0, color='black', linewidth=0.5)
        sub_ax.axvline(x=0, color='black', linewidth=0.5)
        sub_ax.set_title(subtitle, fontsize=9, color=TEXT_COLOR)
        sub_ax.tick_params(labelsize=7)
        sub_ax.grid(True, linestyle='--', alpha=0.3, color=GRID_COLOR)
        for spine in sub_ax.spines.values():
            spine.set_color('#94A3B8')

    fig.suptitle(params.get('title', 'Polynomial End Behavior'),
                 fontsize=TITLE_SIZE, fontweight='bold', color=TEXT_COLOR)
    fig.tight_layout(rect=[0, 0, 1, 0.93])


def _render_composition_flow(ax, params):
    """Render box-and-arrow composition diagram."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis('off')
    ax.grid(False)

    boxes = params.get('boxes', [
        {'label': 'x', 'x': 0.5},
        {'label': 'g(x)', 'x': 3.5},
        {'label': 'f(g(x))', 'x': 7.0},
    ])
    colors_list = [ACCENT, SUCCESS, SECONDARY]

    for i, box in enumerate(boxes):
        bx = box['x']
        color = colors_list[i % len(colors_list)]
        rect = plt.Rectangle((bx, 0.8), 2.0, 1.4, linewidth=2,
                              edgecolor=color, facecolor=color, alpha=0.15,
                              zorder=3)
        ax.add_patch(rect)
        ax.text(bx + 1.0, 1.5, box['label'], fontsize=14, ha='center',
                va='center', fontweight='bold', color=TEXT_COLOR, zorder=4)

        # Arrow to next box
        if i < len(boxes) - 1:
            next_bx = boxes[i + 1]['x']
            ax.annotate('', xy=(next_bx, 1.5), xytext=(bx + 2.0, 1.5),
                        arrowprops=dict(arrowstyle='->', color=PRIMARY,
                                        lw=2, mutation_scale=20),
                        zorder=5)

    # Labels above arrows
    arrow_labels = params.get('arrow_labels', ['apply g', 'apply f'])
    for i, label in enumerate(arrow_labels):
        if i < len(boxes) - 1:
            mid_x = (boxes[i]['x'] + 2.0 + boxes[i + 1]['x']) / 2
            ax.text(mid_x, 2.4, label, fontsize=10, ha='center', va='center',
                    color=PRIMARY, style='italic')


def _render_conic_section(ax, params):
    """Render a conic section with labeled features."""
    conic_type = params.get('conic_type', 'ellipse')
    ax.set_aspect('equal')

    if conic_type == 'ellipse':
        a = params.get('a', 3)
        b = params.get('b', 2)
        h = params.get('h', 0)
        k = params.get('k', 0)
        t = np.linspace(0, 2 * np.pi, 300)
        ax.plot(h + a * np.cos(t), k + b * np.sin(t), color=PRIMARY, linewidth=2, zorder=3)
        c_val = np.sqrt(abs(a**2 - b**2))
        if a >= b:
            ax.plot([h - c_val, h + c_val], [k, k], 'o', color=SECONDARY,
                    markersize=6, zorder=5, label='Foci')
            # Major/minor axes
            ax.plot([h - a, h + a], [k, k], '--', color='#94A3B8', linewidth=1, zorder=2)
            ax.plot([h, h], [k - b, k + b], '--', color='#94A3B8', linewidth=1, zorder=2)
        else:
            ax.plot([h, h], [k - c_val, k + c_val], 'o', color=SECONDARY,
                    markersize=6, zorder=5, label='Foci')
        ax.plot(h, k, '+', color=TEXT_COLOR, markersize=8, zorder=5)
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

    elif conic_type == 'hyperbola':
        a = params.get('a', 2)
        b = params.get('b', 1.5)
        h = params.get('h', 0)
        k = params.get('k', 0)
        orientation = params.get('orientation', 'horizontal')
        t = np.linspace(-2, 2, 300)
        if orientation == 'horizontal':
            # Right branch
            ax.plot(h + a * np.cosh(t), k + b * np.sinh(t), color=PRIMARY, linewidth=2, zorder=3)
            # Left branch
            ax.plot(h - a * np.cosh(t), k + b * np.sinh(t), color=PRIMARY, linewidth=2, zorder=3)
            # Asymptotes
            x_asym = np.linspace(h - 5, h + 5, 100)
            ax.plot(x_asym, k + (b/a) * (x_asym - h), '--', color=ACCENT, linewidth=1, zorder=2)
            ax.plot(x_asym, k - (b/a) * (x_asym - h), '--', color=ACCENT, linewidth=1, zorder=2,
                    label='Asymptotes')
        else:
            ax.plot(h + b * np.sinh(t), k + a * np.cosh(t), color=PRIMARY, linewidth=2, zorder=3)
            ax.plot(h + b * np.sinh(t), k - a * np.cosh(t), color=PRIMARY, linewidth=2, zorder=3)
            y_asym = np.linspace(k - 5, k + 5, 100)
            ax.plot(h + (b/a) * (y_asym - k), y_asym, '--', color=ACCENT, linewidth=1, zorder=2)
            ax.plot(h - (b/a) * (y_asym - k), y_asym, '--', color=ACCENT, linewidth=1, zorder=2,
                    label='Asymptotes')
        c_val = np.sqrt(a**2 + b**2)
        if orientation == 'horizontal':
            ax.plot([h - c_val, h + c_val], [k, k], 'o', color=SECONDARY,
                    markersize=6, zorder=5, label='Foci')
        else:
            ax.plot([h, h], [k - c_val, k + c_val], 'o', color=SECONDARY,
                    markersize=6, zorder=5, label='Foci')
        ax.plot(h, k, '+', color=TEXT_COLOR, markersize=8, zorder=5)
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

    elif conic_type == 'parabola':
        p = params.get('p', 1)
        orientation = params.get('orientation', 'vertical')
        if orientation == 'vertical':
            t = np.linspace(-4, 4, 300)
            ax.plot(t, t**2 / (4 * p), color=PRIMARY, linewidth=2, zorder=3)
            ax.plot(0, p, 'o', color=SECONDARY, markersize=6, zorder=5, label='Focus')
            ax.axhline(y=-p, color=ACCENT, linestyle='--', linewidth=1, zorder=2,
                       label='Directrix')
        else:
            t = np.linspace(-4, 4, 300)
            ax.plot(t**2 / (4 * p), t, color=PRIMARY, linewidth=2, zorder=3)
            ax.plot(p, 0, 'o', color=SECONDARY, markersize=6, zorder=5, label='Focus')
            ax.axvline(x=-p, color=ACCENT, linestyle='--', linewidth=1, zorder=2,
                       label='Directrix')
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)


def _render_matrix_transform(ax, params):
    """Render before/after grid transformation by a 2x2 matrix."""
    ax.set_aspect('equal')
    matrix = params.get('matrix', [[1, 0], [0, 1]])
    m = np.array(matrix, dtype=float)

    # Unit square vertices
    verts = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])

    # Before (dashed)
    ax.plot(verts[:, 0], verts[:, 1], '--', color='#94A3B8', linewidth=1.5, zorder=2,
            label='Original')
    ax.fill(verts[:-1, 0], verts[:-1, 1], alpha=0.08, color='#94A3B8')

    # After (solid)
    transformed = (m @ verts.T).T
    ax.plot(transformed[:, 0], transformed[:, 1], '-', color=PRIMARY, linewidth=2, zorder=3,
            label='Transformed')
    ax.fill(transformed[:-1, 0], transformed[:-1, 1], alpha=0.15, color=PRIMARY)

    # Label vertices of transformed shape
    labels = params.get('vertex_labels', ['O', 'A', 'B', 'C'])
    for i in range(4):
        tx, ty = transformed[i]
        ax.plot(tx, ty, 'o', color=SECONDARY, markersize=5, zorder=5)
        ax.annotate(labels[i], xy=(tx, ty), xytext=(5, 5),
                    textcoords='offset points', fontsize=ANNOTATION_SIZE,
                    color=TEXT_COLOR)

    # Determinant annotation
    det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
    ax.text(0.02, 0.98, f'det = {det:.1f}\nArea scale = |{det:.1f}|',
            transform=ax.transAxes, fontsize=ANNOTATION_SIZE - 1,
            va='top', ha='left', color=TEXT_COLOR,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9C4',
                      edgecolor='#F59E0B', alpha=0.9))

    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)
    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')


def _render_implicit_curve(ax, params):
    """Render an implicit curve F(x,y)=0 using contour."""
    from sympy import Symbol as Sym
    from sympy.parsing.sympy_parser import parse_expr as pe
    from sympy import lambdify as lb

    ax.set_aspect('equal')

    expr_str = params.get('expression', 'x**2 + y**2 - 1')
    x_range = params.get('x_range', [-5, 5])
    y_range = params.get('y_range', [-5, 5])

    xs = Sym('x')
    ys = Sym('y')
    expr = pe(expr_str, local_dict={'x': xs, 'y': ys})
    f = lb((xs, ys), expr, modules=['numpy'])

    xv = np.linspace(x_range[0], x_range[1], 400)
    yv = np.linspace(y_range[0], y_range[1], 400)
    X, Y = np.meshgrid(xv, yv)
    Z = f(X, Y)

    ax.contour(X, Y, Z, levels=[0], colors=[PRIMARY], linewidths=2, zorder=3)

    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)

    # Optional labels for features
    for pt in params.get('points', []):
        style = 'o' if pt.get('style', 'filled') == 'filled' else 'o'
        ax.plot(pt['x'], pt['y'], style, color=SECONDARY, markersize=6, zorder=5)
        if 'label' in pt:
            ax.annotate(pt['label'], xy=(pt['x'], pt['y']),
                        xytext=(8, 8), textcoords='offset points',
                        fontsize=ANNOTATION_SIZE, color=TEXT_COLOR)


def _render_polar_grid(ax, params):
    """Render a polar coordinate system with a labeled point."""
    ax.axis('off')
    ax.grid(False)
    fig = ax.get_figure()
    fig.clear()

    polar_ax = fig.add_subplot(111, projection='polar')
    polar_ax.set_facecolor(BG_COLOR)

    # Plot the example point
    r = params.get('r', 3)
    theta = params.get('theta', np.pi / 4)
    polar_ax.plot(theta, r, 'o', color=SECONDARY, markersize=8, zorder=5)
    polar_ax.plot([0, theta], [0, r], '-', color=PRIMARY, linewidth=1.5, zorder=4)

    # Label
    label = params.get('point_label', f'({r}, $\\pi/4$)')
    polar_ax.annotate(label, xy=(theta, r), xytext=(10, 10),
                      textcoords='offset points', fontsize=ANNOTATION_SIZE + 1,
                      color=SECONDARY, fontweight='bold')

    polar_ax.set_rmax(params.get('r_max', r + 1))
    polar_ax.tick_params(labelsize=TICK_SIZE - 2)
    fig.suptitle(params.get('title', 'Polar Coordinate System'),
                 fontsize=TITLE_SIZE, fontweight='bold', color=TEXT_COLOR)


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
    elif diagram_type == 'unit_circle':
        _render_unit_circle(ax, params)
    elif diagram_type == 'end_behavior':
        _render_end_behavior(ax, params)
    elif diagram_type == 'composition_flow':
        _render_composition_flow(ax, params)
    elif diagram_type == 'conic_section':
        _render_conic_section(ax, params)
    elif diagram_type == 'matrix_transform':
        _render_matrix_transform(ax, params)
    elif diagram_type == 'implicit_curve':
        _render_implicit_curve(ax, params)
    elif diagram_type == 'polar_grid':
        _render_polar_grid(ax, params)
    else:
        # Generic: just plot the function with any special markers
        func_str = params.get('function', 'x')
        x_range = params.get('x_range', [-5, 5])
        x_plot = np.linspace(x_range[0], x_range[1], 500)
        y_plot = _eval(func_str, x_plot)
        ax.plot(x_plot, y_plot, color=PRIMARY, linewidth=2, zorder=3)

    # Skip axis setup for types that manage their own figure
    if diagram_type not in ('end_behavior', 'polar_grid'):
        x_range = params.get('x_range', ax.get_xlim())
        y_range = params.get('y_range', None)
        if isinstance(x_range, list):
            ax.set_xlim(x_range[0] - 0.5, x_range[-1] + 0.5)
        if y_range:
            ax.set_ylim(y_range)

        if diagram_type not in ('composition_flow',):
            ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
            ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)

        add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path
