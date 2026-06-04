"""Renderer for AP Statistics diagram types."""
import numpy as np
from pathlib import Path
from scipy import stats as scipy_stats
from .style import *


def _render_normal(params):
    """Normal curve with optional shading and z-score markers."""
    fig, ax = create_figure()
    mu = params.get('mu', 0)
    sigma = params.get('sigma', 1)

    x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 500)
    y = scipy_stats.norm.pdf(x, mu, sigma)

    ax.plot(x, y, color=PRIMARY, linewidth=2.5, zorder=3)
    ax.fill_between(x, y, alpha=0.08, color=PRIMARY, zorder=2)

    # Shading options
    if 'shade_left' in params:
        bound = params['shade_left']
        mask = x <= bound
        ax.fill_between(x[mask], y[mask], alpha=0.35, color=SECONDARY, zorder=2,
                        label=f'$P(X \\leq {bound})$')
    if 'shade_right' in params:
        bound = params['shade_right']
        mask = x >= bound
        ax.fill_between(x[mask], y[mask], alpha=0.35, color=SECONDARY, zorder=2,
                        label=f'$P(X \\geq {bound})$')
    if 'shade_between' in params:
        lo, hi = params['shade_between']
        mask = (x >= lo) & (x <= hi)
        ax.fill_between(x[mask], y[mask], alpha=0.35, color=SUCCESS, zorder=2,
                        label=f'$P({lo} \\leq X \\leq {hi})$')

    # σ markers (68-95-99.7 rule)
    if params.get('show_empirical'):
        for k, pct in [(1, '68%'), (2, '95%'), (3, '99.7%')]:
            for sign in [-1, 1]:
                xv = mu + sign * k * sigma
                ax.axvline(xv, color='#94A3B8', linestyle=':', linewidth=1, zorder=1)
            # bracket label
            ax.annotate(pct, xy=(mu, scipy_stats.norm.pdf(mu + k * sigma, mu, sigma)),
                       fontsize=ANNOTATION_SIZE - 1, ha='center', va='bottom',
                       xytext=(0, 5 + k * 8), textcoords='offset points',
                       color=TEXT_COLOR)

    # z-score labels on x-axis
    if params.get('z_scores'):
        for z in params['z_scores']:
            xv = mu + z * sigma
            ax.annotate(f'$z={z}$', xy=(xv, 0), fontsize=ANNOTATION_SIZE - 1,
                       ha='center', va='top', xytext=(0, -8),
                       textcoords='offset points', color=SECONDARY)

    # μ marker
    ax.axvline(mu, color=TEXT_COLOR, linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    ax.annotate(f'$\\mu = {mu}$', xy=(mu, max(y) * 1.05), fontsize=ANNOTATION_SIZE,
               ha='center', va='bottom')

    ax.set_ylabel('Density', fontsize=LABEL_SIZE)
    ax.set_ylim(bottom=0)
    if ax.get_legend_handles_labels()[1]:
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_histogram(params):
    """Histogram for frequency distributions."""
    fig, ax = create_figure()

    if 'data' in params:
        data = params['data']
        n_bins = params.get('n_bins', 10)
        ax.hist(data, bins=n_bins, color=PRIMARY, edgecolor='white',
                linewidth=1.2, alpha=0.85, zorder=3)
    elif 'bins' in params and 'frequencies' in params:
        bins = params['bins']
        freqs = params['frequencies']
        widths = [bins[i + 1] - bins[i] for i in range(len(freqs))]
        ax.bar(bins[:len(freqs)], freqs, width=widths, align='edge',
               color=PRIMARY, edgecolor='white', linewidth=1.2, alpha=0.85, zorder=3)
    elif 'categories' in params and 'frequencies' in params:
        cats = params['categories']
        freqs = params['frequencies']
        colors = [COLORS[i % len(COLORS)] for i in range(len(cats))]
        bars = ax.bar(cats, freqs, color=colors, edgecolor='white',
                      linewidth=1.2, alpha=0.85, zorder=3)
        # Add value labels on bars
        for bar, freq in zip(bars, freqs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(freq), ha='center', va='bottom', fontsize=ANNOTATION_SIZE,
                    color=TEXT_COLOR)

    ax.set_xlabel(params.get('x_label', ''), fontsize=LABEL_SIZE)
    ax.set_ylabel(params.get('y_label', 'Frequency'), fontsize=LABEL_SIZE)
    ax.set_ylim(bottom=0)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_boxplot(params):
    """Horizontal box plot with five-number summary."""
    fig, ax = create_figure()
    datasets = params.get('datasets', [])

    if not datasets:
        return fig, ax

    labels = []
    box_data = []

    for ds in datasets:
        labels.append(ds.get('label', ''))
        # Build synthetic data from five-number summary
        q1, med, q3 = ds['q1'], ds['median'], ds['q3']
        lo, hi = ds['min'], ds['max']
        box_data.append([lo, q1, q1, med, med, med, q3, q3, hi])

    bp = ax.boxplot(box_data, labels=labels, vert=False, patch_artist=True,
                    medianprops=dict(color=SECONDARY, linewidth=2),
                    whiskerprops=dict(color=PRIMARY, linewidth=1.5),
                    capprops=dict(color=PRIMARY, linewidth=1.5),
                    flierprops=dict(marker='o', markerfacecolor=ACCENT,
                                   markeredgecolor=ACCENT, markersize=6))

    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(COLORS[i % len(COLORS)])
        patch.set_alpha(0.3)
        patch.set_edgecolor(COLORS[i % len(COLORS)])
        patch.set_linewidth(1.5)

    # Plot outliers from manifest data
    for i, ds in enumerate(datasets):
        if 'outliers' in ds:
            for outlier in ds['outliers']:
                ax.plot(outlier, i + 1, 'o', markersize=7,
                       markerfacecolor=ACCENT, markeredgecolor=ACCENT, zorder=5)

    # Annotate five-number summary on first dataset if only one
    if len(datasets) == 1 and params.get('annotate', True):
        ds = datasets[0]
        for val, label in [(ds['min'], 'Min'), (ds['q1'], '$Q_1$'),
                           (ds['median'], 'Med'), (ds['q3'], '$Q_3$'),
                           (ds['max'], 'Max')]:
            ax.annotate(f'{label}={val}', xy=(val, 1),
                       fontsize=ANNOTATION_SIZE - 1, ha='center', va='bottom',
                       xytext=(0, 22), textcoords='offset points',
                       color=TEXT_COLOR,
                       arrowprops=dict(arrowstyle='->', color='#94A3B8', lw=0.8))

    # Auto-pad x-axis so labels/values never clip at edges
    all_vals = []
    for ds in datasets:
        all_vals.extend([ds['min'], ds['max']])
        if 'outliers' in ds:
            all_vals.extend(ds['outliers'])
    data_min, data_max = min(all_vals), max(all_vals)
    data_range = data_max - data_min
    pad = max(data_range * 0.15, 5)  # at least 15% padding or 5 units
    # Round to nice numbers
    nice_min = np.floor((data_min - pad) / 5) * 5
    nice_max = np.ceil((data_max + pad) / 5) * 5
    ax.set_xlim(nice_min, nice_max)

    ax.set_xlabel(params.get('x_label', params.get('y_label', '')), fontsize=LABEL_SIZE)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_scatter(params):
    """Scatter plot with optional regression line."""
    fig, ax = create_figure()
    points = params.get('points', [])

    xs = [p['x'] for p in points]
    ys = [p['y'] for p in points]

    ax.scatter(xs, ys, color=PRIMARY, s=50, alpha=0.7, edgecolors='white',
              linewidth=0.5, zorder=4)

    if 'regression_line' in params:
        rl = params['regression_line']
        slope, intercept = rl['slope'], rl['intercept']
        x_line = np.linspace(min(xs) - 0.5, max(xs) + 0.5, 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color=SECONDARY, linewidth=2, zorder=3,
               label=f'$\\hat{{y}} = {slope:.2f}x + {intercept:.2f}$')

    if 'r_value' in params:
        r = params['r_value']
        # Place annotation in corner away from regression line:
        # positive slope → line goes bottom-left to top-right → use top-left
        # negative slope → line goes top-left to bottom-right → use top-right
        slope = params.get('regression_line', {}).get('slope', 0)
        if slope >= 0:
            anchor_x, anchor_y, ha = 0.05, 0.95, 'left'
        else:
            anchor_x, anchor_y, ha = 0.95, 0.95, 'right'
        ax.annotate(f'$r = {r:.3f}$\n$r^2 = {r**2:.3f}$',
                   xy=(anchor_x, anchor_y), xycoords='axes fraction',
                   fontsize=ANNOTATION_SIZE, ha=ha, va='top',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9C4',
                            edgecolor='#F59E0B', alpha=0.9))

    labels = params.get('labels', {})
    ax.set_xlabel(labels.get('x', ''), fontsize=LABEL_SIZE)
    ax.set_ylabel(labels.get('y', ''), fontsize=LABEL_SIZE)

    if ax.get_legend_handles_labels()[1]:
        ax.legend(fontsize=LABEL_SIZE - 2, loc='best')

    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_residual(params):
    """Residual plot with horizontal reference line at 0."""
    fig, ax = create_figure()
    points = params.get('points', [])

    xs = [p['x'] for p in points]
    residuals = [p['residual'] for p in points]

    ax.scatter(xs, residuals, color=PRIMARY, s=50, alpha=0.7,
              edgecolors='white', linewidth=0.5, zorder=4)
    ax.axhline(y=0, color=SECONDARY, linewidth=1.5, linestyle='--', zorder=2)

    labels = params.get('labels', {})
    ax.set_xlabel(labels.get('x', 'x'), fontsize=LABEL_SIZE)
    ax.set_ylabel(labels.get('y', 'Residual'), fontsize=LABEL_SIZE)

    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_venn(params):
    """Two-circle Venn diagram for probability concepts."""
    fig, ax = create_figure(figsize=(6, 4.5))
    ax.set_xlim(-3, 3)
    ax.set_ylim(-2, 2.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.grid(False)

    sets = params.get('sets', [{'label': 'A', 'value': ''}, {'label': 'B', 'value': ''}])
    intersection = params.get('intersection', None)
    is_mutually_exclusive = params.get('mutually_exclusive', False)

    if is_mutually_exclusive:
        # Non-overlapping circles
        c1 = plt.Circle((-1.2, 0), 1.0, fill=True, facecolor=PRIMARY,
                        edgecolor=PRIMARY, linewidth=2, alpha=0.25, zorder=2)
        c2 = plt.Circle((1.2, 0), 1.0, fill=True, facecolor=SECONDARY,
                        edgecolor=SECONDARY, linewidth=2, alpha=0.25, zorder=2)
        ax.add_patch(c1)
        ax.add_patch(c2)
        ax.text(-1.2, 0, sets[0].get('label', 'A'), fontsize=LABEL_SIZE + 2,
               ha='center', va='center', fontweight='bold', color=PRIMARY)
        ax.text(1.2, 0, sets[1].get('label', 'B'), fontsize=LABEL_SIZE + 2,
               ha='center', va='center', fontweight='bold', color=SECONDARY)
        # Values
        if sets[0].get('value'):
            ax.text(-1.2, -0.4, str(sets[0]['value']), fontsize=ANNOTATION_SIZE,
                   ha='center', va='center', color=TEXT_COLOR)
        if sets[1].get('value'):
            ax.text(1.2, -0.4, str(sets[1]['value']), fontsize=ANNOTATION_SIZE,
                   ha='center', va='center', color=TEXT_COLOR)
        # "No overlap" annotation
        ax.annotate('$A \\cap B = \\emptyset$', xy=(0, -1.5),
                   fontsize=ANNOTATION_SIZE + 1, ha='center', color=TEXT_COLOR)
    else:
        # Overlapping circles
        c1 = plt.Circle((-0.6, 0), 1.0, fill=True, facecolor=PRIMARY,
                        edgecolor=PRIMARY, linewidth=2, alpha=0.2, zorder=2)
        c2 = plt.Circle((0.6, 0), 1.0, fill=True, facecolor=SECONDARY,
                        edgecolor=SECONDARY, linewidth=2, alpha=0.2, zorder=2)
        ax.add_patch(c1)
        ax.add_patch(c2)
        ax.text(-1.1, 0.3, sets[0].get('label', 'A'), fontsize=LABEL_SIZE + 2,
               ha='center', va='center', fontweight='bold', color=PRIMARY)
        ax.text(1.1, 0.3, sets[1].get('label', 'B'), fontsize=LABEL_SIZE + 2,
               ha='center', va='center', fontweight='bold', color=SECONDARY)
        # Values in regions
        if sets[0].get('value'):
            ax.text(-1.0, -0.3, str(sets[0]['value']), fontsize=ANNOTATION_SIZE,
                   ha='center', va='center', color=TEXT_COLOR)
        if sets[1].get('value'):
            ax.text(1.0, -0.3, str(sets[1]['value']), fontsize=ANNOTATION_SIZE,
                   ha='center', va='center', color=TEXT_COLOR)
        if intersection is not None:
            ax.text(0, 0, str(intersection), fontsize=ANNOTATION_SIZE + 1,
                   ha='center', va='center', fontweight='bold', color=TEXT_COLOR)

        # Shade intersection if requested
        if params.get('shade_intersection'):
            c1_patch = plt.Circle((-0.6, 0), 1.0, transform=ax.transData)
            c2_fill = plt.Circle((0.6, 0), 1.0, fill=True, facecolor=ACCENT,
                                edgecolor='none', alpha=0.4, zorder=3)
            ax.add_patch(c2_fill)
            c2_fill.set_clip_path(c1_patch)

    # Universal set rectangle
    if params.get('show_universal', True):
        rect = plt.Rectangle((-2.8, -1.8), 5.6, 3.8, fill=False,
                             edgecolor='#94A3B8', linewidth=1.5, linestyle='-', zorder=1)
        ax.add_patch(rect)
        ax.text(-2.6, 1.7, '$U$', fontsize=LABEL_SIZE, color='#94A3B8')

    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_dotplot(params):
    """Dot plot: dots stacked at values on a number line."""
    fig, ax = create_figure()
    values = params.get('values', [])

    # Count occurrences
    from collections import Counter
    counts = Counter(values)

    for val, count in counts.items():
        for i in range(count):
            ax.plot(val, i + 1, 'o', markersize=10, markerfacecolor=PRIMARY,
                   markeredgecolor='white', markeredgewidth=1, zorder=3)

    if counts:
        max_count = max(counts.values())
        ax.set_ylim(0, max_count + 1)
        ax.set_yticks(range(1, max_count + 1))

    ax.set_xlabel(params.get('x_label', ''), fontsize=LABEL_SIZE)
    ax.set_ylabel('Count', fontsize=LABEL_SIZE)
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_sampling(params):
    """Population vs sampling distribution overlay."""
    fig, ax = create_figure()
    pop_mu = params.get('pop_mu', 50)
    pop_sigma = params.get('pop_sigma', 10)
    n = params.get('n', 30)

    se = pop_sigma / np.sqrt(n)

    # Population distribution (wider)
    x_pop = np.linspace(pop_mu - 4 * pop_sigma, pop_mu + 4 * pop_sigma, 500)
    y_pop = scipy_stats.norm.pdf(x_pop, pop_mu, pop_sigma)
    ax.plot(x_pop, y_pop, color='#94A3B8', linewidth=2, linestyle='--',
           label=f'Population ($\\sigma = {pop_sigma}$)', zorder=2)
    ax.fill_between(x_pop, y_pop, alpha=0.08, color='#94A3B8')

    # Sampling distribution (narrower, taller)
    x_samp = np.linspace(pop_mu - 4 * se, pop_mu + 4 * se, 500)
    y_samp = scipy_stats.norm.pdf(x_samp, pop_mu, se)
    ax.plot(x_samp, y_samp, color=PRIMARY, linewidth=2.5,
           label=f'Sampling dist. of $\\bar{{x}}$ ($n={n}$, $\\sigma_{{\\bar{{x}}}} = {se:.2f}$)',
           zorder=3)
    ax.fill_between(x_samp, y_samp, alpha=0.2, color=PRIMARY)

    ax.axvline(pop_mu, color=TEXT_COLOR, linestyle=':', linewidth=1, alpha=0.5)
    ax.annotate(f'$\\mu = {pop_mu}$', xy=(pop_mu, 0), fontsize=ANNOTATION_SIZE,
               ha='center', va='top', xytext=(0, -22), textcoords='offset points')

    ax.set_ylabel('Density', fontsize=LABEL_SIZE)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=LABEL_SIZE - 2, loc='best')
    add_title(ax, params.get('title', ''))
    return fig, ax


def _render_ci(params):
    """Confidence interval on a number line."""
    fig, ax = create_figure(figsize=(7, 2.5))

    estimate = params.get('estimate', 0.5)
    margin = params.get('margin', 0.05)
    lo = estimate - margin
    hi = estimate + margin
    cl_label = params.get('cl_label', '95% CI')
    parameter = params.get('parameter', 'p')

    # Horizontal line
    ax.axhline(y=0, color='#94A3B8', linewidth=1.5, zorder=1)

    # CI bracket
    ax.plot([lo, hi], [0, 0], color=PRIMARY, linewidth=4, solid_capstyle='round', zorder=3)
    ax.plot([lo, lo], [-0.15, 0.15], color=PRIMARY, linewidth=2.5, zorder=3)
    ax.plot([hi, hi], [-0.15, 0.15], color=PRIMARY, linewidth=2.5, zorder=3)

    # Point estimate
    ax.plot(estimate, 0, 'o', markersize=10, markerfacecolor=SECONDARY,
           markeredgecolor='white', markeredgewidth=2, zorder=5)

    # Labels
    ax.annotate(f'$\\hat{{{parameter}}} = {estimate}$', xy=(estimate, 0),
               fontsize=ANNOTATION_SIZE + 1, ha='center', va='bottom',
               xytext=(0, 15), textcoords='offset points', fontweight='bold')
    ax.annotate(f'{lo:.3f}', xy=(lo, 0), fontsize=ANNOTATION_SIZE,
               ha='center', va='top', xytext=(0, -15), textcoords='offset points')
    ax.annotate(f'{hi:.3f}', xy=(hi, 0), fontsize=ANNOTATION_SIZE,
               ha='center', va='top', xytext=(0, -15), textcoords='offset points')

    # CI label
    mid = (lo + hi) / 2
    ax.annotate(cl_label, xy=(mid, 0), fontsize=LABEL_SIZE,
               ha='center', va='bottom', xytext=(0, 35), textcoords='offset points',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9',
                        edgecolor=SUCCESS, alpha=0.9))

    # Margin of error annotation
    ax.annotate('', xy=(hi, -0.3), xytext=(estimate, -0.3),
               arrowprops=dict(arrowstyle='<->', color=ACCENT, lw=1.5))
    ax.text((estimate + hi) / 2, -0.4, f'ME = {margin:.3f}',
           fontsize=ANNOTATION_SIZE - 1, ha='center', va='top', color=ACCENT)

    padding = margin * 1.5
    ax.set_xlim(lo - padding, hi + padding)
    ax.set_ylim(-0.7, 0.7)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    add_title(ax, params.get('title', ''))
    return fig, ax


# Dispatch table
_DISPATCH = {
    'normal_curve': _render_normal,
    'histogram': _render_histogram,
    'boxplot': _render_boxplot,
    'scatter_regression': _render_scatter,
    'residual_plot': _render_residual,
    'venn': _render_venn,
    'dotplot': _render_dotplot,
    'sampling_distribution': _render_sampling,
    'confidence_interval': _render_ci,
}


def render(entry, output_dir):
    """Render a statistics diagram from manifest entry."""
    params = entry['params']
    diagram_type = params.get('type', 'normal_curve')

    renderer = _DISPATCH.get(diagram_type)
    if not renderer:
        raise ValueError(f"Unknown statistics diagram type: {diagram_type}")

    fig, ax = renderer(params)

    filename = entry['bucket_key'].split('/')[-1]
    path = Path(output_dir) / filename
    save_figure(fig, path)
    return path
