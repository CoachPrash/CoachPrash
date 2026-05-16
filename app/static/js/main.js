// === KaTeX Auto-Render ===
document.addEventListener('DOMContentLoaded', function () {
    if (typeof renderMathInElement === 'function') {
        renderMathInElement(document.body, {
            delimiters: [
                {left: '\\(', right: '\\)', display: false},
                {left: '\\[', right: '\\]', display: true}
            ]
        });
    }
});

// === Sidebar ===
(function () {
    var STORAGE_KEY = 'coachprash_sidebar_collapsed';
    var body = document.body;

    // Restore saved state on desktop
    if (window.innerWidth > 768) {
        if (localStorage.getItem(STORAGE_KEY) === 'true') {
            body.classList.add('sidebar-collapsed');
        }
    }

    function isCollapsed() {
        return body.classList.contains('sidebar-collapsed') && window.innerWidth > 768;
    }

    function expandSidebar() {
        body.classList.remove('sidebar-collapsed');
        localStorage.setItem(STORAGE_KEY, 'false');
    }

    function collapseSidebar() {
        body.classList.add('sidebar-collapsed');
        localStorage.setItem(STORAGE_KEY, 'true');
    }

    // Desktop: toggle collapsed/expanded (only used by the collapse button)
    window.toggleSidebar = function () {
        if (isCollapsed()) {
            expandSidebar();
        } else {
            collapseSidebar();
        }
    };

    // Mobile: open/close overlay sidebar
    window.openSidebar = function () {
        body.classList.add('sidebar-open');
    };

    window.closeSidebar = function () {
        body.classList.remove('sidebar-open');
    };

    // Expand/collapse sidebar sections
    document.addEventListener('click', function (e) {
        // Ignore clicks on the collapse/expand toggle button itself
        if (e.target.closest('.sidebar-collapse-btn')) {
            return;
        }

        // Any click inside the collapsed sidebar (except the toggle) expands it
        if (isCollapsed() && e.target.closest('.sidebar')) {
            e.preventDefault();
            expandSidebar();
            return;
        }

        // Handle Subjects expand button
        var btn = e.target.closest('.sidebar-expand-btn');
        if (btn) {
            e.preventDefault();
            btn.parentElement.classList.toggle('open');
            return;
        }

        // Handle topic chevron clicks (expand topics, don't navigate)
        var chevron = e.target.closest('.expand-chevron-topic[data-subject-slug]');
        if (chevron) {
            e.preventDefault();
            e.stopPropagation();

            var li = chevron.closest('.sidebar-expandable');
            li.classList.toggle('open');

            // AJAX load topics on first expand
            var topicsList = li.querySelector('.sidebar-topics');
            if (topicsList && !topicsList.dataset.loaded) {
                var slug = chevron.dataset.subjectSlug;
                topicsList.innerHTML = '<li class="sidebar-topics-loading">Loading...</li>';
                fetch('/subjects/' + slug + '/topics-json')
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        topicsList.innerHTML = '';
                        data.topics.forEach(function (t) {
                            var item = document.createElement('li');
                            var a = document.createElement('a');
                            a.href = t.url;
                            a.title = t.name;
                            a.innerHTML = '<span class="sidebar-link-text">' + t.name + '</span>';
                            item.appendChild(a);
                            topicsList.appendChild(item);
                        });
                        topicsList.dataset.loaded = 'true';
                    })
                    .catch(function () {
                        topicsList.innerHTML = '<li class="sidebar-topics-loading">Failed to load</li>';
                    });
            }
            return;
        }

        // Close mobile sidebar on overlay click
        if (e.target.classList.contains('sidebar-overlay')) {
            closeSidebar();
        }
    });

    // ESC closes mobile sidebar
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && body.classList.contains('sidebar-open')) {
            closeSidebar();
        }
    });

    // Clean up mobile state on resize to desktop
    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            body.classList.remove('sidebar-open');
        }
    });
})();

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    var flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(function () { flash.remove(); }, 300);
        }, 5000);
    });
});

// KaTeX preview for admin content editors
function previewKaTeX(btn) {
    var textarea = btn.previousElementSibling;
    if (!textarea) {
        textarea = btn.parentElement.querySelector('textarea');
    }
    var pane = btn.nextElementSibling;
    if (!pane || !pane.classList.contains('preview-pane')) {
        pane = btn.parentElement.querySelector('.preview-pane');
    }
    if (!textarea || !pane) return;

    if (pane.style.display === 'none') {
        pane.style.display = 'block';
        pane.innerHTML = textarea.value;
        if (typeof renderMathInElement === 'function') {
            renderMathInElement(pane, {
                delimiters: [
                    { left: '\\(', right: '\\)', display: false },
                    { left: '\\[', right: '\\]', display: true },
                ],
            });
        }
        btn.textContent = 'Hide Preview';
    } else {
        pane.style.display = 'none';
        btn.textContent = 'Preview';
    }
}
