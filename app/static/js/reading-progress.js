document.addEventListener('DOMContentLoaded', function () {
    var bar = document.getElementById('readingProgressBar');
    if (!bar) return;

    function updateProgress() {
        var scrollTop = window.scrollY || document.documentElement.scrollTop;
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight <= 0) {
            bar.style.width = '100%';
            return;
        }
        var pct = Math.min((scrollTop / docHeight) * 100, 100);
        bar.style.width = pct + '%';
    }

    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
});
