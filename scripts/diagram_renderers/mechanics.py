"""Renderer for AP Physics 1 mechanics diagram types."""
import numpy as np
from pathlib import Path
from .style import *
from .physics_primitives import (
    draw_arrow, draw_force_arrow, draw_object, draw_ground, draw_spring,
    draw_pivot, draw_angle_arc, draw_wall,
)


def _render_fbd(params):
    """Free-body diagram: force arrows on an object.

    params:
        object_shape : 'block' | 'circle' | 'dot'  (default 'block')
        object_label : str  (default 'm')
        object_size  : float (default 0.4)
        incline_angle: float degrees (default 0 = flat ground)
        show_ground  : bool (default True)
        forces       : list of {name, type, angle_deg, length, label, label_offset}
        show_axes    : bool – draw tilted x/y axes for incline problems
        title        : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    incline = params.get('incline_angle', 0)
    obj_shape = params.get('object_shape', 'block')
    obj_size = params.get('object_size', 0.4)
    obj_label = params.get('object_label', 'm')
    origin = (0, 0)

    # Draw ground / incline surface
    if params.get('show_ground', True):
        if incline == 0:
            draw_ground(ax, (-1.5, 1.5), y=-obj_size / 2)
        else:
            rad = np.radians(incline)
            # Inclined surface
            length = 3.0
            x0 = -length / 2 * np.cos(rad)
            y0 = -length / 2 * np.sin(rad) - obj_size / 2
            x1 = length / 2 * np.cos(rad)
            y1 = length / 2 * np.sin(rad) - obj_size / 2
            ax.plot([x0, x1], [y0, y1], color=TEXT_COLOR, lw=2, zorder=2)
            # Ground line
            ax.plot([x0, x0], [y0, y0 - 0.3], color=TEXT_COLOR, lw=1.5, zorder=2)
            draw_ground(ax, (x0 - 0.5, x0 + 0.1), y=y0 - 0.3)
            # Angle arc
            draw_angle_arc(ax, (x0, y0), 0.5, 0, incline, label=f'{incline}°')

    # Draw the object
    draw_object(ax, origin, shape=obj_shape, size=obj_size, label=obj_label)

    # Draw force arrows
    forces = params.get('forces', [])
    for f in forces:
        angle = f.get('angle_deg', 90)
        length = f.get('length', 0.8)
        label = f.get('label', f.get('name', ''))
        ftype = f.get('type', 'applied')
        offset = tuple(f.get('label_offset', [0, 0]))
        draw_force_arrow(ax, origin, angle, length, label=label,
                         force_type=ftype, label_offset=offset)

    # Optional coordinate axes
    if params.get('show_axes'):
        axis_len = 0.6
        rad = np.radians(incline)
        # x-axis along incline
        ax.annotate('', xy=(axis_len * np.cos(rad), axis_len * np.sin(rad)),
                    xytext=origin,
                    arrowprops=dict(arrowstyle='->', color='#94A3B8', lw=1.2))
        ax.text(axis_len * np.cos(rad) + 0.1, axis_len * np.sin(rad), '+x',
                fontsize=ANNOTATION_SIZE - 1, color='#94A3B8')
        # y-axis perpendicular to incline
        ax.annotate('', xy=(-axis_len * np.sin(rad), axis_len * np.cos(rad)),
                    xytext=origin,
                    arrowprops=dict(arrowstyle='->', color='#94A3B8', lw=1.2))
        ax.text(-axis_len * np.sin(rad), axis_len * np.cos(rad) + 0.1, '+y',
                fontsize=ANNOTATION_SIZE - 1, color='#94A3B8')

    # Auto-scale
    ax.set_xlim(-2, 2)
    ax.set_ylim(-1.5, 1.8)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_motion_graph(params):
    """Position-time, velocity-time, or acceleration-time graph.

    params:
        graph_type : 'x-t' | 'v-t' | 'a-t'
        segments   : list of {t_start, t_end, expr, label}
                     expr is a Python expression in terms of 't'
                     OR {t_start, t_end, y_start, y_end} for linear segments
        x_label, y_label : str
        title      : str
        annotations: list of {t, text, va} for labelling key points
    """
    fig, ax = create_figure()
    graph_type = params.get('graph_type', 'x-t')

    y_labels = {'x-t': 'Position (m)', 'v-t': 'Velocity (m/s)', 'a-t': 'Acceleration (m/s²)'}
    ax.set_xlabel(params.get('x_label', 'Time (s)'), fontsize=LABEL_SIZE)
    ax.set_ylabel(params.get('y_label', y_labels.get(graph_type, 'y')), fontsize=LABEL_SIZE)

    segments = params.get('segments', [])
    for i, seg in enumerate(segments):
        t0 = seg['t_start']
        t1 = seg['t_end']
        t = np.linspace(t0, t1, 200)
        color = COLORS[i % len(COLORS)]

        if 'expr' in seg:
            # Evaluate expression safely
            y = eval(seg['expr'], {'t': t, 'np': np, 'sin': np.sin,
                                    'cos': np.cos, 'sqrt': np.sqrt,
                                    'abs': np.abs, 'pi': np.pi})
            ax.plot(t, y, color=color, linewidth=2.5, zorder=3)
        else:
            # Linear segment from y_start to y_end
            y0 = seg.get('y_start', 0)
            y1 = seg.get('y_end', 0)
            ax.plot([t0, t1], [y0, y1], color=color, linewidth=2.5, zorder=3)

        if seg.get('label'):
            t_mid = (t0 + t1) / 2
            if 'expr' in seg:
                y_mid = eval(seg['expr'], {'t': np.array([t_mid]), 'np': np,
                                            'sin': np.sin, 'cos': np.cos,
                                            'sqrt': np.sqrt, 'abs': np.abs,
                                            'pi': np.pi})[0]
            else:
                y_mid = (seg.get('y_start', 0) + seg.get('y_end', 0)) / 2
            ax.annotate(seg['label'], xy=(t_mid, y_mid), fontsize=ANNOTATION_SIZE - 1,
                        ha='center', va='bottom', xytext=(0, 8),
                        textcoords='offset points', color=color)

    # Annotations
    for ann in params.get('annotations', []):
        ax.annotate(ann['text'], xy=(ann['t'], ann.get('y', 0)),
                    fontsize=ANNOTATION_SIZE, ha='center',
                    va=ann.get('va', 'bottom'), xytext=(0, 10),
                    textcoords='offset points', color=TEXT_COLOR,
                    arrowprops=dict(arrowstyle='->', color='#94A3B8', lw=0.8))

    ax.axhline(y=0, color='#94A3B8', linewidth=0.8, zorder=1)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_vector(params):
    """Vector decomposition or addition diagram.

    params:
        style   : 'components' | 'addition'
        vectors : list of {magnitude, angle_deg, label, color}
        show_components : bool (for 'components' style)
        origin  : [x, y] (default [0, 0])
        title   : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')

    style = params.get('style', 'components')
    vecs = params.get('vectors', [])
    ox, oy = params.get('origin', [0, 0])

    if style == 'components':
        # Show one vector and its x/y components
        v = vecs[0] if vecs else {'magnitude': 1, 'angle_deg': 45, 'label': 'v'}
        mag = v['magnitude']
        ang = np.radians(v['angle_deg'])
        color = v.get('color', PRIMARY)

        end = (ox + mag * np.cos(ang), oy + mag * np.sin(ang))

        # Components (dashed)
        vx = mag * np.cos(ang)
        vy = mag * np.sin(ang)
        ax.plot([ox, ox + vx], [oy, oy], '--', color=SECONDARY, lw=1.5, zorder=2)
        ax.plot([ox + vx, ox + vx], [oy, oy + vy], '--', color=SUCCESS, lw=1.5, zorder=2)

        # Component arrows
        draw_arrow(ax, (ox, oy), (ox + vx, oy),
                   label=f'$v_x = {vx:.1f}$', color=SECONDARY,
                   label_offset=(0, -0.15 * mag))
        draw_arrow(ax, (ox, oy), (ox, oy + vy),
                   label=f'$v_y = {vy:.1f}$', color=SUCCESS,
                   label_offset=(-0.2 * mag, 0))

        # Main vector
        draw_arrow(ax, (ox, oy), end, label=v.get('label', ''), color=color)

        # Angle arc
        draw_angle_arc(ax, (ox, oy), mag * 0.25, 0, v['angle_deg'],
                       label=f'{v["angle_deg"]}°')

    elif style == 'addition':
        # Head-to-tail vector addition
        tip_x, tip_y = ox, oy
        starts = []
        ends = []
        for i, v in enumerate(vecs):
            mag = v['magnitude']
            ang = np.radians(v['angle_deg'])
            start = (tip_x, tip_y)
            tip_x += mag * np.cos(ang)
            tip_y += mag * np.sin(ang)
            end = (tip_x, tip_y)
            starts.append(start)
            ends.append(end)
            color = v.get('color', COLORS[i % len(COLORS)])
            draw_arrow(ax, start, end, label=v.get('label', ''), color=color)

        # Resultant (dashed)
        if len(vecs) > 1:
            draw_arrow(ax, (ox, oy), (tip_x, tip_y),
                       label=params.get('resultant_label', 'R'),
                       color=TEXT_COLOR, lw=2)
            # Draw resultant dashed underneath
            ax.plot([ox, tip_x], [oy, tip_y], '--', color=TEXT_COLOR,
                    lw=1, alpha=0.4, zorder=1)

    # Auto-scale with padding
    ax.autoscale()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    pad = max(xlim[1] - xlim[0], ylim[1] - ylim[0]) * 0.2
    ax.set_xlim(xlim[0] - pad, xlim[1] + pad)
    ax.set_ylim(ylim[0] - pad, ylim[1] + pad)
    ax.axhline(y=0, color='#94A3B8', linewidth=0.5, zorder=0)
    ax.axvline(x=0, color='#94A3B8', linewidth=0.5, zorder=0)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_energy_bars(params):
    """Energy bar chart showing KE, PE, Work at different states.

    params:
        states : list of {label, KE, PE, W (optional), Eth (optional)}
        title  : str
    """
    fig, ax = create_figure()
    states = params.get('states', [])
    if not states:
        return fig, ax

    n = len(states)
    labels = [s['label'] for s in states]
    bar_w = 0.18
    energy_types = ['KE', 'PE', 'W', 'Eth']
    energy_colors = {'KE': SECONDARY, 'PE': SUCCESS, 'W': ACCENT, 'Eth': '#94A3B8'}
    energy_labels = {'KE': 'KE', 'PE': 'PE', 'W': 'Work', 'Eth': 'Thermal'}

    x_positions = np.arange(n)

    for j, etype in enumerate(energy_types):
        vals = [s.get(etype, 0) for s in states]
        if any(v != 0 for v in vals):
            offset = (j - 1.5) * bar_w
            bars = ax.bar(x_positions + offset, vals, bar_w * 0.9,
                          color=energy_colors[etype], alpha=0.85,
                          label=energy_labels[etype], edgecolor='white',
                          linewidth=0.8, zorder=3)
            for bar, val in zip(bars, vals):
                if val != 0:
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.02 * max(max(s.get(etype, 0) for s in states) for etype in energy_types if any(s.get(etype, 0) for s in states)),
                            f'{val}', ha='center', va='bottom',
                            fontsize=ANNOTATION_SIZE - 1, color=TEXT_COLOR)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, fontsize=LABEL_SIZE)
    ax.set_ylabel('Energy (J)', fontsize=LABEL_SIZE)
    ax.axhline(y=0, color=TEXT_COLOR, linewidth=0.8, zorder=1)
    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_collision(params):
    """Before/after collision diagram with momentum arrows.

    params:
        before : list of {label, mass, velocity, color}
        after  : list of {label, mass, velocity, color}
        collision_type : 'elastic' | 'inelastic' | 'perfectly_inelastic'
        title  : str
    """
    fig, ax = create_figure(figsize=(7, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    before = params.get('before', [])
    after = params.get('after', [])

    # Draw "Before" section (top half)
    ax.text(0, 2.2, 'Before', fontsize=LABEL_SIZE + 1, ha='center',
            fontweight='bold', color=TEXT_COLOR)
    _draw_collision_row(ax, before, y=1.5)

    # Divider
    ax.axhline(y=0.5, color='#94A3B8', linewidth=1, linestyle='--', zorder=1,
               xmin=0.1, xmax=0.9)

    # Draw "After" section (bottom half)
    ax.text(0, -0.3, 'After', fontsize=LABEL_SIZE + 1, ha='center',
            fontweight='bold', color=TEXT_COLOR)
    _draw_collision_row(ax, after, y=-1.0)

    ctype = params.get('collision_type', '')
    if ctype:
        nice = ctype.replace('_', ' ').title()
        ax.text(0, 2.8, nice, fontsize=ANNOTATION_SIZE, ha='center',
                color='#94A3B8', style='italic')

    ax.set_xlim(-4, 4)
    ax.set_ylim(-2.2, 3.2)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _draw_collision_row(ax, objects, y):
    """Helper: draw objects with velocity arrows in a collision row."""
    n = len(objects)
    spacing = 3.0
    x_start = -spacing * (n - 1) / 2
    for i, obj in enumerate(objects):
        x = x_start + i * spacing
        color = obj.get('color', COLORS[i % len(COLORS)])
        draw_object(ax, (x, y), shape='circle', size=0.35,
                    label=obj.get('label', ''), color=color + '33',
                    edgecolor=color)
        # Mass label below
        ax.text(x, y - 0.35, f'{obj["mass"]} kg', fontsize=ANNOTATION_SIZE - 1,
                ha='center', va='top', color=TEXT_COLOR)
        # Velocity arrow
        vel = obj.get('velocity', 0)
        if vel != 0:
            arrow_len = min(abs(vel) * 0.15, 1.5)
            direction = 1 if vel > 0 else -1
            draw_arrow(ax, (x, y), (x + direction * arrow_len, y),
                       label=f'v = {vel} m/s', color=color,
                       label_offset=(0, 0.25))


def _render_circular(params):
    """Circular motion diagram with centripetal force and velocity vectors.

    params:
        radius     : float (default 1.0)
        positions  : list of {angle_deg, show_v, show_ac, show_F, label}
        show_path  : bool (default True)
        title      : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    r = params.get('radius', 1.0)
    positions = params.get('positions', [{'angle_deg': 0}])

    # Draw circular path
    if params.get('show_path', True):
        theta = np.linspace(0, 2 * np.pi, 200)
        ax.plot(r * np.cos(theta), r * np.sin(theta), color='#94A3B8',
                lw=1.5, linestyle='--', zorder=1)

    # Draw center
    ax.plot(0, 0, '+', color='#94A3B8', markersize=8, mew=1.5, zorder=2)

    arrow_len = r * 0.5

    for pos in positions:
        ang = np.radians(pos['angle_deg'])
        px = r * np.cos(ang)
        py = r * np.sin(ang)

        # Object on the path
        ax.plot(px, py, 'o', markersize=10, color=PRIMARY,
                markeredgecolor='white', mew=1.5, zorder=5)

        if pos.get('label'):
            ax.text(px + 0.15, py + 0.15, pos['label'],
                    fontsize=ANNOTATION_SIZE, color=TEXT_COLOR, zorder=6)

        # Velocity (tangent: perpendicular to radius, CCW)
        if pos.get('show_v', True):
            vx = -arrow_len * np.sin(ang)
            vy = arrow_len * np.cos(ang)
            draw_arrow(ax, (px, py), (px + vx, py + vy),
                       label='v', color=SUCCESS,
                       label_offset=(vx * 0.3, vy * 0.3))

        # Centripetal acceleration / force (toward center)
        if pos.get('show_ac') or pos.get('show_F'):
            ax_len = arrow_len * 0.8
            cx = -ax_len * np.cos(ang)
            cy = -ax_len * np.sin(ang)
            label = '$a_c$' if pos.get('show_ac') else '$F_c$'
            draw_arrow(ax, (px, py), (px + cx, py + cy),
                       label=label, color=SECONDARY,
                       label_offset=(cx * 0.3, cy * 0.3))

    lim = r * 2.0
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_shm(params):
    """Simple harmonic motion diagrams.

    params:
        style     : 'wave' | 'spring_mass' | 'snapshots'
        amplitude : float (default 1.0)
        period    : float (default 2.0)
        n_cycles  : float (default 2)
        phase     : float radians (default 0)
        snapshots : list of {x, label}  (for 'snapshots' style)
        show_equilibrium : bool (default True)
        title     : str
    """
    style = params.get('style', 'wave')

    if style == 'wave':
        return _render_shm_wave(params)
    elif style == 'spring_mass':
        return _render_spring_mass(params)
    elif style == 'snapshots':
        return _render_shm_snapshots(params)
    return _render_shm_wave(params)


def _render_shm_wave(params):
    """x(t) sinusoidal wave."""
    fig, ax = create_figure()
    A = params.get('amplitude', 1.0)
    T = params.get('period', 2.0)
    n_cyc = params.get('n_cycles', 2)
    phase = params.get('phase', 0)

    t = np.linspace(0, T * n_cyc, 500)
    x = A * np.sin(2 * np.pi * t / T + phase)

    ax.plot(t, x, color=PRIMARY, linewidth=2.5, zorder=3)

    if params.get('show_equilibrium', True):
        ax.axhline(y=0, color='#94A3B8', linewidth=1, linestyle='--', zorder=1)
        ax.text(t[-1] * 1.02, 0, 'equilibrium', fontsize=ANNOTATION_SIZE - 2,
                va='center', color='#94A3B8')

    # Amplitude markers
    ax.axhline(y=A, color=SECONDARY, linewidth=0.8, linestyle=':', zorder=1)
    ax.axhline(y=-A, color=SECONDARY, linewidth=0.8, linestyle=':', zorder=1)
    ax.text(-T * 0.05, A, f'A = {A}', fontsize=ANNOTATION_SIZE - 1,
            va='bottom', ha='right', color=SECONDARY)
    ax.text(-T * 0.05, -A, f'−A', fontsize=ANNOTATION_SIZE - 1,
            va='top', ha='right', color=SECONDARY)

    ax.set_xlabel('Time (s)', fontsize=LABEL_SIZE)
    ax.set_ylabel('Displacement', fontsize=LABEL_SIZE)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_spring_mass(params):
    """Horizontal spring-mass system."""
    fig, ax = create_figure(figsize=(7, 3))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    x_eq = params.get('equilibrium_x', 2.0)
    displacement = params.get('displacement', 0.5)
    mass_x = x_eq + displacement

    # Wall
    draw_wall(ax, 0, (-0.5, 0.8), side='left')

    # Spring
    draw_spring(ax, (0, 0.15), (mass_x - 0.2, 0.15), coils=8)

    # Mass block
    draw_object(ax, (mass_x, 0.15), shape='block', size=0.35, label='m')

    # Ground
    draw_ground(ax, (-0.3, mass_x + 0.8), y=-0.05)

    # Equilibrium marker
    ax.plot([x_eq, x_eq], [-0.2, 0.6], '--', color='#94A3B8', lw=1, zorder=1)
    ax.text(x_eq, -0.3, 'x = 0', fontsize=ANNOTATION_SIZE - 1,
            ha='center', color='#94A3B8')

    # Displacement annotation
    if displacement != 0:
        direction = 'stretched' if displacement > 0 else 'compressed'
        ax.annotate('', xy=(mass_x, -0.15), xytext=(x_eq, -0.15),
                    arrowprops=dict(arrowstyle='<->', color=ACCENT, lw=1.5))
        ax.text((x_eq + mass_x) / 2, -0.28, f'x = {displacement}',
                fontsize=ANNOTATION_SIZE - 1, ha='center', color=ACCENT)

    ax.set_xlim(-0.8, mass_x + 1.2)
    ax.set_ylim(-0.6, 1.0)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_shm_snapshots(params):
    """Multiple snapshots of SHM at different positions."""
    fig, ax = create_figure(figsize=(7, 3))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    snapshots = params.get('snapshots', [
        {'x': -1, 'label': '−A'}, {'x': 0, 'label': '0'}, {'x': 1, 'label': '+A'}
    ])

    # Number line
    x_vals = [s['x'] for s in snapshots]
    xmin, xmax = min(x_vals) - 0.5, max(x_vals) + 0.5
    ax.plot([xmin, xmax], [0, 0], color=TEXT_COLOR, lw=1.5, zorder=1)

    for s in snapshots:
        ax.plot(s['x'], 0, 'o', markersize=12, color=PRIMARY,
                markeredgecolor='white', mew=1.5, zorder=3)
        ax.text(s['x'], -0.15, s.get('label', ''), fontsize=ANNOTATION_SIZE,
                ha='center', va='top', color=TEXT_COLOR)

    ax.set_xlim(xmin - 0.3, xmax + 0.3)
    ax.set_ylim(-0.5, 0.5)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_torque(params):
    """Torque diagram: force at a lever arm with pivot.

    params:
        beam_length : float (default 2.0)
        pivot_pos   : float fraction along beam (default 0.5 = centre)
        forces      : list of {pos (fraction), angle_deg, length, label, type}
        show_pivot  : bool (default True)
        title       : str
    """
    fig, ax = create_figure(figsize=(7, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    L = params.get('beam_length', 2.0)
    pivot_frac = params.get('pivot_pos', 0.5)
    pivot_x = -L / 2 + pivot_frac * L
    beam_y = 0.15

    # Beam
    ax.plot([-L / 2, L / 2], [beam_y, beam_y], color=TEXT_COLOR, lw=4,
            solid_capstyle='round', zorder=3)

    # Pivot
    if params.get('show_pivot', True):
        draw_pivot(ax, (pivot_x, beam_y - 0.01), size=0.12)
        draw_ground(ax, (pivot_x - 0.4, pivot_x + 0.4), y=beam_y - 0.13)

    # Forces
    forces = params.get('forces', [])
    for f in forces:
        frac = f.get('pos', 0.5)
        fx = -L / 2 + frac * L
        angle = f.get('angle_deg', 90)
        length = f.get('length', 0.6)
        label = f.get('label', '')
        ftype = f.get('type', 'applied')
        draw_force_arrow(ax, (fx, beam_y), angle, length, label=label,
                         force_type=ftype,
                         label_offset=tuple(f.get('label_offset', [0, 0])))

        # Lever arm dimension
        if f.get('show_lever_arm') and pivot_frac != frac:
            draw_arrow(ax, (pivot_x, beam_y - 0.35), (fx, beam_y - 0.35),
                       label=f.get('r_label', 'r'), color='#94A3B8')

    ax.set_xlim(-L / 2 - 0.5, L / 2 + 0.5)
    ax.set_ylim(-0.6, 1.5)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_fluid(params):
    """Fluid / pressure diagrams.

    params:
        style : 'pressure_depth' | 'buoyancy' | 'u_tube'
        (each has sub-params)
    """
    style = params.get('style', 'buoyancy')

    if style == 'buoyancy':
        return _render_buoyancy(params)
    elif style == 'pressure_depth':
        return _render_pressure_depth(params)
    elif style == 'u_tube':
        return _render_u_tube(params)
    return _render_buoyancy(params)


def _render_buoyancy(params):
    """Object submerged/floating with weight and buoyant force arrows."""
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    # Water
    ax.fill_between([-2, 2], -2, 0.5, color='#DBEAFE', alpha=0.5, zorder=1)
    ax.plot([-2, 2], [0.5, 0.5], color='#3B82F6', lw=1.5, zorder=2)
    ax.text(1.7, 0.6, 'water', fontsize=ANNOTATION_SIZE - 1, color='#3B82F6')

    # Object
    obj_y = params.get('object_y', -0.3)
    obj_size = params.get('object_size', 0.5)
    draw_object(ax, (0, obj_y), shape=params.get('object_shape', 'block'),
                size=obj_size, label=params.get('object_label', 'm'),
                color='#FEF3C7', edgecolor=ACCENT)

    # Forces
    fg_len = params.get('fg_length', 0.7)
    fb_len = params.get('fb_length', 0.7)
    draw_force_arrow(ax, (0, obj_y), 270, fg_len, label='$F_g$',
                     force_type='gravity', label_offset=(-0.25, 0))
    draw_force_arrow(ax, (0, obj_y), 90, fb_len, label='$F_b$',
                     force_type='spring', label_offset=(0.25, 0))

    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 1.5)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_pressure_depth(params):
    """Pressure increases with depth in a fluid column."""
    fig, ax = create_figure(figsize=(4, 5))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    depth = params.get('depth', 3.0)

    # Container
    ax.plot([-0.8, -0.8], [0, -depth], color=TEXT_COLOR, lw=2)
    ax.plot([0.8, 0.8], [0, -depth], color=TEXT_COLOR, lw=2)
    ax.plot([-0.8, 0.8], [-depth, -depth], color=TEXT_COLOR, lw=2)

    # Water fill with gradient
    for i in range(20):
        y_top = -depth * i / 20
        y_bot = -depth * (i + 1) / 20
        alpha = 0.15 + 0.4 * (i / 20)
        ax.fill_between([-0.78, 0.78], y_bot, y_top, color='#3B82F6',
                        alpha=alpha, zorder=1)

    # Surface
    ax.plot([-0.8, 0.8], [0, 0], color='#3B82F6', lw=1.5)

    # Pressure arrows (increasing size with depth)
    depths_shown = params.get('depths_shown', [0.5, 1.5, 2.5])
    for d in depths_shown:
        arrow_len = 0.15 + 0.2 * d / depth
        ax.annotate('', xy=(-0.78, -d), xytext=(-0.78 - arrow_len, -d),
                    arrowprops=dict(arrowstyle='->', color=SECONDARY, lw=1.5))
        ax.annotate('', xy=(0.78, -d), xytext=(0.78 + arrow_len, -d),
                    arrowprops=dict(arrowstyle='->', color=SECONDARY, lw=1.5))
        ax.text(1.1, -d, f'h = {d}', fontsize=ANNOTATION_SIZE - 1, color=TEXT_COLOR)

    # Labels
    ax.text(0, 0.15, '$P_0$', fontsize=ANNOTATION_SIZE, ha='center', color='#94A3B8')
    ax.text(0, -depth - 0.25, '$P = P_0 + \\rho g h$', fontsize=ANNOTATION_SIZE,
            ha='center', color=TEXT_COLOR)

    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-depth - 0.6, 0.8)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_u_tube(params):
    """U-tube manometer."""
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    h_diff = params.get('h_diff', 0.5)
    left_label = params.get('left_label', 'Fluid A')
    right_label = params.get('right_label', 'Fluid B')

    # U-tube shape
    tube_w = 0.3
    left_x, right_x = -1.0, 1.0
    bottom = -1.5

    # Left arm
    ax.plot([left_x - tube_w, left_x - tube_w], [1.5, bottom], color=TEXT_COLOR, lw=2)
    ax.plot([left_x + tube_w, left_x + tube_w], [1.5, bottom], color=TEXT_COLOR, lw=2)
    # Right arm
    ax.plot([right_x - tube_w, right_x - tube_w], [1.5, bottom], color=TEXT_COLOR, lw=2)
    ax.plot([right_x + tube_w, right_x + tube_w], [1.5, bottom], color=TEXT_COLOR, lw=2)
    # Bottom connection
    ax.plot([left_x + tube_w, right_x - tube_w], [bottom, bottom], color=TEXT_COLOR, lw=2)
    ax.plot([left_x - tube_w, right_x + tube_w], [bottom - 0.1, bottom - 0.1],
            color=TEXT_COLOR, lw=2)

    # Fluid levels
    left_h = 0 + h_diff / 2
    right_h = 0 - h_diff / 2
    ax.fill_between([left_x - tube_w, left_x + tube_w], bottom, left_h,
                    color='#3B82F6', alpha=0.3)
    ax.fill_between([right_x - tube_w, right_x + tube_w], bottom, right_h,
                    color='#F59E0B', alpha=0.3)
    # Bottom fill
    ax.fill_between([left_x + tube_w, right_x - tube_w], bottom - 0.1, bottom,
                    color='#3B82F6', alpha=0.3)

    # Height difference
    ax.annotate('', xy=(right_x + tube_w + 0.3, left_h),
                xytext=(right_x + tube_w + 0.3, right_h),
                arrowprops=dict(arrowstyle='<->', color=SECONDARY, lw=1.5))
    ax.text(right_x + tube_w + 0.5, (left_h + right_h) / 2, f'Δh = {h_diff}',
            fontsize=ANNOTATION_SIZE, va='center', color=SECONDARY)

    ax.text(left_x, 1.6, left_label, fontsize=ANNOTATION_SIZE, ha='center', color='#3B82F6')
    ax.text(right_x, 1.6, right_label, fontsize=ANNOTATION_SIZE, ha='center', color='#F59E0B')

    ax.set_xlim(-2, 2.5)
    ax.set_ylim(-2, 2)
    add_title(ax, params.get('title', ''))
    return fig, ax


# Dispatch table
_DISPATCH = {
    'free_body_diagram': _render_fbd,
    'motion_graph': _render_motion_graph,
    'vector_diagram': _render_vector,
    'energy_bar_chart': _render_energy_bars,
    'collision_diagram': _render_collision,
    'circular_motion': _render_circular,
    'shm_diagram': _render_shm,
    'torque_diagram': _render_torque,
    'fluid_diagram': _render_fluid,
}


def render(entry, output_dir):
    """Render a mechanics diagram from manifest entry."""
    params = entry['params']
    diagram_type = params.get('type', 'free_body_diagram')

    renderer = _DISPATCH.get(diagram_type)
    if not renderer:
        raise ValueError(f"Unknown mechanics diagram type: {diagram_type}")

    fig, ax = renderer(params)

    filename = entry['bucket_key'].split('/')[-1]
    path = Path(output_dir) / filename
    save_figure(fig, path)
    return path
