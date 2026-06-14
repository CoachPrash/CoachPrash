"""Renderer for AP Physics 2 electromagnetism diagram types.

Handles: field lines, equipotentials, capacitors, circuits (SchemDraw),
Kirchhoff's, magnetic fields, and force on moving charges.
"""
import numpy as np
from pathlib import Path
from .style import *
from .physics_primitives import (
    draw_charge, draw_into_page, draw_out_of_page,
    draw_plate, draw_field_lines, draw_arrow, draw_bar_magnet,
    draw_angle_arc,
)


# ── Field Line Diagrams ──────────────────────────────────────────────

def _render_field_line_diagram(params):
    """Electric field lines from point charges.

    params:
        charges : list of {x, y, q, label}  (q > 0 positive, q < 0 negative)
        x_range : [xmin, xmax]  (default [-3, 3])
        y_range : [ymin, ymax]  (default [-3, 3])
        density : int  (streamplot density, default 20)
        title   : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    charges_data = params.get('charges', [])
    x_range = tuple(params.get('x_range', [-3, 3]))
    y_range = tuple(params.get('y_range', [-3, 3]))
    density = params.get('density', 20)

    charge_tuples = [(c['x'], c['y'], c['q']) for c in charges_data]
    draw_field_lines(ax, charge_tuples, x_range, y_range, density=density)

    for c in charges_data:
        sign = '+' if c['q'] > 0 else '-'
        draw_charge(ax, (c['x'], c['y']), sign, label=c.get('label', ''))

    ax.set_xlim(*x_range)
    ax.set_ylim(*y_range)
    add_title(ax, params.get('title', ''))
    return fig, ax


# ── Equipotential Diagrams ──────────────────────────────────────────

def _render_equipotential_diagram(params):
    """Equipotential contours overlaid on field lines.

    params:
        charges   : list of {x, y, q, label}
        n_levels  : int  (number of equipotential contours, default 12)
        x_range, y_range : [min, max]
        title     : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    charges_data = params.get('charges', [])
    x_range = tuple(params.get('x_range', [-3, 3]))
    y_range = tuple(params.get('y_range', [-3, 3]))
    n_levels = params.get('n_levels', 12)

    # Compute potential field
    nx, ny = 300, 300
    xs = np.linspace(x_range[0], x_range[1], nx)
    ys = np.linspace(y_range[0], y_range[1], ny)
    X, Y = np.meshgrid(xs, ys)
    V = np.zeros_like(X)

    charge_tuples = []
    for c in charges_data:
        dx = X - c['x']
        dy = Y - c['y']
        r = np.sqrt(dx ** 2 + dy ** 2)
        r = np.maximum(r, 0.15)
        V += c['q'] / r
        charge_tuples.append((c['x'], c['y'], c['q']))

    # Clip extreme values for better visualization
    vmax = np.percentile(np.abs(V), 95)
    V = np.clip(V, -vmax, vmax)

    # Draw equipotentials (dashed contours)
    levels = np.linspace(-vmax, vmax, n_levels)
    ax.contour(X, Y, V, levels=levels, colors='#94A3B8', linewidths=0.8,
               linestyles='--', zorder=1)

    # Draw field lines on top
    draw_field_lines(ax, charge_tuples, x_range, y_range, density=15)

    # Draw charges
    for c in charges_data:
        sign = '+' if c['q'] > 0 else '-'
        draw_charge(ax, (c['x'], c['y']), sign, label=c.get('label', ''))

    ax.set_xlim(*x_range)
    ax.set_ylim(*y_range)
    add_title(ax, params.get('title', ''))
    return fig, ax


# ── Capacitor Diagrams ──────────────────────────────────────────────

def _render_capacitor_diagram(params):
    """Parallel plate capacitor with field, charges, optional dielectric.

    params:
        plate_separation : float (default 1.0)
        plate_length     : float (default 2.0)
        show_field       : bool (default True)
        show_charges     : bool (default True)
        dielectric       : bool (default False)
        dielectric_label : str (default 'κ')
        labels           : {left, right, top, bottom}
        title            : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    sep = params.get('plate_separation', 1.0)
    plen = params.get('plate_length', 2.0)

    # Draw plates
    draw_plate(ax, (-sep / 2, 0), plen, 'vertical',
               charge_sign='+' if params.get('show_charges', True) else None)
    draw_plate(ax, (sep / 2, 0), plen, 'vertical',
               charge_sign='-' if params.get('show_charges', True) else None)

    # Uniform field arrows between plates
    if params.get('show_field', True):
        n_arrows = 5
        for i in range(n_arrows):
            y = -plen / 2 + (i + 0.5) * plen / n_arrows
            ax.annotate('', xy=(sep / 2 - 0.15, y),
                        xytext=(-sep / 2 + 0.15, y),
                        arrowprops=dict(arrowstyle='->', color=ACCENT,
                                        lw=1.2),
                        zorder=3)

    # Dielectric
    if params.get('dielectric', False):
        rect = plt.Rectangle((-sep / 2 + 0.05, -plen / 2 + 0.05),
                              sep - 0.1, plen - 0.1,
                              facecolor='#FEF3C7', edgecolor=ACCENT,
                              alpha=0.5, linewidth=1, linestyle='--',
                              zorder=2)
        ax.add_patch(rect)
        ax.text(0, 0, params.get('dielectric_label', 'κ'),
                ha='center', va='center', fontsize=14,
                color=ACCENT, fontweight='bold', zorder=4)

    # Labels
    labels = params.get('labels', {})
    if labels.get('left'):
        ax.text(-sep / 2 - 0.25, 0, labels['left'], ha='right', va='center',
                fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)
    if labels.get('right'):
        ax.text(sep / 2 + 0.25, 0, labels['right'], ha='left', va='center',
                fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)
    if labels.get('top'):
        ax.text(0, plen / 2 + 0.2, labels['top'], ha='center', va='bottom',
                fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)
    # bottom label rendered after dimension line

    # Dimension for d
    ax.annotate('', xy=(sep / 2, -plen / 2 - 0.35),
                xytext=(-sep / 2, -plen / 2 - 0.35),
                arrowprops=dict(arrowstyle='<->', color='#94A3B8', lw=1.2))
    ax.text(0, -plen / 2 - 0.5, '$d$', ha='center', va='top',
            fontsize=ANNOTATION_SIZE + 4, color='#94A3B8')

    # Bottom label below the d dimension
    if labels.get('bottom'):
        ax.text(0, -plen / 2 - 0.85, labels['bottom'], ha='center', va='top',
                fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)

    pad = max(sep, plen) * 0.4
    ax.set_xlim(-sep / 2 - pad, sep / 2 + pad)
    ax.set_ylim(-plen / 2 - 1.2, plen / 2 + 0.5)
    add_title(ax, params.get('title', ''))
    return fig, ax


# ── Circuit Diagrams (SchemDraw) ─────────────────────────────────────

def _render_circuit_diagram(params):
    """Circuit schematic using SchemDraw.

    params:
        elements : list of {type, label, value, direction}
            type: 'resistor'|'capacitor'|'battery'|'switch'|'ammeter'|
                  'voltmeter'|'wire'|'push'|'pop'
            label: component label (e.g. 'R₁')
            value: component value (e.g. '4 Ω')
            direction: 'right'|'down'|'left'|'up'
        title : str
    """
    import schemdraw
    import schemdraw.elements as elm

    ELEMENT_MAP = {
        'resistor': elm.Resistor,
        'capacitor': elm.Capacitor,
        'battery': elm.Battery,
        'switch': elm.Switch,
        'ammeter': elm.MeterA,
        'voltmeter': elm.MeterV,
        'wire': elm.Line,
        'dot': elm.Dot,
        'ground': elm.Ground,
        'lamp': elm.Lamp,
    }

    DIRECTION_MAP = {
        'right': 'right',
        'down': 'down',
        'left': 'left',
        'up': 'up',
    }

    d = schemdraw.Drawing(backend='matplotlib')

    # Track elements by enclose group for EncircleBox
    enclose_groups = {}

    for el in params.get('elements', []):
        el_type = el.get('type', 'wire')

        if el_type == 'push':
            d.push()
            continue
        elif el_type == 'pop':
            d.pop()
            continue

        cls = ELEMENT_MAP.get(el_type, elm.Line)
        direction = DIRECTION_MAP.get(el.get('direction', 'right'), 'right')

        element = cls()
        if el.get('reverse'):
            element = element.reverse()
        if el.get('length'):
            element = element.length(el['length'])
        element = getattr(element, direction)()

        label_text = el.get('label', '')
        value_text = el.get('value', '')
        if label_text and value_text:
            element = element.label(f'{label_text}\n{value_text}')
        elif label_text:
            element = element.label(label_text)
        elif value_text:
            element = element.label(value_text)

        added = d.add(element)

        # Track enclose groups
        group = el.get('enclose')
        if group:
            enclose_groups.setdefault(group, []).append(added)

    # Draw enclosure boxes (dashed rounded rectangles around grouped elements)
    for group_name, group_elms in enclose_groups.items():
        box = elm.EncircleBox(group_elms, padx=0.1, pady=0.1)
        box = box.linestyle('--').linewidth(1).color('#94A3B8')
        # Label the enclosure
        box = box.label(group_name, loc='top')
        d.add(box)

    # Render to matplotlib figure
    fig = d.draw()
    fig_mpl = fig.fig if hasattr(fig, 'fig') else plt.gcf()
    ax = fig_mpl.axes[0] if fig_mpl.axes else fig_mpl.add_subplot(111)

    title = params.get('title', '')
    if title:
        fig_mpl.subplots_adjust(top=0.85)
        fig_mpl.suptitle(title, fontsize=TITLE_SIZE, fontweight='bold',
                         color=TEXT_COLOR, y=0.97)

    return fig_mpl, ax


def _render_kirchhoff_diagram(params):
    """Circuit with Kirchhoff's loop/junction annotations using SchemDraw.

    params:
        elements : list (same as circuit_diagram)
        loops    : list of {label, color, position}  — loop current annotations
        junctions: list of {label, x, y}  — junction labels
        title    : str
    """
    import schemdraw
    import schemdraw.elements as elm

    ELEMENT_MAP = {
        'resistor': elm.Resistor,
        'capacitor': elm.Capacitor,
        'battery': elm.Battery,
        'switch': elm.Switch,
        'ammeter': elm.MeterA,
        'voltmeter': elm.MeterV,
        'wire': elm.Line,
        'dot': elm.Dot,
        'ground': elm.Ground,
        'lamp': elm.Lamp,
    }

    d = schemdraw.Drawing(backend='matplotlib')

    for el in params.get('elements', []):
        el_type = el.get('type', 'wire')

        if el_type == 'push':
            d.push()
            continue
        elif el_type == 'pop':
            d.pop()
            continue

        cls = ELEMENT_MAP.get(el_type, elm.Line)
        direction = el.get('direction', 'right')

        element = cls()
        if el.get('reverse'):
            element = element.reverse()
        if el.get('length'):
            element = element.length(el['length'])
        element = getattr(element, direction)()

        label_text = el.get('label', '')
        value_text = el.get('value', '')
        if label_text and value_text:
            element = element.label(f'{label_text}\n{value_text}')
        elif label_text:
            element = element.label(label_text)
        elif value_text:
            element = element.label(value_text)

        d.add(element)

    fig = d.draw()
    fig_mpl = fig.fig if hasattr(fig, 'fig') else plt.gcf()
    ax = fig_mpl.axes[0] if fig_mpl.axes else fig_mpl.add_subplot(111)

    # Add loop current annotations
    for loop in params.get('loops', []):
        pos = loop.get('position', [0, 0])
        color = loop.get('color', ACCENT)
        label = loop.get('label', '')
        # Circular loop arrow
        arc = plt.matplotlib.patches.FancyArrowPatch(
            (pos[0] - 0.4, pos[1]),
            (pos[0] + 0.4, pos[1]),
            connectionstyle="arc3,rad=0.8",
            arrowstyle='->', color=color, lw=1.5,
            mutation_scale=12, zorder=10)
        ax.add_patch(arc)
        ax.text(pos[0], pos[1] - 0.3, label, ha='center', va='top',
                fontsize=ANNOTATION_SIZE + 4, color=color, fontweight='bold',
                zorder=11)

    # Add junction labels
    for junc in params.get('junctions', []):
        ax.plot(junc['x'], junc['y'], 'o', color=PRIMARY, markersize=6,
                zorder=10)
        ax.text(junc['x'] + 0.15, junc['y'] + 0.15, junc.get('label', ''),
                fontsize=ANNOTATION_SIZE + 4, color=PRIMARY, fontweight='bold',
                zorder=11)

    title = params.get('title', '')
    if title:
        fig_mpl.subplots_adjust(top=0.85)
        fig_mpl.suptitle(title, fontsize=TITLE_SIZE, fontweight='bold',
                         color=TEXT_COLOR, y=0.97)

    return fig_mpl, ax


# ── Magnetic Field Diagrams ──────────────────────────────────────────

def _render_magnetic_field(params):
    """Magnetic field diagrams: bar magnet, wire, solenoid.

    params:
        style : 'bar_magnet' | 'wire' | 'solenoid'
        (sub-params vary by style)
        title : str
    """
    style = params.get('style', 'bar_magnet')
    if style == 'bar_magnet':
        return _render_b_field_magnet(params)
    elif style == 'wire':
        return _render_b_field_wire(params)
    elif style == 'solenoid':
        return _render_b_field_solenoid(params)
    return _render_b_field_magnet(params)


def _render_b_field_magnet(params):
    """B-field lines around a bar magnet."""
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    draw_bar_magnet(ax, (0, 0))

    # Draw field lines (dipole pattern)
    # Use a magnetic dipole field: B_x, B_y from a dipole at origin
    nx, ny = 200, 200
    xs = np.linspace(-3, 3, nx)
    ys = np.linspace(-3, 3, ny)
    X, Y = np.meshgrid(xs, ys)

    # Dipole moment along y-axis
    r2 = X ** 2 + Y ** 2
    r2 = np.maximum(r2, 0.2)
    r = np.sqrt(r2)
    # Magnetic dipole field components (m along y)
    Bx = 3 * X * Y / (r2 * r2 * r)
    By = (3 * Y * Y - r2) / (r2 * r2 * r)

    # Mask near the magnet body
    mask = (np.abs(X) < 0.4) & (np.abs(Y) < 0.7)
    Bx[mask] = 0
    By[mask] = 0

    ax.streamplot(X, Y, Bx, By, color='#64748B', linewidth=0.8,
                  density=1.5, arrowsize=1.0, zorder=1)

    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_b_field_wire(params):
    """B-field concentric circles around a current-carrying wire."""
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    current_dir = params.get('current_direction', 'out')

    # Draw the wire cross-section
    if current_dir == 'out':
        draw_out_of_page(ax, (0, 0), size=0.15)
        ax.text(0, -0.35, '$I$ (out)', ha='center', va='top',
                fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)
    else:
        draw_into_page(ax, (0, 0), size=0.15)
        ax.text(0, -0.35, '$I$ (in)', ha='center', va='top',
                fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)

    # Concentric B-field circles with arrows
    radii = [0.5, 1.0, 1.5, 2.0]
    for r in radii:
        theta = np.linspace(0, 2 * np.pi, 200)
        ax.plot(r * np.cos(theta), r * np.sin(theta), color='#64748B',
                lw=0.8, zorder=1)
        # Arrow indicator at top of each circle
        # CCW for current out of page (right-hand rule)
        arrow_angle = np.pi / 2  # top
        ccw = 1 if current_dir == 'out' else -1
        dx = -ccw * 0.12
        dy = 0
        ax.annotate('', xy=(dx + r * np.cos(arrow_angle),
                            r * np.sin(arrow_angle)),
                    xytext=(r * np.cos(arrow_angle),
                            r * np.sin(arrow_angle)),
                    arrowprops=dict(arrowstyle='->', color='#64748B',
                                    lw=1.2),
                    zorder=2)

    # Label B = μ₀I/(2πr)
    ax.text(2.3, 0, '$B = \\frac{\\mu_0 I}{2\\pi r}$',
            fontsize=16, color=TEXT_COLOR, va='center')

    ax.set_xlim(-2.8, 3.5)
    ax.set_ylim(-2.8, 2.8)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_b_field_solenoid(params):
    """B-field inside and around a solenoid."""
    fig, ax = create_figure(figsize=(7, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    n_turns = params.get('n_turns', 8)
    length = params.get('length', 4.0)
    radius = params.get('radius', 0.8)

    # Draw coil turns
    for i in range(n_turns):
        x = -length / 2 + (i + 0.5) * length / n_turns
        # Ellipse representing a turn viewed from the side
        ellipse = plt.matplotlib.patches.Ellipse(
            (x, 0), 0.15, 2 * radius,
            facecolor='none', edgecolor=PRIMARY, linewidth=1.2, zorder=3)
        ax.add_patch(ellipse)

    # Connect turns with wire along top and bottom
    x_start = -length / 2 + 0.5 * length / n_turns
    x_end = -length / 2 + (n_turns - 0.5) * length / n_turns
    ax.plot([x_start, x_end], [radius, radius], color=PRIMARY, lw=1.2, zorder=2)
    ax.plot([x_start, x_end], [-radius, -radius], color=PRIMARY, lw=1.2, zorder=2)

    # Uniform B-field arrows inside
    n_arrows = 5
    for i in range(n_arrows):
        x = -length / 2 + (i + 1) * length / (n_arrows + 1)
        ax.annotate('', xy=(x + 0.3, 0), xytext=(x - 0.3, 0),
                    arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.5),
                    zorder=4)

    # Label
    ax.text(0, -radius - 0.4, '$B = \\mu_0 n I$',
            ha='center', va='top', fontsize=ANNOTATION_SIZE + 4, color=TEXT_COLOR)
    ax.text(length / 2 + 0.3, 0, '$\\vec{B}$',
            ha='left', va='center', fontsize=12, color=ACCENT,
            fontweight='bold')

    ax.set_xlim(-length / 2 - 1, length / 2 + 1.5)
    ax.set_ylim(-radius - 0.8, radius + 0.8)
    add_title(ax, params.get('title', ''))
    return fig, ax


# ── Force on Moving Charge ───────────────────────────────────────────

def _render_force_on_charge(params):
    """Moving charge in B-field with F = qv × B.

    params:
        charge_sign    : '+' or '-'
        velocity_dir   : angle in degrees (in plane of diagram)
        b_field_dir    : 'into_page' | 'out_of_page' | angle in degrees
        show_circular  : bool (show circular path, default False)
        radius         : float (circular path radius if show_circular)
        labels         : {v, B, F}
        title          : str
    """
    fig, ax = create_figure()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    charge_pos = (0, 0)
    charge_sign = params.get('charge_sign', '+')
    v_angle = params.get('velocity_dir', 0)
    b_field = params.get('b_field_dir', 'into_page')
    labels = params.get('labels', {})

    # Draw B-field markers
    if b_field in ('into_page', 'out_of_page'):
        # Grid of markers
        for xi in np.arange(-2, 2.5, 0.8):
            for yi in np.arange(-2, 2.5, 0.8):
                if np.hypot(xi, yi) < 0.3:
                    continue
                if b_field == 'into_page':
                    draw_into_page(ax, (xi, yi), size=0.08)
                else:
                    draw_out_of_page(ax, (xi, yi), size=0.08)
        b_label = labels.get('B', '$\\vec{B}$ (into page)' if b_field == 'into_page'
                             else '$\\vec{B}$ (out of page)')
        ax.text(2.5, -2.5, b_label, fontsize=ANNOTATION_SIZE + 4 + 2,
                color='#94A3B8', ha='right', va='bottom')

    # Draw the charge
    draw_charge(ax, charge_pos, charge_sign, size=0.2)

    # Velocity arrow
    v_rad = np.radians(v_angle)
    v_len = 1.2
    v_end = (v_len * np.cos(v_rad), v_len * np.sin(v_rad))
    # Offset label perpendicular to arrow direction (to the left of arrow)
    # Allow manifest override via label_offsets.v
    label_offsets = params.get('label_offsets', {})
    if 'v' in label_offsets:
        v_label_offset = tuple(label_offsets['v'])
    else:
        v_perp = (np.cos(v_rad + np.pi/2), np.sin(v_rad + np.pi/2))
        v_label_offset = (0.25 * v_perp[0], 0.25 * v_perp[1])
    draw_arrow(ax, charge_pos, v_end,
               label=labels.get('v', '$\\vec{v}$'), color=SUCCESS,
               label_offset=v_label_offset)

    # Force arrow (F = qv × B)
    # For into-page B: F perpendicular to v, rotated 90° CW for +charge
    if b_field == 'into_page':
        f_angle = v_angle - 90 if charge_sign == '+' else v_angle + 90
    else:
        f_angle = v_angle + 90 if charge_sign == '+' else v_angle - 90

    f_rad = np.radians(f_angle)
    f_len = 1.0
    f_end = (f_len * np.cos(f_rad), f_len * np.sin(f_rad))
    # Offset label perpendicular to arrow direction (to the left of arrow)
    # Allow manifest override via label_offsets.F
    if 'F' in label_offsets:
        f_label_offset = tuple(label_offsets['F'])
    else:
        f_perp = (np.cos(f_rad + np.pi/2), np.sin(f_rad + np.pi/2))
        f_label_offset = (0.25 * f_perp[0], 0.25 * f_perp[1])
    draw_arrow(ax, charge_pos, f_end,
               label=labels.get('F', '$\\vec{F}$'), color=SECONDARY,
               label_offset=f_label_offset)

    # Circular path
    if params.get('show_circular', False):
        r = params.get('radius', 1.5)
        # Center of circular path is in the force direction
        cx = r * np.cos(f_rad)
        cy = r * np.sin(f_rad)
        theta = np.linspace(0, 2 * np.pi, 200)
        ax.plot(cx + r * np.cos(theta), cy + r * np.sin(theta),
                '--', color='#94A3B8', lw=1, zorder=1)
        ax.text(cx, cy, f'$r = mv/qB$', ha='center', va='center',
                fontsize=ANNOTATION_SIZE + 4 + 2, color='#94A3B8')

    # Formula annotation at bottom
    formula = params.get('formula', '$\\vec{F} = q\\vec{v} \\times \\vec{B}$')
    ax.text(0, -2.6, formula, ha='center', va='top',
            fontsize=16, color=TEXT_COLOR)

    ax.set_xlim(-2.8, 2.8)
    ax.set_ylim(-2.8, 3.0)
    add_title(ax, params.get('title', ''))
    return fig, ax


# ── RC Circuit Graph ─────────────────────────────────────────────────

def _render_rc_graph(params):
    """RC circuit charging/discharging voltage and current curves.

    params:
        style    : 'charging' | 'discharging'
        emf      : float (battery voltage for charging)
        R        : float (resistance in ohms)
        C        : float (capacitance in farads)
        show_current : bool (default True)
        title    : str
    """
    fig, ax = create_figure()

    style = params.get('style', 'charging')
    emf = params.get('emf', 10)
    R = params.get('R', 1000)
    C = params.get('C', 0.001)
    tau = R * C
    t_max = 5 * tau

    t = np.linspace(0, t_max, 500)

    if style == 'charging':
        V_c = emf * (1 - np.exp(-t / tau))
        I = (emf / R) * np.exp(-t / tau)
        v_label = '$V_C = \\varepsilon(1 - e^{-t/RC})$'
    else:
        V_c = emf * np.exp(-t / tau)
        I = -(emf / R) * np.exp(-t / tau)
        v_label = '$V_C = V_0 e^{-t/RC}$'

    ax.plot(t / tau, V_c, color=PRIMARY, linewidth=2.5, label='$V_C$', zorder=3)

    if params.get('show_current', True):
        ax2 = ax.twinx()
        ax2.plot(t / tau, I * 1000, color=SECONDARY, linewidth=2,
                 linestyle='--', label='$I$', zorder=3)
        ax2.set_ylabel('Current (mA)', fontsize=LABEL_SIZE, color=SECONDARY)
        ax2.tick_params(axis='y', labelcolor=SECONDARY)

    # Time constant markers
    ax.axvline(x=1, color='#94A3B8', linewidth=0.8, linestyle=':', zorder=1)
    ax.text(1, emf * 1.05, '$\\tau = RC$', ha='center', va='bottom',
            fontsize=ANNOTATION_SIZE + 4 + 2, color='#94A3B8')

    # Asymptote
    if style == 'charging':
        ax.axhline(y=emf, color=ACCENT, linewidth=0.8, linestyle=':', zorder=1)
        ax.text(5.1, emf, f'$\\varepsilon$ = {emf} V', va='center',
                fontsize=ANNOTATION_SIZE + 4 + 2, color=ACCENT)

    ax.set_xlabel('Time ($\\tau = RC$)', fontsize=LABEL_SIZE)
    ax.set_ylabel('Voltage (V)', fontsize=LABEL_SIZE, color=PRIMARY)
    ax.tick_params(axis='y', labelcolor=PRIMARY)
    ax.set_xlim(0, 5)
    ax.set_ylim(0, emf * 1.15)

    add_title(ax, params.get('title', ''))
    return fig, ax


# ── Dispatch table ───────────────────────────────────────────────────

_DISPATCH = {
    'field_line_diagram': _render_field_line_diagram,
    'equipotential_diagram': _render_equipotential_diagram,
    'capacitor_diagram': _render_capacitor_diagram,
    'circuit_diagram': _render_circuit_diagram,
    'kirchhoff_diagram': _render_kirchhoff_diagram,
    'magnetic_field': _render_magnetic_field,
    'force_on_charge': _render_force_on_charge,
    'rc_graph': _render_rc_graph,
}


def render(entry, output_dir):
    """Render an electromagnetism diagram from manifest entry."""
    params = entry['params']
    diagram_type = params.get('type', 'field_line_diagram')

    renderer = _DISPATCH.get(diagram_type)
    if not renderer:
        raise ValueError(f"Unknown electromagnetism diagram type: {diagram_type}")

    fig, ax = renderer(params)

    filename = entry['bucket_key'].split('/')[-1]
    path = Path(output_dir) / filename

    # SchemDraw figures need special handling
    if diagram_type in ('circuit_diagram', 'kirchhoff_diagram'):
        fig.savefig(path, format='svg', bbox_inches='tight',
                    facecolor=BG_COLOR)
        plt.close(fig)
    else:
        save_figure(fig, path)

    return path
