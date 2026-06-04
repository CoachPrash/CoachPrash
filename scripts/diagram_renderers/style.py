"""Shared style constants for CoachPrash diagram renderers."""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Color palette matching CoachPrash CSS variables
PRIMARY = '#1B365D'
SECONDARY = '#C41E3A'
ACCENT = '#F4A100'
SUCCESS = '#2D8659'
GRID_COLOR = '#E2E8F0'
BG_COLOR = '#FFFFFF'
TEXT_COLOR = '#1A1A2E'

# Additional plot colors for multiple curves
COLORS = [PRIMARY, SECONDARY, SUCCESS, ACCENT, '#7C3AED', '#0891B2']

# Standard figure size
FIG_SIZE = (6, 4)
DPI = 150

# Font sizes
TITLE_SIZE = 14
LABEL_SIZE = 12
TICK_SIZE = 10
ANNOTATION_SIZE = 10


def create_figure(figsize=None):
    """Create a styled figure and axes."""
    fig, ax = plt.subplots(figsize=figsize or FIG_SIZE)
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)
    ax.grid(True, linestyle='--', alpha=0.3, color=GRID_COLOR)
    ax.tick_params(labelsize=TICK_SIZE)
    for spine in ax.spines.values():
        spine.set_color('#94A3B8')
    return fig, ax


def save_figure(fig, path, fmt='svg'):
    """Save figure and close."""
    fig.savefig(path, format=fmt, bbox_inches='tight',
                facecolor=BG_COLOR, dpi=DPI if fmt == 'png' else None)
    plt.close(fig)


def add_title(ax, title):
    """Add styled title to axes."""
    if title:
        ax.set_title(title, fontsize=TITLE_SIZE, fontweight='bold',
                     color=TEXT_COLOR, pad=12)
