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
    var codeEditorInstance = null;  // CodeMirror editor for 'code' problems

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
        // sqrt(X) → \sqrt{X}
        s = s.replace(/sqrt\(([^)]*)\)/g, '\\sqrt{$1}');
        // trig / log functions
        s = s.replace(/\b(ln|log|sin|cos|tan)\(/g, '\\$1(');
        // |X| → \left|X\right|
        s = s.replace(/\|([^|]+)\|/g, '\\left|$1\\right|');
        // e^(X) → e^{X}
        s = s.replace(/e\^\(([^)]*)\)/g, 'e^{$1}');
        // e^X (single token) → e^{X}
        s = s.replace(/e\^([a-zA-Z0-9])/g, 'e^{$1}');
        // ^(X) → ^{X}
        s = s.replace(/\^\(([^)]*)\)/g, '^{$1}');
        // ^X (single token) → ^{X}
        s = s.replace(/\^([a-zA-Z0-9])/g, '^{$1}');
        // Full-string simple fraction A/B → \frac{A}{B}
        if (/^[^/]+\/[^/]+$/.test(s) && !/\\/.test(text)) {
            var parts = s.split('/');
            s = '\\frac{' + parts[0].trim() + '}{' + parts[1].trim() + '}';
        }
        // pi → \pi, infinity → \infty
        s = s.replace(/\binfinity\b/g, '\\infty');
        s = s.replace(/\bpi\b/g, '\\pi');
        // N*\pi → N\pi (cleaner)
        s = s.replace(/\*\\pi/g, '\\pi');
        return s;
    }

    function insertAtCursor(inputEl, text, cursorOffset) {
        var start = inputEl.selectionStart;
        var end = inputEl.selectionEnd;
        var val = inputEl.value;

        if (start !== end && cursorOffset < 0) {
            // Wrap selection: e.g. sqrt() wraps to sqrt(selection)
            var wrapper = text;
            var insertPos = wrapper.length + cursorOffset; // position of closing char
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
            { label: '√', text: 'sqrt()', offset: -1, aria: 'Square root' },
            { label: 'π', text: 'pi', offset: 0, aria: 'Pi' },
            { label: '∞', text: 'infinity', offset: 0, aria: 'Infinity' },
            { label: 'xⁿ', text: '^', offset: 0, aria: 'Exponent' },
            { label: 'a/b', text: '/', offset: 0, aria: 'Fraction' },
            { label: '|x|', text: '||', offset: -1, aria: 'Absolute value' },
            { label: 'ln', text: 'ln()', offset: -1, aria: 'Natural log' },
            { label: 'eˣ', text: 'e^', offset: 0, aria: 'Exponential' },
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
                e.preventDefault(); // prevent input blur on mobile
            });
            btn.addEventListener('click', function () {
                insertAtCursor(inputEl, b.text, b.offset);
                updateMathPreview(inputEl, preview);
            });
            toolbar.appendChild(btn);
        });

        var preview = document.createElement('div');
        preview.className = 'math-preview';

        // Insert toolbar before input, preview after input
        container.insertBefore(toolbar, inputEl);
        inputEl.parentNode.insertBefore(preview, inputEl.nextSibling);

        // Live preview on typing
        inputEl.addEventListener('input', function () {
            updateMathPreview(inputEl, preview);
        });
    }

    function showProblem(index) {
        var p = problems[index];
        answered = false;
        selectedAnswer = null;
        problemStartTime = Date.now();

        // Clean up previous code editor
        if (codeEditorInstance) {
            codeEditorInstance.destroy();
            codeEditorInstance = null;
        }

        counter.textContent = 'Problem ' + (index + 1) + ' of ' + problems.length;
        progressFill.style.width = (index / problems.length * 100) + '%';

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
        submitBtn.disabled = true;
        submitBtn.style.display = '';
        submitBtn.textContent = 'Submit Answer';
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
                });
                choicesArea.appendChild(btn);
            });
        } else if (p.problem_type === 'code') {
            // YouCode: render CodeMirror editor + Run Code button
            submitBtn.style.display = 'none';  // hide standard submit

            // Editor container
            var editorWrapper = document.createElement('div');
            editorWrapper.className = 'code-editor-wrapper';
            editorWrapper.id = 'codeEditorContainer';
            choicesArea.appendChild(editorWrapper);

            // Actions: Run Code button + spinner
            var actionsDiv = document.createElement('div');
            actionsDiv.className = 'code-actions';
            actionsDiv.innerHTML = '<button class="btn-run-code" id="runCodeBtn">'
                + '<span class="run-icon">&#9654;</span> Run Code'
                + '<span class="run-shortcut">(Ctrl+Enter)</span>'
                + '</button>'
                + '<div class="code-spinner" id="codeSpinner"></div>';
            choicesArea.appendChild(actionsDiv);

            // Output panel
            var outputPanel = document.createElement('div');
            outputPanel.className = 'code-output-panel';
            outputPanel.id = 'codeOutputPanel';
            outputPanel.innerHTML = '<div class="code-output-header"></div>'
                + '<div class="code-output-body"></div>';
            choicesArea.appendChild(outputPanel);

            // Initialize CodeMirror (loaded as ES module — may not be ready yet)
            function mountEditor() {
                if (codeEditorInstance) {
                    codeEditorInstance.destroy();
                }
                codeEditorInstance = window._initCodeEditor(
                    editorWrapper,
                    p.starter_code || '',
                    { onRunCode: function () { runCode(p); } }
                );
            }
            if (window._initCodeEditor) {
                mountEditor();
            } else {
                // ES module not loaded yet — poll until ready
                var cmPoll = setInterval(function() {
                    if (window._initCodeEditor) {
                        clearInterval(cmPoll);
                        // Only mount if this editor wrapper is still in the DOM
                        if (document.contains(editorWrapper)) {
                            mountEditor();
                        }
                    }
                }, 100);
            }

            // Run Code button click
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
            });
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && selectedAnswer && !answered) {
                    submitAnswer();
                }
            });
            choicesArea.appendChild(input);
            createMathToolbar(input, choicesArea);
        }

        renderKaTeX(problemDisplay);
        renderKaTeX(choicesArea);
    }

    function submitAnswer() {
        if (answered || !selectedAnswer) return;
        answered = true;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span>Checking...';

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

                // Hide Next button until student self-grades
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
                        // Replace self-grade buttons with result
                        var gradeDiv = feedbackArea.querySelector('.frq-self-grade');
                        if (gotIt) {
                            gradeDiv.innerHTML = '<p class="frq-grade-result frq-grade-correct">Marked as correct!</p>';
                            showConfetti();
                        } else {
                            gradeDiv.innerHTML = '<p class="frq-grade-result frq-grade-incorrect">Marked as incorrect. Review the model answer above.</p>';
                        }
                        nextBtn.style.display = '';
                    });
                });
            } else if (data.correct) {
                score++;
                feedbackArea.innerHTML = '<strong>Correct!</strong>';
                feedbackArea.className = 'quiz-feedback feedback-correct';
                showConfetti();

                // Highlight correct choice
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
            // For FRQ, Next button is shown after self-grading (handled above)
            if (data.correct !== null) {
                nextBtn.style.display = '';
            }

            // Show solution button after answering
            if (p.has_solution) {
                solutionBtn.style.display = '';
            }

            // Disable choice buttons
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

            // Signup prompt for unauthenticated users
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
        activeFilter = type;
        if (type === 'all') {
            problems = allProblems;
        } else {
            problems = allProblems.filter(function(p) { return p.problem_type === type; });
        }

        // Reset quiz state
        currentIndex = 0;
        score = 0;
        answers = {};
        hintsRevealed = {};
        startTime = Date.now();
        signupPromptCount = 0;

        // Update active button styling
        document.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
            btn.classList.toggle('active', btn.getAttribute('data-filter') === type);
        });

        // Handle empty result
        if (problems.length === 0) {
            if (quizBody) quizBody.style.display = 'none';
            if (emptyFilter) emptyFilter.style.display = 'block';
            counter.textContent = 'Problem 0 of 0';
            progressFill.style.width = '0%';
            return;
        }

        if (quizBody) quizBody.style.display = '';
        if (emptyFilter) emptyFilter.style.display = 'none';

        // Restart timer
        clearInterval(timerInterval);
        timerInterval = setInterval(function () {
            var elapsed = Math.floor((Date.now() - startTime) / 1000);
            var mins = Math.floor(elapsed / 60);
            var secs = elapsed % 60;
            timer.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
        }, 1000);

        showProblem(0);
    }

    function nextProblem() {
        currentIndex++;
        if (currentIndex >= problems.length) {
            showResults();
        } else {
            showProblem(currentIndex);
        }
    }

    function showResults() {
        clearInterval(timerInterval);
        quizContainer.style.display = 'none';
        quizResults.style.display = 'block';

        var elapsed = Math.floor((Date.now() - startTime) / 1000);
        var mins = Math.floor(elapsed / 60);
        var secs = elapsed % 60;

        document.getElementById('resultsScore').textContent = score;
        document.getElementById('resultsTotal').textContent = problems.length;
        document.getElementById('resultsAccuracy').textContent = Math.round(score / problems.length * 100) + '%';
        document.getElementById('resultsTime').textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;

        progressFill.style.width = '100%';

        // Report quiz completion to update StudentProgress
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

    function runCode(problem) {
        if (!codeEditorInstance || !window._getEditorCode) return;
        var code = window._getEditorCode(codeEditorInstance);
        if (!code.trim()) return;

        var runBtn = document.getElementById('runCodeBtn');
        var spinner = document.getElementById('codeSpinner');
        var panel = document.getElementById('codeOutputPanel');

        runBtn.disabled = true;
        spinner.classList.add('active');
        panel.className = 'code-output-panel';  // reset

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
                // Method test results (Tier 2)
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
                    // Auto-grade as correct
                    answered = true;
                    score++;
                    answers[problem.id] = true;
                    showConfetti();
                    feedbackArea.innerHTML = '<strong>All tests passed!</strong>';
                    feedbackArea.className = 'quiz-feedback feedback-correct';
                    feedbackArea.style.display = 'block';
                    nextBtn.style.display = '';
                    if (problem.has_solution) solutionBtn.style.display = '';
                }
            } else {
                // Output match (Tier 1)
                if (data.passed) {
                    panel.className = 'code-output-panel visible success';
                    header.textContent = 'Output Correct!';
                    body.textContent = data.actual || data.output;

                    answered = true;
                    score++;
                    answers[problem.id] = true;
                    showConfetti();
                    feedbackArea.innerHTML = '<strong>Correct!</strong>';
                    feedbackArea.className = 'quiz-feedback feedback-correct';
                    feedbackArea.style.display = 'block';
                    nextBtn.style.display = '';
                    if (problem.has_solution) solutionBtn.style.display = '';
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

    var retryBtn = document.getElementById('retryBtn');
    if (retryBtn) {
        retryBtn.addEventListener('click', function () {
            // Reset to ALL filter on retry
            activeFilter = 'all';
            problems = allProblems;
            document.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
                btn.classList.toggle('active', btn.getAttribute('data-filter') === 'all');
            });
            currentIndex = 0;
            score = 0;
            answers = {};
            hintsRevealed = {};
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
        });
    }

    // Filter button click handlers
    document.querySelectorAll('.quiz-filter-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var type = btn.getAttribute('data-filter');
            if (type === activeFilter) return;
            // If results are showing, switch back to quiz view
            quizResults.style.display = 'none';
            quizContainer.style.display = '';
            applyFilter(type);
        });
    });

    // Start
    showProblem(0);
});
