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

    function showProblem(index) {
        var p = problems[index];
        answered = false;
        selectedAnswer = null;
        problemStartTime = Date.now();

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
        hintBtn.style.display = p.hint_count > 0 ? '' : 'none';
        hintBtn.textContent = 'Show Hint';
        solutionBtn.style.display = 'none';

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
        }

        renderKaTeX(problemDisplay);
        renderKaTeX(choicesArea);
    }

    function submitAnswer() {
        if (answered || !selectedAnswer) return;
        answered = true;
        submitBtn.disabled = true;

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

            if (data.correct) {
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
                    // Highlight correct choice
                    choicesArea.querySelectorAll('.choice-btn').forEach(function (btn) {
                        // We don't know which is correct from client data, rely on visual feedback
                    });
                }
            }

            feedbackArea.style.display = 'block';
            submitBtn.style.display = 'none';
            nextBtn.style.display = '';

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
                    total: problems.length
                })
            }).catch(function () {});
        }
    }

    function requestHint() {
        var p = problems[currentIndex];
        var hintIndex = hintsRevealed[p.id] || 0;

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
            // Silently fail
        });
    }

    function requestSolution() {
        var p = problems[currentIndex];

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
                    html += '<div class="solution-step">';
                    html += '<button class="solution-step-toggle" onclick="this.parentElement.classList.toggle(\'open\')">';
                    html += 'Step ' + stepNum;
                    html += '</button>';
                    html += '<div class="solution-step-content">' + stepText + '</div>';
                    html += '</div>';
                });
            }
            html += '</div>';
            solutionArea.innerHTML = html;
            solutionBtn.style.display = 'none';
            renderKaTeX(solutionArea);
        })
        .catch(function () {
            // Silently fail
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

    // Event listeners
    submitBtn.addEventListener('click', submitAnswer);
    nextBtn.addEventListener('click', nextProblem);
    hintBtn.addEventListener('click', requestHint);
    solutionBtn.addEventListener('click', requestSolution);

    var retryBtn = document.getElementById('retryBtn');
    if (retryBtn) {
        retryBtn.addEventListener('click', function () {
            currentIndex = 0;
            score = 0;
            answers = {};
            hintsRevealed = {};
            startTime = Date.now();
            signupPromptCount = 0;
            quizResults.style.display = 'none';
            quizContainer.style.display = '';
            timerInterval = setInterval(function () {
                var elapsed = Math.floor((Date.now() - startTime) / 1000);
                var mins = Math.floor(elapsed / 60);
                var secs = elapsed % 60;
                timer.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
            }, 1000);
            showProblem(0);
        });
    }

    // Start
    showProblem(0);
});
