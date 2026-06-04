"""Renderer for slope field diagrams."""
import numpy as np
from sympy import Symbol, lambdify
from sympy.parsing.sympy_parser import parse_expr
from scipy.integrate import odeint
from .style import *

x_sym = Symbol('x')
y_sym = Symbol('y')


def render(entry, output_dir):
    """Render a slope field diagram."""
    params = entry['params']
    fig, ax = create_figure()

    x_range = params.get('x_range', [-3, 3])
    y_range = params.get('y_range', [-3, 3])

    # Create grid for slope field
    x_grid = np.linspace(x_range[0], x_range[1], 20)
    y_grid = np.linspace(y_range[0], y_range[1], 20)
    X, Y = np.meshgrid(x_grid, y_grid)

    # Parse dy/dx expression
    dy_dx_str = params['dy_dx']
    expr = parse_expr(dy_dx_str, local_dict={'x': x_sym, 'y': y_sym})
    f = lambdify((x_sym, y_sym), expr, modules=['numpy'])

    # Compute slopes
    DY = np.array(f(X, Y), dtype=float)
    DX = np.ones_like(DY)

    # Normalize for uniform segment length
    magnitude = np.sqrt(DX**2 + DY**2)
    magnitude[magnitude == 0] = 1
    DX = DX / magnitude
    DY = DY / magnitude

    # Handle inf/nan
    DX[~np.isfinite(DY)] = 0
    DY[~np.isfinite(DY)] = 0

    ax.quiver(X, Y, DX, DY, angles='xy', scale=30, width=0.003,
              color='#64748B', alpha=0.6, zorder=2)

    # Draw solution curves if specified
    for curve in params.get('solution_curves', []):
        x0, y0 = curve['x0'], curve['y0']

        # Forward integration
        t_forward = np.linspace(x0, x_range[1], 200)
        if len(t_forward) > 1:
            def ode_func(y_val, x_val):
                try:
                    result = float(f(x_val, y_val))
                    if not np.isfinite(result):
                        return 0
                    return np.clip(result, -100, 100)
                except:
                    return 0
            y_forward = odeint(ode_func, y0, t_forward).flatten()
            mask = (y_forward >= y_range[0]) & (y_forward <= y_range[1])
            ax.plot(t_forward[mask], y_forward[mask], color=SECONDARY,
                   linewidth=2, zorder=4)

        # Backward integration
        t_backward = np.linspace(x0, x_range[0], 200)
        if len(t_backward) > 1:
            y_backward = odeint(ode_func, y0, t_backward).flatten()
            mask = (y_backward >= y_range[0]) & (y_backward <= y_range[1])
            ax.plot(t_backward[mask], y_backward[mask], color=SECONDARY,
                   linewidth=2, zorder=4)

        # Mark initial point
        ax.plot(x0, y0, 'o', markersize=6, color=SECONDARY, zorder=5)

    ax.set_xlim(x_range)
    ax.set_ylim(y_range)
    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)
    ax.set_xlabel('x', fontsize=LABEL_SIZE)
    ax.set_ylabel('y', fontsize=LABEL_SIZE)

    add_title(ax, params.get('title', ''))

    filename = entry['bucket_key'].split('/')[-1]
    path = output_dir / filename
    save_figure(fig, path)
    return path
