"""Shared drawing primitives for physics diagram renderers."""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from .style import FORCE_COLORS, PRIMARY, SECONDARY, ACCENT, TEXT_COLOR, LABEL_SIZE, ANNOTATION_SIZE


def draw_arrow(ax, start, end, label='', color=PRIMARY, lw=2.5, head_width=0.06,
               label_offset=(0, 0), fontsize=None, zorder=5):
    """Draw a labeled force/velocity/momentum arrow.

    Parameters
    ----------
    start, end : tuple (x, y)
    label : str  – LaTeX-friendly label placed near the tip
    color : str
    label_offset : tuple – manual nudge for the label position
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    ax.annotate('', xy=end, xytext=start,
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                mutation_scale=15),
                zorder=zorder)
    if label:
        mid_x = (start[0] + end[0]) / 2 + label_offset[0]
        mid_y = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(mid_x, mid_y, label, color=color,
                fontsize=fontsize or ANNOTATION_SIZE, fontweight='bold',
                ha='center', va='center', zorder=zorder + 1)


def draw_force_arrow(ax, origin, angle_deg, length, label='', force_type='applied',
                     label_offset=(0, 0)):
    """Draw a force arrow from *origin* at *angle_deg* (CCW from +x).

    Uses FORCE_COLORS to colour-code by force type.
    """
    rad = np.radians(angle_deg)
    end = (origin[0] + length * np.cos(rad),
           origin[1] + length * np.sin(rad))
    color = FORCE_COLORS.get(force_type, FORCE_COLORS.get('applied'))
    draw_arrow(ax, origin, end, label=label, color=color,
               label_offset=label_offset)
    return end


def draw_object(ax, pos, shape='block', size=0.4, label='', color='#E2E8F0',
                edgecolor=TEXT_COLOR, zorder=3):
    """Draw a simple object (block, circle, or dot) at *pos*.

    Returns the centre coordinates.
    """
    x, y = pos
    if shape == 'block':
        rect = patches.FancyBboxPatch(
            (x - size / 2, y - size / 2), size, size,
            boxstyle='round,pad=0.02', facecolor=color,
            edgecolor=edgecolor, linewidth=1.5, zorder=zorder)
        ax.add_patch(rect)
    elif shape == 'circle':
        circ = plt.Circle((x, y), size / 2, facecolor=color,
                          edgecolor=edgecolor, linewidth=1.5, zorder=zorder)
        ax.add_patch(circ)
    elif shape == 'dot':
        ax.plot(x, y, 'o', color=edgecolor, markersize=size * 20, zorder=zorder)
    if label:
        ax.text(x, y, label, ha='center', va='center',
                fontsize=ANNOTATION_SIZE, fontweight='bold',
                color=TEXT_COLOR, zorder=zorder + 1)
    return (x, y)


def draw_ground(ax, x_range, y=0, hatch_height=0.15):
    """Draw a hatched ground surface spanning *x_range* at height *y*."""
    x0, x1 = x_range
    ax.plot([x0, x1], [y, y], color=TEXT_COLOR, lw=2, zorder=2)
    ax.fill_between([x0, x1], y, y - hatch_height,
                    hatch='///', facecolor='none', edgecolor='#94A3B8',
                    linewidth=0.5, zorder=1)


def draw_surface(ax, x_range, y=0, angle_deg=0):
    """Draw a surface (optionally inclined) spanning *x_range*."""
    rad = np.radians(angle_deg)
    x0, x1 = x_range
    length = x1 - x0
    ax.plot([x0, x0 + length * np.cos(rad)],
            [y, y + length * np.sin(rad)],
            color=TEXT_COLOR, lw=2, zorder=2)


def draw_spring(ax, start, end, coils=6, width=0.15, color='#94A3B8', lw=1.5):
    """Draw a coiled spring between *start* and *end*."""
    x0, y0 = start
    x1, y1 = end
    length = np.hypot(x1 - x0, y1 - y0)
    angle = np.arctan2(y1 - y0, x1 - x0)

    # Build spring profile along local x-axis
    n_pts = coils * 20
    t = np.linspace(0, 1, n_pts)
    # Straight lead-in/out (10% each side)
    sx = t * length
    sy = np.zeros_like(t)
    mask = (t > 0.1) & (t < 0.9)
    sy[mask] = width * np.sin(2 * np.pi * coils * (t[mask] - 0.1) / 0.8)

    # Rotate to actual angle
    rx = sx * np.cos(angle) - sy * np.sin(angle) + x0
    ry = sx * np.sin(angle) + sy * np.cos(angle) + y0
    ax.plot(rx, ry, color=color, lw=lw, zorder=2)


def draw_pivot(ax, pos, size=0.12, color=TEXT_COLOR):
    """Draw a triangular pivot/fulcrum at *pos*."""
    x, y = pos
    triangle = plt.Polygon([
        (x - size, y - size),
        (x + size, y - size),
        (x, y),
    ], closed=True, facecolor='#E2E8F0', edgecolor=color, lw=1.5, zorder=3)
    ax.add_patch(triangle)


def draw_angle_arc(ax, center, radius, start_deg, end_deg, label='',
                   color=TEXT_COLOR, lw=1.5):
    """Draw an arc showing an angle, with optional label."""
    arc = patches.Arc(center, 2 * radius, 2 * radius,
                      angle=0, theta1=start_deg, theta2=end_deg,
                      color=color, lw=lw, zorder=4)
    ax.add_patch(arc)
    if label:
        mid_deg = (start_deg + end_deg) / 2
        rad = np.radians(mid_deg)
        lx = center[0] + radius * 1.35 * np.cos(rad)
        ly = center[1] + radius * 1.35 * np.sin(rad)
        ax.text(lx, ly, label, ha='center', va='center',
                fontsize=ANNOTATION_SIZE, color=color, zorder=5)


def draw_wall(ax, x, y_range, side='left'):
    """Draw a wall with hatching on one side."""
    y0, y1 = y_range
    ax.plot([x, x], [y0, y1], color=TEXT_COLOR, lw=2, zorder=2)
    hatch_w = 0.12
    if side == 'left':
        ax.fill_betweenx([y0, y1], x - hatch_w, x,
                         hatch='///', facecolor='none', edgecolor='#94A3B8',
                         linewidth=0.5, zorder=1)
    else:
        ax.fill_betweenx([y0, y1], x, x + hatch_w,
                         hatch='///', facecolor='none', edgecolor='#94A3B8',
                         linewidth=0.5, zorder=1)


def draw_dimension(ax, start, end, label='', offset=0.15, color='#94A3B8'):
    """Draw a dimensioning line with end ticks and a centred label."""
    x0, y0 = start
    x1, y1 = end
    # Offset perpendicular
    dx, dy = x1 - x0, y1 - y0
    length = np.hypot(dx, dy)
    if length == 0:
        return
    nx, ny = -dy / length * offset, dx / length * offset
    sx, sy = x0 + nx, y0 + ny
    ex, ey = x1 + nx, y1 + ny
    ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1))
    if label:
        ax.text((sx + ex) / 2, (sy + ey) / 2, label,
                ha='center', va='center', fontsize=ANNOTATION_SIZE - 1,
                color=color, backgroundcolor='white', zorder=6)


# ── E&M primitives ────────────────────────────────────────────────────

def draw_charge(ax, pos, sign, label='', size=0.18, fontsize=None):
    """Draw a point charge (+ or −) with optional label.

    Parameters
    ----------
    pos : tuple (x, y)
    sign : '+' or '-'
    label : str – text placed beside the charge
    """
    x, y = pos
    color = SECONDARY if sign == '+' else PRIMARY
    circ = plt.Circle((x, y), size, facecolor=color + '22',
                       edgecolor=color, linewidth=1.5, zorder=5)
    ax.add_patch(circ)
    ax.text(x, y, sign, ha='center', va='center', fontsize=fontsize or 14,
            fontweight='bold', color=color, zorder=6)
    if label:
        ax.text(x, y - size - 0.12, label, ha='center', va='top',
                fontsize=ANNOTATION_SIZE, color=TEXT_COLOR, zorder=6)


def draw_into_page(ax, pos, size=0.12):
    """Draw an ⊗ marker (vector into the page)."""
    x, y = pos
    circ = plt.Circle((x, y), size, facecolor='white', edgecolor=TEXT_COLOR,
                       linewidth=1.2, zorder=5)
    ax.add_patch(circ)
    s = size * 0.7
    ax.plot([x - s, x + s], [y - s, y + s], color=TEXT_COLOR, lw=1.2, zorder=6)
    ax.plot([x - s, x + s], [y + s, y - s], color=TEXT_COLOR, lw=1.2, zorder=6)


def draw_out_of_page(ax, pos, size=0.12):
    """Draw an ⊙ marker (vector out of the page)."""
    x, y = pos
    circ = plt.Circle((x, y), size, facecolor='white', edgecolor=TEXT_COLOR,
                       linewidth=1.2, zorder=5)
    ax.add_patch(circ)
    ax.plot(x, y, 'o', color=TEXT_COLOR, markersize=size * 18, zorder=6)


def draw_plate(ax, center, length, orientation='vertical', label='',
               charge_sign=None, color=TEXT_COLOR):
    """Draw a charged plate (for capacitor diagrams).

    Parameters
    ----------
    center : tuple (x, y)
    length : float
    orientation : 'vertical' or 'horizontal'
    charge_sign : '+' or '-' to show distributed charges
    """
    x, y = center
    if orientation == 'vertical':
        ax.plot([x, x], [y - length / 2, y + length / 2],
                color=color, lw=3, solid_capstyle='butt', zorder=3)
        if charge_sign:
            n = 5
            for i in range(n):
                yi = y - length / 2 + (i + 0.5) * length / n
                ch_color = SECONDARY if charge_sign == '+' else PRIMARY
                ax.text(x + (0.08 if charge_sign == '+' else -0.08), yi,
                        charge_sign, ha='center', va='center', fontsize=7,
                        color=ch_color, zorder=4)
    else:
        ax.plot([x - length / 2, x + length / 2], [y, y],
                color=color, lw=3, solid_capstyle='butt', zorder=3)
    if label:
        ax.text(x, y - length / 2 - 0.15, label, ha='center', va='top',
                fontsize=ANNOTATION_SIZE, color=TEXT_COLOR, zorder=4)


def draw_field_lines(ax, charges, x_range, y_range, density=20):
    """Draw electric field lines from a list of point charges using streamplot.

    Parameters
    ----------
    charges : list of (x, y, q) tuples
    x_range : (xmin, xmax)
    y_range : (ymin, ymax)
    density : streamplot density
    """
    nx, ny = 200, 200
    xs = np.linspace(x_range[0], x_range[1], nx)
    ys = np.linspace(y_range[0], y_range[1], ny)
    X, Y = np.meshgrid(xs, ys)
    Ex = np.zeros_like(X)
    Ey = np.zeros_like(Y)

    for cx, cy, q in charges:
        dx = X - cx
        dy = Y - cy
        r2 = dx ** 2 + dy ** 2
        r2 = np.maximum(r2, 0.04)  # avoid singularity
        r = np.sqrt(r2)
        Ex += q * dx / (r2 * r)
        Ey += q * dy / (r2 * r)

    # Normalize for consistent arrow lengths
    mag = np.sqrt(Ex ** 2 + Ey ** 2)
    mag = np.maximum(mag, 1e-10)

    ax.streamplot(X, Y, Ex, Ey, color='#64748B', linewidth=0.8,
                  density=density / 10, arrowsize=1.0, zorder=2)


def draw_bar_magnet(ax, center, width=0.6, height=1.2):
    """Draw a bar magnet with N and S poles."""
    x, y = center
    # North half (red)
    north = patches.FancyBboxPatch(
        (x - width / 2, y), width, height / 2,
        boxstyle='round,pad=0.02', facecolor='#FEE2E2',
        edgecolor=SECONDARY, linewidth=1.5, zorder=3)
    ax.add_patch(north)
    ax.text(x, y + height / 4, 'N', ha='center', va='center',
            fontsize=12, fontweight='bold', color=SECONDARY, zorder=4)
    # South half (blue)
    south = patches.FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height / 2,
        boxstyle='round,pad=0.02', facecolor='#DBEAFE',
        edgecolor=PRIMARY, linewidth=1.5, zorder=3)
    ax.add_patch(south)
    ax.text(x, y - height / 4, 'S', ha='center', va='center',
            fontsize=12, fontweight='bold', color=PRIMARY, zorder=4)
