document.addEventListener('DOMContentLoaded', function () {
    var bar = document.getElementById('readingProgressBar');
    if (!bar) return;

    // On desktop the scroll container is .main-wrapper; on mobile it's the window
    var wrapper = document.getElementById('mainWrapper');

    function getScrollContainer() {
        if (window.innerWidth > 768 && wrapper) return wrapper;
        return null; // use window
    }

    function updateProgress() {
        var container = getScrollContainer();
        var scrollTop, docHeight;
        if (container) {
            scrollTop = container.scrollTop;
            docHeight = container.scrollHeight - container.clientHeight;
        } else {
            scrollTop = window.scrollY || document.documentElement.scrollTop;
            docHeight = document.documentElement.scrollHeight - window.innerHeight;
        }
        if (docHeight <= 0) {
            bar.style.width = '100%';
            return;
        }
        var pct = Math.min((scrollTop / docHeight) * 100, 100);
        bar.style.width = pct + '%';
    }

    if (wrapper) {
        wrapper.addEventListener('scroll', updateProgress, { passive: true });
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
});
