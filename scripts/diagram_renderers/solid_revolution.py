"""Renderer for solid of revolution diagrams (disc, washer, shell methods)."""
import numpy as np
from sympy import Symbol, lambdify
from sympy.parsing.sympy_parser import parse_expr
from .style import *

x_sym = Symbol('x')


def _eval(expr_str, x_vals):
    expr = parse_expr(expr_str, local_dict={'x': x_sym})
    f = lambdify(x_sym, expr, modules=['numpy'])
    return np.array(f(x_vals), dtype=float)


def render(entry, output_dir):
    """Render a solid of revolution diagram (2D cross-section view)."""
    params = entry['params']
    fig, ax = create_figure()

    func_str = params['function']
    x_range = params.get('x_range', [0, 4])
    axis = params.get('axis', 'x')  # Revolution axis
    method = params.get('method', 'disc')

    x_vals = np.linspace(x_range[0], x_range[1], 500)
    y_vals = _eval(func_str, x_vals)

    # Plot the function
    ax.plot(x_vals, y_vals, color=PRIMARY, linewidth=2, label='f(x)', zorder=4)

    if axis == 'x':
        # Show the region being revolved (shaded)
        ax.fill_between(x_vals, 0, y_vals, alpha=0.2, color=ACCENT, zorder=2)

        if method == 'disc':
            # Draw a few representative discs (as vertical lines)
            n_discs = 5
            disc_x = np.linspace(x_range[0] + 0.2, x_range[1] - 0.2, n_discs)
            for dx in disc_x:
                dy = float(_eval(func_str, np.array([dx]))[0])
                ax.plot([dx, dx], [0, dy], color=SECONDARY, linewidth=2, alpha=0.5, zorder=3)
                ax.plot([dx, dx], [0, -dy], color=SECONDARY, linewidth=2, alpha=0.3,
                       linestyle='--', zorder=3)

            # Mirror the curve below x-axis (showing revolution)
            ax.plot(x_vals, -y_vals, color=PRIMARY, linewidth=1.5, alpha=0.4,
                   linestyle='--', zorder=3)
            ax.fill_between(x_vals, -y_vals, 0, alpha=0.1, color=ACCENT, zorder=2)

        elif method == 'washer':
            inner_str = params.get('inner_function', '0.5*x')
            inner_y = _eval(inner_str, x_vals)
            ax.plot(x_vals, inner_y, color=SUCCESS, linewidth=2, label='g(x)', zorder=4)
            ax.fill_between(x_vals, inner_y, y_vals, alpha=0.2, color=ACCENT, zorder=2)

            # Show washer cross-sections
            n_washers = 4
            washer_x = np.linspace(x_range[0] + 0.3, x_range[1] - 0.3, n_washers)
            for wx in washer_x:
                outer = float(_eval(func_str, np.array([wx]))[0])
                inner = float(_eval(inner_str, np.array([wx]))[0])
                ax.plot([wx, wx], [inner, outer], color=SECONDARY, linewidth=3, alpha=0.5, zorder=3)

            ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

        elif method == 'shell':
            # Show representative shells (as horizontal rectangles)
            n_shells = 5
            y_max = float(np.nanmax(y_vals))
            shell_y_vals = np.linspace(0.3, y_max - 0.1, n_shells)
            for sy in shell_y_vals:
                # Find x where f(x) = sy (inverse)
                diffs = np.abs(y_vals - sy)
                sx = x_vals[np.argmin(diffs)]
                rect = plt.Rectangle((0, sy - 0.08), sx, 0.16,
                                   facecolor=ACCENT, edgecolor=PRIMARY,
                                   alpha=0.4, linewidth=1, zorder=3)
                ax.add_patch(rect)

    elif axis == 'y':
        # Revolution about y-axis
        ax.fill_betweenx(y_vals, 0, x_vals, alpha=0.2, color=ACCENT, zorder=2)
        ax.plot(-x_vals, y_vals, color=PRIMARY, linewidth=1.5, alpha=0.4,
               linestyle='--', zorder=3)

    ax.axhline(y=0, color='black', linewidth=0.8, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.8, zorder=1)
    ax.set_xlabel('x', fontsize=LABEL_SIZE)
    ax.set_ylabel('y', fontsize=LABEL_SIZE)

    add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path
