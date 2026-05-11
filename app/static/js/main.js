function toggleNav() {
    document.querySelector('.nav-links').classList.toggle('show');
}

function toggleUserMenu(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('userDropdown').classList.toggle('show');
}

document.addEventListener('click', function (e) {
    var dropdown = document.getElementById('userDropdown');
    if (dropdown && !e.target.closest('.nav-user-menu')) {
        dropdown.classList.remove('show');
    }
});

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
