document.addEventListener('DOMContentLoaded', function () {
    var dataEl = document.getElementById('quiz-data');
    if (!dataEl) return;

    var problems = JSON.parse(dataEl.textContent);
    if (!problems.length) return;

    var csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    var metaEl = document.getElementById('quiz-meta');
    var quizMeta = metaEl ? JSON.parse(metaEl.textContent) : {};
    var currentIndex = 0;
    var score = 0;
    var answers = {};
    var hintsRevealed = {};
    var answered = false;
    var selectedAnswer = null;
    var startTime = Date.now();
    var problemStartTime = Date.now();
    var timerInterval = null;
    var signupPromptCount = 0;
    var codeEditorInstance = null;

    // Navigation state
    var visited = {};
    var draftAnswers = {};

    // Filter state
    var allProblems = problems;
    var activeFilter = 'all';
    var availableTypes = {};
    allProblems.forEach(function(p) { availableTypes[p.problem_type] = (availableTypes[p.problem_type] || 0) + 1; });

    // DOM refs
    var counter = document.getElementById('quizCounter');
    var timer = document.getElementById('quizTimer');
    var progressFill = document.getElementById('quizProgressFill');
    var problemDisplay = document.getElementById('problemDisplay');
    var choicesArea = document.getElementById('choicesArea');
    var actionsArea = document.getElementById('actionsArea');
    var submitBtn = document.getElementById('submitBtn');
    var saveBtn = document.getElementById('saveBtn');
    var hintBtn = document.getElementById('hintBtn');
    var solutionBtn = document.getElementById('solutionBtn');
    var feedbackArea = document.getElementById('feedbackArea');
    var hintsArea = document.getElementById('hintsArea');
    var solutionArea = document.getElementById('solutionArea');
    var nextBtn = document.getElementById('nextBtn');
    var quizContainer = document.getElementById('quizContainer');
    var quizResults = document.getElementById('quizResults');
    var signupPrompt = document.getElementById('signupPrompt');
    var filterBar = document.getElementById('quizFilterBar');
    var emptyFilter = document.getElementById('quizEmptyFilter');
    var quizBody = document.getElementById('quizBody');

    // Navigator DOM refs
    var navPrevBtn = document.getElementById('navPrevBtn');
    var navNextBtn = document.getElementById('navNextBtn');
    var navShapesContainer = document.getElementById('navShapesContainer');

    // Filter bar: show/hide buttons based on available types, hide bar if only 1 type
    if (filterBar) {
        var typeCount = Object.keys(availableTypes).length;
        if (typeCount <= 1) {
            filterBar.style.display = 'none';
        } else {
            filterBar.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
                var type = btn.getAttribute('data-filter');
                if (type !== 'all' && !availableTypes[type]) {
                    btn.style.display = 'none';
                } else if (type !== 'all') {
                    btn.style.display = '';
                }
            });
        }
    }

    // Timer
    timerInterval = setInterval(function () {
        var elapsed = Math.floor((Date.now() - startTime) / 1000);
        var mins = Math.floor(elapsed / 60);
        var secs = elapsed % 60;
        timer.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
    }, 1000);

    function renderKaTeX(el) {
        if (typeof renderMathInElement === 'function') {
            renderMathInElement(el, {
                delimiters: [
                    { left: '\\(', right: '\\)', display: false },
                    { left: '\\[', right: '\\]', display: true }
                ]
            });
        }
    }

    function textToLatex(text) {
        if (!text) return '';
        var s = text;
        s = s.replace(/sqrt\(([^)]*)\)/g, '\\sqrt{$1}');
        s = s.replace(/\b(ln|log|sin|cos|tan)\(/g, '\\$1(');
        s = s.replace(/\|([^|]+)\|/g, '\\left|$1\\right|');
        s = s.replace(/e\^\(([^)]*)\)/g, 'e^{$1}');
        s = s.replace(/e\^([a-zA-Z0-9])/g, 'e^{$1}');
        s = s.replace(/\^\(([^)]*)\)/g, '^{$1}');
        s = s.replace(/\^([a-zA-Z0-9])/g, '^{$1}');
        if (/^[^/]+\/[^/]+$/.test(s) && !/\\/.test(text)) {
            var parts = s.split('/');
            s = '\\frac{' + parts[0].trim() + '}{' + parts[1].trim() + '}';
        }
        s = s.replace(/\binfinity\b/g, '\\infty');
        s = s.replace(/\bpi\b/g, '\\pi');
        s = s.replace(/\*\\pi/g, '\\pi');
        return s;
    }

    function insertAtCursor(inputEl, text, cursorOffset) {
        var start = inputEl.selectionStart;
        var end = inputEl.selectionEnd;
        var val = inputEl.value;

        if (start !== end && cursorOffset < 0) {
            var wrapper = text;
            var insertPos = wrapper.length + cursorOffset;
            var before = wrapper.substring(0, insertPos);
            var after = wrapper.substring(insertPos);
            var selected = val.substring(start, end);
            inputEl.value = val.substring(0, start) + before + selected + after + val.substring(end);
            inputEl.selectionStart = start + before.length;
            inputEl.selectionEnd = start + before.length + selected.length;
        } else {
            inputEl.value = val.substring(0, start) + text + val.substring(end);
            var newPos = start + text.length + cursorOffset;
            inputEl.selectionStart = newPos;
            inputEl.selectionEnd = newPos;
        }

        inputEl.dispatchEvent(new Event('input'));
        inputEl.focus();
    }

    function updateMathPreview(inputEl, previewDiv) {
        var val = inputEl.value.trim();
        if (!val) {
            previewDiv.innerHTML = '';
            return;
        }
        if (typeof katex === 'undefined') return;
        var latex = textToLatex(val);
        try {
            katex.render(latex, previewDiv, { throwOnError: false });
        } catch (e) {
            previewDiv.textContent = val;
        }
    }

    function createMathToolbar(inputEl, container) {
        var buttons = [
            { label: '\u221A', text: 'sqrt()', offset: -1, aria: 'Square root' },
            { label: '\u03C0', text: 'pi', offset: 0, aria: 'Pi' },
            { label: '\u221E', text: 'infinity', offset: 0, aria: 'Infinity' },
            { label: 'x\u207F', text: '^', offset: 0, aria: 'Exponent' },
            { label: 'a/b', text: '/', offset: 0, aria: 'Fraction' },
            { label: '|x|', text: '||', offset: -1, aria: 'Absolute value' },
            { label: 'ln', text: 'ln()', offset: -1, aria: 'Natural log' },
            { label: 'e\u02E3', text: 'e^', offset: 0, aria: 'Exponential' },
            { label: 'sin', text: 'sin()', offset: -1, aria: 'Sine' },
            { label: 'cos', text: 'cos()', offset: -1, aria: 'Cosine' },
            { label: 'tan', text: 'tan()', offset: -1, aria: 'Tangent' }
        ];

        var toolbar = document.createElement('div');
        toolbar.className = 'math-toolbar';

        buttons.forEach(function (b) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'math-btn';
            btn.textContent = b.label;
            btn.setAttribute('aria-label', b.aria);
            btn.addEventListener('mousedown', function (e) {
                e.preventDefault();
            });
            btn.addEventListener('click', function () {
                insertAtCursor(inputEl, b.text, b.offset);
                updateMathPreview(inputEl, preview);
            });
            toolbar.appendChild(btn);
        });

        var preview = document.createElement('div');
        preview.className = 'math-preview';

        container.insertBefore(toolbar, inputEl);
        inputEl.parentNode.insertBefore(preview, inputEl.nextSibling);

        inputEl.addEventListener('input', function () {
            updateMathPreview(inputEl, preview);
        });
    }

    // ── Navigator functions ──

    function getShapeSVG(type, index) {
        var num = index + 1;
        if (type === 'mcq') {
            // Circle
            return '<svg width="28" height="28" viewBox="0 0 28 28">'
                + '<circle cx="14" cy="14" r="12" class="nav-shape"/>'
                + '<text x="14" y="14" class="nav-num" text-anchor="middle" dy="0.35em">' + num + '</text>'
                + '</svg>';
        } else if (type === 'ftb') {
            // Triangle
            return '<svg width="28" height="28" viewBox="0 0 28 28">'
                + '<polygon points="14,2 26,26 2,26" class="nav-shape"/>'
                + '<text x="14" y="19" class="nav-num" text-anchor="middle" dy="0.35em">' + num + '</text>'
                + '</svg>';
        } else {
            // Square for FRQ and code
            return '<svg width="28" height="28" viewBox="0 0 28 28">'
                + '<rect x="2" y="2" width="24" height="24" rx="3" class="nav-shape"/>'
                + '<text x="14" y="14" class="nav-num" text-anchor="middle" dy="0.35em">' + num + '</text>'
                + '</svg>';
        }
    }

    function buildNavigator() {
        if (!navShapesContainer) return;
        navShapesContainer.innerHTML = '';
        problems.forEach(function(p, i) {
            var item = document.createElement('button');
            item.className = 'quiz-nav-item';
            item.setAttribute('data-index', i);
            item.setAttribute('aria-label', 'Problem ' + (i + 1) + ' (' + p.problem_type.toUpperCase() + ')');
            item.innerHTML = getShapeSVG(p.problem_type, i);
            item.addEventListener('click', function() {
                navigateTo(i);
            });
            navShapesContainer.appendChild(item);
        });
        updateNavigator();
    }

    function updateNavigator() {
        var items = document.querySelectorAll('.quiz-nav-item');
        var answeredCount = 0;
        items.forEach(function(item, i) {
            var p = problems[i];
            item.classList.remove('nav-current', 'nav-correct', 'nav-incorrect', 'nav-skipped');
            if (i === currentIndex) {
                item.classList.add('nav-current');
            }
            if (p.id in answers) {
                answeredCount++;
                if (answers[p.id] === true) {
                    item.classList.add('nav-correct');
                } else if (answers[p.id] === false) {
                    item.classList.add('nav-incorrect');
                }
                // answers[p.id] === null means FRQ pending self-grade — treat as skipped
                if (answers[p.id] === null) {
                    item.classList.add('nav-skipped');
                }
            } else if (visited[p.id] && i !== currentIndex) {
                item.classList.add('nav-skipped');
            }
        });

        // Update prev/next arrows
        if (navPrevBtn) navPrevBtn.disabled = (currentIndex <= 0);
        if (navNextBtn) navNextBtn.disabled = (currentIndex >= problems.length - 1);

        // Scroll active item into view on mobile
        var activeItem = document.querySelector('.quiz-nav-item.nav-current');
        if (activeItem) activeItem.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' });

        // Update progress bar — completion-based
        var completionPct = problems.length > 0 ? (answeredCount / problems.length * 100) : 0;
        progressFill.style.width = completionPct + '%';
    }

    function saveDraftForCurrent() {
        var currentP = problems[currentIndex];
        if (!currentP) return;
        if (currentP.id in answers) return; // already submitted, no draft needed

        if (currentP.problem_type === 'code' && codeEditorInstance && window._getEditorCode) {
            var code = window._getEditorCode(codeEditorInstance);
            if (code && code.trim()) {
                draftAnswers[currentP.id] = code;
            }
        } else if (selectedAnswer !== null) {
            draftAnswers[currentP.id] = selectedAnswer;
        }
    }

    function navigateTo(index) {
        if (index < 0 || index >= problems.length || index === currentIndex) return;

        // Save draft for current problem if unanswered
        saveDraftForCurrent();

        // Mark current as visited if not already answered
        var currentP = problems[currentIndex];
        if (currentP && !(currentP.id in answers)) {
            visited[currentP.id] = true;
        }

        currentIndex = index;
        showProblem(index);
        updateNavigator();
    }

    function showProblem(index) {
        var p = problems[index];
        selectedAnswer = null;
        problemStartTime = Date.now();

        // Clean up previous code editor
        if (codeEditorInstance) {
            codeEditorInstance.destroy();
            codeEditorInstance = null;
        }

        // Check if this problem was already answered
        var wasAnswered = (p.id in answers);
        answered = wasAnswered;

        // Mark as visited
        visited[p.id] = true;

        counter.textContent = 'Problem ' + (index + 1) + ' of ' + problems.length;

        problemDisplay.innerHTML = '<div class="problem-question">' + p.question_html + '</div>';
        if (p.difficulty) {
            problemDisplay.innerHTML += '<span class="difficulty-badge difficulty-' + p.difficulty + '">' + p.difficulty + '</span>';
        }

        choicesArea.innerHTML = '';
        feedbackArea.style.display = 'none';
        feedbackArea.className = 'quiz-feedback';
        hintsArea.innerHTML = '';
        solutionArea.innerHTML = '';
        nextBtn.style.display = 'none';
        nextBtn.textContent = 'Next Problem';
        nextBtn.onclick = nextProblem;
        submitBtn.disabled = true;
        submitBtn.style.display = '';
        submitBtn.textContent = 'Submit Answer';
        saveBtn.style.display = 'none';
        hintBtn.style.display = p.hint_count > 0 ? '' : 'none';
        hintBtn.textContent = 'Show Hint';
        solutionBtn.style.display = 'none';
        solutionBtn.disabled = false;
        solutionBtn.textContent = 'Show Solution';

        if (p.problem_type === 'mcq' && p.choices) {
            p.choices.forEach(function (c) {
                var btn = document.createElement('button');
                btn.className = 'choice-btn';
                btn.setAttribute('data-id', c.id);
                btn.innerHTML = c.text;
                btn.addEventListener('click', function () {
                    if (answered) return;
                    document.querySelectorAll('.choice-btn').forEach(function (b) {
                        b.classList.remove('selected');
                    });
                    btn.classList.add('selected');
                    selectedAnswer = c.id;
                    submitBtn.disabled = false;
                    saveBtn.style.display = '';
                });
                choicesArea.appendChild(btn);
            });
        } else if (p.problem_type === 'code') {
            submitBtn.style.display = 'none';

            var editorWrapper = document.createElement('div');
            editorWrapper.className = 'code-editor-wrapper';
            editorWrapper.id = 'codeEditorContainer';
            choicesArea.appendChild(editorWrapper);

            var actionsDiv = document.createElement('div');
            actionsDiv.className = 'code-actions';
            actionsDiv.innerHTML = '<button class="btn-run-code" id="runCodeBtn">'
                + '<span class="run-icon">&#9654;</span> Run Code'
                + '<span class="run-shortcut">(Ctrl+Enter)</span>'
                + '</button>'
                + '<div class="code-spinner" id="codeSpinner"></div>';
            choicesArea.appendChild(actionsDiv);

            var outputPanel = document.createElement('div');
            outputPanel.className = 'code-output-panel';
            outputPanel.id = 'codeOutputPanel';
            outputPanel.innerHTML = '<div class="code-output-header"></div>'
                + '<div class="code-output-body"></div>';
            choicesArea.appendChild(outputPanel);

            function mountEditor() {
                if (codeEditorInstance) {
                    codeEditorInstance.destroy();
                }
                var initialCode = p.starter_code || '';
                // Restore draft code if available
                if (!wasAnswered && draftAnswers[p.id] !== undefined) {
                    initialCode = draftAnswers[p.id];
                }
                codeEditorInstance = window._initCodeEditor(
                    editorWrapper,
                    initialCode,
                    { onRunCode: function () { runCode(p); } }
                );
            }
            if (window._initCodeEditor) {
                mountEditor();
            } else {
                var cmPoll = setInterval(function() {
                    if (window._initCodeEditor) {
                        clearInterval(cmPoll);
                        if (document.contains(editorWrapper)) {
                            mountEditor();
                        }
                    }
                }, 100);
            }

            var runBtn = document.getElementById('runCodeBtn');
            runBtn.addEventListener('click', function () { runCode(p); });

        } else if (p.problem_type === 'frq') {
            var textarea = document.createElement('textarea');
            textarea.className = 'frq-textarea';
            textarea.placeholder = 'Write your answer here...';
            textarea.rows = 6;
            textarea.addEventListener('input', function () {
                selectedAnswer = textarea.value.trim();
                submitBtn.disabled = !selectedAnswer;
                if (selectedAnswer) saveBtn.style.display = '';
            });
            choicesArea.appendChild(textarea);
            submitBtn.textContent = 'Submit Response';
        } else {
            var input = document.createElement('input');
            input.type = 'text';
            input.className = 'fill-blank-input';
            input.placeholder = 'Type your answer...';
            input.addEventListener('input', function () {
                selectedAnswer = input.value.trim();
                submitBtn.disabled = !selectedAnswer;
                if (selectedAnswer) saveBtn.style.display = '';
            });
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && selectedAnswer && !answered) {
                    submitAnswer();
                }
            });
            choicesArea.appendChild(input);
            createMathToolbar(input, choicesArea);
        }

        // Restore state for already-answered problems
        if (wasAnswered) {
            submitBtn.style.display = 'none';
            saveBtn.style.display = 'none';

            if (answers[p.id] === true) {
                feedbackArea.innerHTML = '<strong>Correct!</strong>';
                feedbackArea.className = 'quiz-feedback feedback-correct';
            } else if (answers[p.id] === false) {
                feedbackArea.innerHTML = '<strong>Incorrect.</strong>';
                feedbackArea.className = 'quiz-feedback feedback-incorrect';
            } else if (answers[p.id] === null) {
                feedbackArea.innerHTML = '<strong>Response submitted.</strong> (Pending self-grade)';
                feedbackArea.className = 'quiz-feedback feedback-frq';
            }
            feedbackArea.style.display = 'block';

            // Show next/results button
            if (currentIndex < problems.length - 1) {
                nextBtn.style.display = '';
            } else {
                nextBtn.textContent = 'View Results';
                nextBtn.style.display = '';
                nextBtn.onclick = function() { showResults(); };
            }

            // Disable inputs
            choicesArea.querySelectorAll('.choice-btn').forEach(function(b) { b.style.pointerEvents = 'none'; });
            var fi = choicesArea.querySelector('.fill-blank-input');
            if (fi) fi.disabled = true;
            var mt = choicesArea.querySelector('.math-toolbar');
            if (mt) { mt.style.pointerEvents = 'none'; mt.style.opacity = '0.5'; }
            var ft = choicesArea.querySelector('.frq-textarea');
            if (ft) ft.disabled = true;

            if (p.has_solution) solutionBtn.style.display = '';
        }

        // Restore draft for unanswered problems
        if (!wasAnswered && draftAnswers[p.id] !== undefined) {
            selectedAnswer = draftAnswers[p.id];
            if (p.problem_type === 'mcq') {
                var draftBtn = choicesArea.querySelector('.choice-btn[data-id="' + selectedAnswer + '"]');
                if (draftBtn) { draftBtn.classList.add('selected'); submitBtn.disabled = false; }
            } else if (p.problem_type === 'frq') {
                var ta = choicesArea.querySelector('.frq-textarea');
                if (ta) { ta.value = selectedAnswer; submitBtn.disabled = !selectedAnswer; }
            } else if (p.problem_type === 'ftb') {
                var inp = choicesArea.querySelector('.fill-blank-input');
                if (inp) { inp.value = selectedAnswer; submitBtn.disabled = !selectedAnswer; }
            }
            // Code drafts handled in mountEditor above
            if (selectedAnswer) saveBtn.style.display = '';
        }

        renderKaTeX(problemDisplay);
        renderKaTeX(choicesArea);
        updateNavigator();
    }

    function submitAnswer() {
        if (answered || !selectedAnswer) return;
        answered = true;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span>Checking...';
        saveBtn.style.display = 'none';

        var p = problems[currentIndex];
        var timeSpent = Math.floor((Date.now() - problemStartTime) / 1000);
        var hintsUsed = hintsRevealed[p.id] || 0;

        fetch('/api/practice/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                problem_id: p.id,
                submitted_answer: String(selectedAnswer),
                time_spent_seconds: timeSpent,
                hints_used: hintsUsed
            })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            answers[p.id] = data.correct;
            delete draftAnswers[p.id];

            if (data.correct === null) {
                // FRQ: show model answer then ask student to self-grade
                feedbackArea.innerHTML = '<strong>Response submitted.</strong>';
                feedbackArea.className = 'quiz-feedback feedback-frq';
                if (data.model_answer) {
                    feedbackArea.innerHTML += '<div class="frq-model-answer"><strong>Model Answer:</strong><div class="frq-model-answer-content">' + data.model_answer + '</div></div>';
                }
                feedbackArea.innerHTML += '<div class="frq-self-grade"><p>Compare your answer to the model answer. Did you get it right?</p>'
                    + '<button class="btn btn-sm btn-success frq-grade-btn" data-grade="yes">Yes, I got it right</button> '
                    + '<button class="btn btn-sm btn-danger frq-grade-btn" data-grade="no">No, I got it wrong</button></div>';

                nextBtn.style.display = 'none';

                feedbackArea.querySelectorAll('.frq-grade-btn').forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        var gotIt = btn.getAttribute('data-grade') === 'yes';
                        if (gotIt) {
                            score++;
                            answers[p.id] = true;
                        } else {
                            answers[p.id] = false;
                        }
                        var gradeDiv = feedbackArea.querySelector('.frq-self-grade');
                        if (gotIt) {
                            gradeDiv.innerHTML = '<p class="frq-grade-result frq-grade-correct">Marked as correct!</p>';
                            showConfetti();
                        } else {
                            gradeDiv.innerHTML = '<p class="frq-grade-result frq-grade-incorrect">Marked as incorrect. Review the model answer above.</p>';
                        }
                        if (currentIndex < problems.length - 1) {
                            nextBtn.style.display = '';
                        } else {
                            nextBtn.textContent = 'View Results';
                            nextBtn.style.display = '';
                            nextBtn.onclick = function() { showResults(); };
                        }
                        updateNavigator();
                    });
                });
            } else if (data.correct) {
                score++;
                feedbackArea.innerHTML = '<strong>Correct!</strong>';
                feedbackArea.className = 'quiz-feedback feedback-correct';
                showConfetti();

                if (p.problem_type === 'mcq') {
                    var sel = choicesArea.querySelector('.choice-btn.selected');
                    if (sel) sel.classList.add('correct');
                }
            } else {
                feedbackArea.innerHTML = '<strong>Incorrect.</strong> The correct answer is: <span class="correct-answer">' + (data.correct_answer || '') + '</span>';
                feedbackArea.className = 'quiz-feedback feedback-incorrect';

                if (p.problem_type === 'mcq') {
                    var sel = choicesArea.querySelector('.choice-btn.selected');
                    if (sel) sel.classList.add('incorrect');
                }
            }

            feedbackArea.style.display = 'block';
            submitBtn.style.display = 'none';

            if (data.correct !== null) {
                if (currentIndex < problems.length - 1) {
                    nextBtn.style.display = '';
                } else {
                    nextBtn.textContent = 'View Results';
                    nextBtn.style.display = '';
                    nextBtn.onclick = function() { showResults(); };
                }
            }

            if (p.has_solution) {
                solutionBtn.style.display = '';
            }

            choicesArea.querySelectorAll('.choice-btn').forEach(function (b) {
                b.style.pointerEvents = 'none';
            });
            var fillInput = choicesArea.querySelector('.fill-blank-input');
            if (fillInput) fillInput.disabled = true;
            var mathToolbar = choicesArea.querySelector('.math-toolbar');
            if (mathToolbar) { mathToolbar.style.pointerEvents = 'none'; mathToolbar.style.opacity = '0.5'; }
            var frqTextarea = choicesArea.querySelector('.frq-textarea');
            if (frqTextarea) frqTextarea.disabled = true;

            renderKaTeX(feedbackArea);
            updateNavigator();

            signupPromptCount++;
            if (signupPrompt && signupPromptCount % 3 === 0) {
                signupPrompt.style.display = 'block';
            }
        })
        .catch(function (err) {
            feedbackArea.innerHTML = 'Error checking answer. Please try again.';
            feedbackArea.className = 'quiz-feedback feedback-incorrect';
            feedbackArea.style.display = 'block';
            answered = false;
            submitBtn.disabled = false;
        });
    }

    function applyFilter(type) {
        // Save draft for current problem before switching
        saveDraftForCurrent();
        var currentP = problems[currentIndex];
        if (currentP && !(currentP.id in answers)) {
            visited[currentP.id] = true;
        }

        activeFilter = type;

        // Update active button styling
        document.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
            btn.classList.toggle('active', btn.getAttribute('data-filter') === type);
        });

        // Find the first unanswered problem of this type, or first of this type
        var targetIdx = -1;
        if (type === 'all') {
            // Jump to first unanswered overall
            for (var i = 0; i < problems.length; i++) {
                if (!(problems[i].id in answers)) { targetIdx = i; break; }
            }
            if (targetIdx === -1) targetIdx = 0;
        } else {
            // Jump to first unanswered of this type
            for (var i = 0; i < problems.length; i++) {
                if (problems[i].problem_type === type && !(problems[i].id in answers)) {
                    targetIdx = i;
                    break;
                }
            }
            // If all of this type are answered, jump to first of this type
            if (targetIdx === -1) {
                for (var i = 0; i < problems.length; i++) {
                    if (problems[i].problem_type === type) { targetIdx = i; break; }
                }
            }
            // If none of this type exist, show empty message
            if (targetIdx === -1) {
                if (quizBody) quizBody.style.display = 'none';
                if (emptyFilter) emptyFilter.style.display = 'block';
                return;
            }
        }

        if (quizBody) quizBody.style.display = '';
        if (emptyFilter) emptyFilter.style.display = 'none';

        currentIndex = targetIdx;
        showProblem(currentIndex);
        updateNavigator();
    }

    function nextProblem() {
        if (currentIndex >= problems.length - 1) {
            showResults();
        } else {
            navigateTo(currentIndex + 1);
        }
    }

    function showResults() {
        clearInterval(timerInterval);
        quizContainer.style.display = 'none';
        quizResults.style.display = 'block';

        var elapsed = Math.floor((Date.now() - startTime) / 1000);
        var mins = Math.floor(elapsed / 60);
        var secs = elapsed % 60;

        // Calculate total score across ALL problems (not just filtered view)
        var totalScore = 0;
        allProblems.forEach(function(p) { if (answers[p.id] === true) totalScore++; });

        document.getElementById('resultsScore').textContent = totalScore;
        document.getElementById('resultsTotal').textContent = allProblems.length;
        document.getElementById('resultsAccuracy').textContent = Math.round(totalScore / allProblems.length * 100) + '%';
        document.getElementById('resultsTime').textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;

        progressFill.style.width = '100%';

        if (quizMeta.concept_id) {
            fetch('/api/practice/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    concept_id: quizMeta.concept_id,
                    score: score,
                    total: allProblems.length
                })
            }).catch(function () {});
        }
    }

    function requestHint() {
        var p = problems[currentIndex];
        var hintIndex = hintsRevealed[p.id] || 0;
        hintBtn.disabled = true;
        hintBtn.innerHTML = '<span class="spinner"></span>Loading...';

        fetch('/api/practice/hint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                problem_id: p.id,
                hint_index: hintIndex
            })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            hintBtn.disabled = false;
            if (data.blocked) {
                var div = document.createElement('div');
                div.className = 'hint-box hint-blocked';
                div.innerHTML = '<span class="lock-icon">&#128274;</span> Additional hints available with Premium';
                hintsArea.appendChild(div);
                hintBtn.style.display = 'none';
                return;
            }

            hintsRevealed[p.id] = hintIndex + 1;

            var div = document.createElement('div');
            div.className = 'hint-box hint-reveal';
            div.innerHTML = '<strong>Hint ' + (hintIndex + 1) + ':</strong> ' + data.hint_text;
            hintsArea.appendChild(div);
            renderKaTeX(div);

            if (data.has_more && data.next_accessible) {
                hintBtn.textContent = 'Next Hint';
            } else if (data.has_more && !data.next_accessible) {
                hintBtn.textContent = 'Next Hint (Premium)';
            } else {
                hintBtn.style.display = 'none';
            }
        })
        .catch(function () {
            hintBtn.disabled = false;
            hintBtn.textContent = 'Get Hint';
        });
    }

    function requestSolution() {
        var p = problems[currentIndex];
        solutionBtn.disabled = true;
        solutionBtn.innerHTML = '<span class="spinner"></span>Loading...';

        fetch('/api/practice/solution', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ problem_id: p.id })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.blocked) {
                solutionArea.innerHTML = '<div class="solution-blocked"><span class="lock-icon">&#128274;</span> Step-by-step solution available with Premium</div>';
                solutionBtn.style.display = 'none';
                return;
            }

            var html = '<div class="solution-accordion">';
            if (data.steps && data.steps.length) {
                data.steps.forEach(function (step, i) {
                    var stepText = typeof step === 'string' ? step : (step.text_html || step.text || '');
                    var stepNum = typeof step === 'object' && step.step_number ? step.step_number : (i + 1);
                    html += '<div class="solution-step open">';
                    html += '<button class="solution-step-toggle">';
                    html += 'Step ' + stepNum;
                    html += '</button>';
                    html += '<div class="solution-step-content">' + stepText + '</div>';
                    html += '</div>';
                });
            }
            html += '</div>';
            solutionArea.innerHTML = html;
            solutionArea.querySelectorAll('.solution-step-toggle').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    this.parentElement.classList.toggle('open');
                });
            });
            solutionBtn.style.display = 'none';
            renderKaTeX(solutionArea);
        })
        .catch(function () {
            solutionBtn.disabled = false;
            solutionBtn.textContent = 'View Solution';
        });
    }

    function showConfetti() {
        var container = document.getElementById('confetti-container');
        if (!container) return;
        var colors = ['#1B365D', '#C41E3A', '#F4A100', '#2D8659', '#6B48FF'];
        for (var i = 0; i < 40; i++) {
            var piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = Math.random() * 100 + '%';
            piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            piece.style.animationDelay = Math.random() * 0.5 + 's';
            piece.style.animationDuration = (1 + Math.random()) + 's';
            container.appendChild(piece);
        }
        setTimeout(function () {
            container.innerHTML = '';
        }, 2500);
    }

    function saveDraft() {
        var p = problems[currentIndex];
        if (!p || answered || (p.id in answers)) return;

        saveDraftForCurrent();
        visited[p.id] = true;

        // Brief "Saved!" feedback on button
        saveBtn.textContent = 'Saved!';
        saveBtn.disabled = true;
        setTimeout(function() {
            saveBtn.textContent = 'Save';
            saveBtn.disabled = false;
        }, 1000);

        updateNavigator();
    }

    function runCode(problem) {
        if (!codeEditorInstance || !window._getEditorCode) return;
        var code = window._getEditorCode(codeEditorInstance);
        if (!code.trim()) return;

        var runBtn = document.getElementById('runCodeBtn');
        var spinner = document.getElementById('codeSpinner');
        var panel = document.getElementById('codeOutputPanel');

        runBtn.disabled = true;
        spinner.classList.add('active');
        panel.className = 'code-output-panel';

        fetch('/api/practice/run-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                problem_id: problem.id,
                code: code
            })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            runBtn.disabled = false;
            spinner.classList.remove('active');

            var header = panel.querySelector('.code-output-header');
            var body = panel.querySelector('.code-output-body');

            if (data.compile_error) {
                panel.className = 'code-output-panel visible compile-error';
                header.textContent = 'Compilation Error';
                body.textContent = data.error;
            } else if (data.runtime_error) {
                panel.className = 'code-output-panel visible runtime-error';
                header.textContent = 'Runtime Error';
                body.textContent = data.error;
            } else if (data.test_results) {
                var passed = data.test_results.passed;
                var total = data.test_results.total;
                var allPass = passed === total;

                panel.className = 'code-output-panel visible ' + (allPass ? 'success' : 'fail');
                header.textContent = passed + ' of ' + total + ' tests passed';

                var tableHtml = '<table class="test-results-table"><thead><tr><th></th><th>Test</th><th>Details</th></tr></thead><tbody>';
                data.test_results.results.forEach(function (r) {
                    var rowClass = 'test-' + r.status;
                    var icon = r.status === 'pass' ? '&#10003;' : (r.status === 'error' ? '&#9888;' : '&#10007;');
                    var iconClass = r.status;
                    var detail = '';
                    if (r.status === 'fail') {
                        detail = 'Expected: ' + (r.expected || '') + ', Got: ' + (r.actual || '');
                    } else if (r.status === 'error') {
                        detail = r.error || 'Exception thrown';
                    }
                    tableHtml += '<tr class="' + rowClass + '"><td><span class="test-status-icon ' + iconClass + '">' + icon + '</span></td><td>' + (r.description || 'Test ' + r.case_num) + '</td><td>' + detail + '</td></tr>';
                });
                tableHtml += '</tbody></table>';
                body.innerHTML = tableHtml;

                if (allPass) {
                    answered = true;
                    score++;
                    answers[problem.id] = true;
                    delete draftAnswers[problem.id];
                    showConfetti();
                    feedbackArea.innerHTML = '<strong>All tests passed!</strong>';
                    feedbackArea.className = 'quiz-feedback feedback-correct';
                    feedbackArea.style.display = 'block';
                    saveBtn.style.display = 'none';
                    if (currentIndex < problems.length - 1) {
                        nextBtn.style.display = '';
                    } else {
                        nextBtn.textContent = 'View Results';
                        nextBtn.style.display = '';
                        nextBtn.onclick = function() { showResults(); };
                    }
                    if (problem.has_solution) solutionBtn.style.display = '';
                    updateNavigator();
                }
            } else {
                if (data.passed) {
                    panel.className = 'code-output-panel visible success';
                    header.textContent = 'Output Correct!';
                    body.textContent = data.actual || data.output;

                    answered = true;
                    score++;
                    answers[problem.id] = true;
                    delete draftAnswers[problem.id];
                    showConfetti();
                    feedbackArea.innerHTML = '<strong>Correct!</strong>';
                    feedbackArea.className = 'quiz-feedback feedback-correct';
                    feedbackArea.style.display = 'block';
                    saveBtn.style.display = 'none';
                    if (currentIndex < problems.length - 1) {
                        nextBtn.style.display = '';
                    } else {
                        nextBtn.textContent = 'View Results';
                        nextBtn.style.display = '';
                        nextBtn.onclick = function() { showResults(); };
                    }
                    if (problem.has_solution) solutionBtn.style.display = '';
                    updateNavigator();
                } else {
                    panel.className = 'code-output-panel visible fail';
                    header.textContent = 'Output Incorrect';
                    if (data.details && data.details.length) {
                        body.innerHTML = '<pre>' + data.details.map(function(d) { return d.replace(/</g, '&lt;'); }).join('\n') + '</pre>';
                    } else {
                        var exp = (data.expected || '').replace(/</g, '&lt;');
                        var act = (data.actual || '').replace(/</g, '&lt;');
                        body.innerHTML = '<pre><strong>Expected:</strong>\n' + exp + '\n\n<strong>Your output:</strong>\n' + act + '</pre>';
                    }
                }
            }
        })
        .catch(function (err) {
            runBtn.disabled = false;
            spinner.classList.remove('active');
            panel.className = 'code-output-panel visible compile-error';
            panel.querySelector('.code-output-header').textContent = 'Error';
            panel.querySelector('.code-output-body').textContent = 'Failed to run code. Please try again.';
        });
    }

    // Event listeners
    submitBtn.addEventListener('click', submitAnswer);
    nextBtn.addEventListener('click', nextProblem);
    hintBtn.addEventListener('click', requestHint);
    solutionBtn.addEventListener('click', requestSolution);
    saveBtn.addEventListener('click', saveDraft);

    // Navigator arrow buttons
    if (navPrevBtn) {
        navPrevBtn.addEventListener('click', function() {
            navigateTo(currentIndex - 1);
        });
    }
    if (navNextBtn) {
        navNextBtn.addEventListener('click', function() {
            navigateTo(currentIndex + 1);
        });
    }

    var retryBtn = document.getElementById('retryBtn');
    if (retryBtn) {
        retryBtn.addEventListener('click', function () {
            activeFilter = 'all';
            problems = allProblems;
            document.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
                btn.classList.toggle('active', btn.getAttribute('data-filter') === 'all');
            });
            currentIndex = 0;
            score = 0;
            answers = {};
            hintsRevealed = {};
            visited = {};
            draftAnswers = {};
            startTime = Date.now();
            signupPromptCount = 0;
            quizResults.style.display = 'none';
            quizContainer.style.display = '';
            if (quizBody) quizBody.style.display = '';
            if (emptyFilter) emptyFilter.style.display = 'none';
            timerInterval = setInterval(function () {
                var elapsed = Math.floor((Date.now() - startTime) / 1000);
                var mins = Math.floor(elapsed / 60);
                var secs = elapsed % 60;
                timer.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
            }, 1000);
            showProblem(0);
            buildNavigator();
        });
    }

    // Filter button click handlers
    document.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var type = btn.getAttribute('data-filter');
            if (type === activeFilter) return;
            quizResults.style.display = 'none';
            quizContainer.style.display = '';
            applyFilter(type);
        });
    });

    // Start
    showProblem(0);
    buildNavigator();
});
