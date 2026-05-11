# CoachPrash.com — Build Prompts for Claude

This document contains 3 self-contained prompts to build CoachPrash.com incrementally. Each phase produces a deployable, testable increment. Paste each prompt into Claude Pro (or Claude Code) and execute them in order.

**Architecture:** Flask + PostgreSQL + KaTeX + Vanilla JS, deployed on Railway.

---

## PHASE 1 — Foundation (Core Site + Auth + Admin)

Paste this entire prompt into Claude:

---

```
You are building CoachPrash.com from scratch — a STEM tutoring and self-study website for a coach who teaches elementary through college students. This is Phase 1 of 3. Your job is to produce a fully deployable Flask application with the complete project structure, database schema, authentication, admin panel, all static pages, and Railway deployment configuration.

=== TECH STACK (non-negotiable) ===
- Python 3.11+ / Flask
- PostgreSQL (Railway-provisioned)
- SQLAlchemy ORM + Flask-Migrate (Alembic)
- Flask-Login for session management
- Flask-WTF for forms
- KaTeX (client-side via CDN) for LaTeX math rendering
- Blueprint-based architecture
- Gunicorn for production serving
- Environment variables for all secrets/config (never hardcode)

=== PROJECT STRUCTURE ===
Create this exact directory layout:

coachprash/
├── app/
│   ├── __init__.py              # App factory (create_app)
│   ├── config.py                # Config classes (Dev, Prod, Test)
│   ├── extensions.py            # db, migrate, login_manager, csrf
│   ├── models/
│   │   ├── __init__.py          # Import all models
│   │   ├── user.py              # Student, Admin user models
│   │   ├── content.py           # Subject, Topic, Concept, Lesson
│   │   ├── practice.py          # ProblemSet, Problem, Choice, Hint, Solution
│   │   ├── progress.py          # StudentProgress, AttemptLog, MasteryScore
│   │   └── access.py            # AccessCode, Subscription tier
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── main/                # Home, About, Contact, Testimonials
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── forms.py
│   │   ├── subjects/            # Subject catalog, topic browsing
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── auth/                # Login, register, access codes
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── forms.py
│   │   ├── study/               # (Phase 2) Concept viewer, practice engine
│   │   │   ├── __init__.py
│   │   │   └── routes.py        # Placeholder: return "Coming in Phase 2"
│   │   ├── blog/                # Blog/Resources listing
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   └── admin_panel/         # Admin dashboard
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── forms.py
│   ├── templates/
│   │   ├── base.html            # Master layout: nav, footer, KaTeX CDN
│   │   ├── main/
│   │   │   ├── home.html
│   │   │   ├── about.html
│   │   │   ├── contact.html
│   │   │   └── testimonials.html
│   │   ├── subjects/
│   │   │   ├── catalog.html     # All subjects grid
│   │   │   └── topic_list.html  # Topics within a subject
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── study/
│   │   │   └── coming_soon.html
│   │   ├── blog/
│   │   │   ├── list.html
│   │   │   └── post.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── manage_students.html
│   │       ├── manage_content.html
│   │       ├── manage_codes.html
│   │       ├── manage_blog.html
│   │       ├── manage_testimonials.html
│   │       └── manage_messages.html
│   └── static/
│       ├── css/
│       │   └── style.css        # Custom styles (Bold & Academic theme)
│       ├── js/
│       │   └── main.js
│       └── images/
│           └── placeholder/     # Placeholder images
├── migrations/                  # Flask-Migrate (auto-generated)
├── wsgi.py                      # Gunicorn entry point
├── requirements.txt
├── Procfile                     # Railway deployment
├── railway.toml                 # Railway config
├── .env.example                 # Template for env vars
├── .gitignore
└── seed.py                      # DB seed script for demo data

=== DATABASE SCHEMA ===

Design these models with SQLAlchemy. Use UUIDs for primary keys. Add created_at/updated_at timestamps on every table. Design for future adaptive practice and scheduling even though those features come later.

1. User
   - id (UUID, PK)
   - email (unique, indexed)
   - username (unique)
   - password_hash
   - role ENUM('student', 'admin')
   - is_active (boolean, default True)
   - tier ENUM('free', 'premium') default 'free'
   - created_at, updated_at

2. AccessCode
   - id (UUID, PK)
   - code (string, unique, indexed) — 8-char alphanumeric
   - tier ENUM('free', 'premium')
   - max_uses (int, nullable — null = unlimited)
   - current_uses (int, default 0)
   - expires_at (datetime, nullable)
   - created_by (FK -> User admin)
   - is_active (boolean)
   - created_at, updated_at

3. Subject
   - id (UUID, PK)
   - name (e.g., "Mathematics", "Physics", "Chemistry", "Computer Science", "Test Prep")
   - slug (unique)
   - description (text)
   - icon (string — CSS class or emoji placeholder)
   - display_order (int)
   - is_active (boolean)
   - created_at, updated_at

4. Topic
   - id (UUID, PK)
   - subject_id (FK -> Subject)
   - name (e.g., "Algebra 1", "AP Physics C Mechanics")
   - slug (unique within subject)
   - description (text)
   - difficulty_level ENUM('elementary', 'middle_school', 'high_school', 'ap', 'college')
   - display_order (int)
   - is_active (boolean)
   - created_at, updated_at

5. Concept (a lesson/explainer within a topic, designed for microlearning)
   - id (UUID, PK)
   - topic_id (FK -> Topic)
   - title (e.g., "Solving Linear Equations")
   - slug
   - content_html (text — rendered from Markdown+LaTeX)
   - content_raw (text — source Markdown+LaTeX for editing)
   - estimated_minutes (int, 3-7 range target)
   - access_tier ENUM('free', 'premium')
   - display_order (int)
   - is_active (boolean)
   - created_at, updated_at

6. ProblemSet
   - id (UUID, PK)
   - concept_id (FK -> Concept)
   - title
   - access_tier ENUM('free', 'premium')
   - display_order (int)
   - is_active (boolean)
   - created_at, updated_at

7. Problem
   - id (UUID, PK)
   - problem_set_id (FK -> ProblemSet)
   - question_html (text — supports LaTeX)
   - question_raw (text)
   - problem_type ENUM('mcq', 'fill_in_blank')
   - correct_answer (string — for fill-in-blank; for MCQ, marked on Choice)
   - points (int, default 1)
   - difficulty ENUM('easy', 'medium', 'hard') — for future adaptive practice
   - display_order (int)
   - created_at, updated_at

8. Choice (for MCQ problems)
   - id (UUID, PK)
   - problem_id (FK -> Problem)
   - choice_text (string — supports LaTeX)
   - is_correct (boolean)
   - display_order (int)

9. Hint
   - id (UUID, PK)
   - problem_id (FK -> Problem)
   - hint_text (text — supports LaTeX)
   - display_order (int) — hints revealed progressively
   - cost_points (int, default 0) — future: deduct points for using hints

10. StepByStepSolution
    - id (UUID, PK)
    - problem_id (FK -> Problem, unique — one solution per problem)
    - steps_json (JSON — array of {step_number, text_html, text_raw})
    - access_tier ENUM('free', 'premium') — solutions can be gated

11. StudentProgress (for tracking per-concept mastery)
    - id (UUID, PK)
    - student_id (FK -> User)
    - concept_id (FK -> Concept)
    - status ENUM('not_started', 'in_progress', 'completed')
    - mastery_score (float, 0.0-1.0, nullable) — for future adaptive engine
    - last_accessed (datetime)
    - created_at, updated_at
    - UNIQUE(student_id, concept_id)

12. AttemptLog (individual problem attempts — for analytics and adaptive practice)
    - id (UUID, PK)
    - student_id (FK -> User)
    - problem_id (FK -> Problem)
    - submitted_answer (string)
    - is_correct (boolean)
    - hints_used (int, default 0)
    - time_spent_seconds (int, nullable)
    - attempted_at (datetime)

13. Testimonial
    - id (UUID, PK)
    - student_name (string)
    - student_grade (string, nullable — e.g., "11th Grade")
    - content (text)
    - rating (int, 1-5)
    - is_featured (boolean, default False)
    - is_active (boolean, default True)
    - created_at

14. BlogPost
    - id (UUID, PK)
    - author_id (FK -> User admin)
    - title
    - slug (unique)
    - content_html (text)
    - content_raw (text)
    - excerpt (string)
    - is_published (boolean, default False)
    - published_at (datetime, nullable)
    - created_at, updated_at

15. ContactMessage
    - id (UUID, PK)
    - name (string)
    - email (string)
    - subject (string)
    - message (text)
    - is_read (boolean, default False)
    - created_at

FUTURE TABLES (do NOT create yet, but design the schema above to accommodate):
- ScheduledSession (calendar/booking)
- StripeCustomer (payment integration)
- AdaptivePath (learning path engine)

=== VISUAL DESIGN: BOLD & ACADEMIC THEME ===

Implement this design system in CSS (no CSS framework — custom CSS for full control):

Color palette:
- Primary: #1B365D (deep navy — trust, academia)
- Secondary: #C41E3A (crimson — energy, action)
- Accent: #F4A100 (gold — achievement, premium)
- Background: #FAFAFA
- Card background: #FFFFFF
- Text primary: #1A1A2E
- Text secondary: #4A4A6A
- Success: #2D8659
- Border: #E2E8F0

Typography:
- Headings: 'Playfair Display' (Google Fonts) — serif, academic feel
- Body: 'Inter' (Google Fonts) — clean, modern readability
- Code/Math: 'JetBrains Mono' (Google Fonts)

Layout principles:
- Max content width: 1200px, centered
- Card-based design with subtle shadows (box-shadow: 0 2px 8px rgba(0,0,0,0.08))
- Generous whitespace (padding: 2rem sections)
- Mobile-first responsive (breakpoints: 480px, 768px, 1024px)
- Sticky navigation bar with logo text "CoachPrash" in Playfair Display
- Hamburger menu on mobile

Navigation:
- Desktop: horizontal bar — Home | Subjects | About | Resources | Testimonials | Contact | [Login]
- When logged in as student: add "My Progress" link, change Login to user dropdown
- When logged in as admin: add "Admin" link

=== PAGE CONTENT (use professional placeholder copy) ===

HOME PAGE:
- Hero section: large heading "Master STEM with Confidence", subheading "Personalized coaching and self-study tools for students from elementary through college", CTA button "Explore Subjects" (links to /subjects) and secondary CTA "Start Practicing Free" (links to /register)
- "What We Teach" section: 5 subject cards (Math, Physics, Chemistry, CS, Test Prep) each with icon placeholder, brief description, and "View Topics" link
- "Why CoachPrash" section: 3-column grid with icons — "Expert Instruction" / "Interactive Practice" / "Proven Results"
- Testimonials carousel (3 placeholder testimonials)
- CTA banner: "Ready to Excel? Start your free practice today."

ABOUT PAGE:
- Coach bio section (placeholder photo area, placeholder bio text about STEM tutoring expertise)
- Teaching philosophy section
- Credentials/experience section (placeholder)
- "Subjects & Levels" summary

SUBJECTS PAGE (/subjects):
- Grid of all subject areas, each as a card with subject name, icon, brief description, and number of topics available
- Clicking a subject goes to /subjects/<slug> showing all topics within it
- Each topic card shows: name, difficulty badge, number of concepts, "Free" or "Premium" badge
- Clicking a topic goes to the topic detail page (Phase 2 builds this out; for now show a "Content coming soon" page with the topic title and description)

CONTACT PAGE:
- Contact form (name, email, subject dropdown, message) — saves to ContactMessage table
- Display a success flash message on submission
- Sidebar with: email placeholder, phone placeholder, "Based in [City, State]" placeholder

TESTIMONIALS PAGE:
- Grid of testimonial cards showing student name, grade, rating (stars), and testimonial text
- Seed with 5 placeholder testimonials

BLOG/RESOURCES PAGE (/resources):
- List of blog posts (card layout with title, excerpt, date, "Read More" link)
- Individual post page at /resources/<slug>
- Seed with 2 placeholder posts: "5 Tips for Acing AP Calculus" and "How to Study Effectively for the SAT"

=== AUTHENTICATION SYSTEM ===

Registration flow:
1. Student goes to /register
2. Enters: username, email, password, confirm password, access code (optional)
3. If no access code provided -> free tier account
4. If valid premium access code -> premium tier account
5. Access code usage count increments; if max_uses reached, code becomes invalid
6. After registration -> redirect to home with flash "Welcome! Your account has been created."

Login flow:
1. /login with email + password
2. Flask-Login session management
3. "Remember me" checkbox
4. After login -> redirect to home

Access code validation:
- Check: code exists, is_active, not expired, current_uses < max_uses (or max_uses is null)
- On successful use: increment current_uses

Password requirements:
- Minimum 8 characters
- Hashed with Werkzeug's generate_password_hash

=== ADMIN PANEL ===

Build a custom admin panel (NOT Flask-Admin) at /admin/* protected by @admin_required decorator.

Admin Dashboard (/admin/):
- Stats cards: total students, total premium students, total concepts published, total problems
- Recent registrations (last 10)
- Recent contact messages (last 5, unread highlighted)

Manage Students (/admin/students):
- Table: username, email, tier, registration date, last login
- Actions: change tier, deactivate account
- Search by email/username

Manage Content (/admin/content):
- Hierarchical view: Subject -> Topic -> Concept -> ProblemSet -> Problem
- CRUD forms for each level (create, edit, delete with confirmation)
- Content editor: textarea for raw Markdown+LaTeX with a preview pane that renders KaTeX
- For Problems: form to add choices (MCQ), set correct answer, add hints (ordered), add step-by-step solution (as ordered steps)

Manage Access Codes (/admin/codes):
- Table: code, tier, max uses, current uses, expires_at, status
- Generate new code (auto-generate 8-char alphanumeric or manual entry)
- Deactivate code

Manage Blog (/admin/blog):
- List all posts with title, status (draft/published), date
- Create/edit post with Markdown+LaTeX editor and preview
- Publish/unpublish toggle

Manage Testimonials (/admin/testimonials):
- List, create, edit, delete, toggle featured

View Contact Messages (/admin/messages):
- List with read/unread status
- Click to view full message, mark as read

=== RAILWAY DEPLOYMENT ===

Procfile:
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2

railway.toml:
[build]
builder = "nixpacks"

[deploy]
startCommand = "flask db upgrade && gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2"
healthcheckPath = "/health"
healthcheckTimeout = 100

.env.example (document every required env var):
SECRET_KEY=change-me-to-a-random-string
DATABASE_URL=postgresql://...
FLASK_ENV=production
ADMIN_EMAIL=admin@coachprash.com
ADMIN_PASSWORD=change-me

.gitignore:
- .env, __pycache__, *.pyc, instance/, .DS_Store, venv/

wsgi.py:
- Import create_app, call it, assign to `app`
- Add a /health endpoint that returns 200 OK with JSON {"status": "healthy"}

Create a seed.py script that:
1. Creates an admin user (email/password from env vars)
2. Populates all Subject and Topic records from this complete list:

   MATHEMATICS:
   - Arithmetic (elementary)
   - Algebra 1 (middle_school)
   - Geometry (high_school)
   - Algebra 2 (high_school)
   - Precalculus (high_school)
   - Calculus — Honors (high_school)
   - AP Calculus AB (ap)
   - AP Calculus BC (ap)
   - Statistics — Honors (high_school)
   - AP Statistics (ap)
   - Discrete Mathematics (college)
   - Multivariable Calculus (college)
   - Linear Algebra (college)

   PHYSICS:
   - Honors Physics (high_school)
   - AP Physics 1: Mechanics (ap)
   - AP Physics 2: E&M (ap)
   - AP Physics C: Mechanics (ap)
   - AP Physics C: E&M (ap)

   CHEMISTRY:
   - Honors Chemistry (high_school)
   - Advanced Chemistry (high_school)

   COMPUTER SCIENCE:
   - AP Computer Science Principles (ap)
   - AP Computer Science A — Java (ap)
   - Algorithms and Data Structures (college)

   TEST PREP:
   - SAT Mathematics (high_school)
   - ACT Mathematics (high_school)
   - ACT Science (high_school)

3. Creates 5 placeholder testimonials with realistic copy
4. Creates 2 placeholder blog posts
5. Generates 3 sample access codes (1 free unlimited, 1 premium with 10 uses, 1 expired for testing)
6. Register as a Flask CLI command: `flask seed`
7. Make it idempotent — safe to re-run without duplicating data

=== REQUIREMENTS.TXT ===
Flask==3.1.*
Flask-SQLAlchemy==3.1.*
Flask-Migrate==4.1.*
Flask-Login==0.6.*
Flask-WTF==1.2.*
psycopg2-binary==2.9.*
gunicorn==23.*
python-dotenv==1.0.*
email-validator==2.*
Werkzeug==3.1.*

=== WHAT TO DELIVER ===
Produce every file listed in the project structure above with complete, working code. Every template should be fully styled. Every route should be functional. The site should be deployable to Railway with just:
1. Create a new Railway project
2. Provision a PostgreSQL database
3. Set environment variables (SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD — DATABASE_URL is auto-set by Railway)
4. Deploy from GitHub repo
5. Run `flask seed` via Railway CLI

Do NOT leave any TODOs or placeholder comments in the code. The only "coming soon" should be the study/practice pages (Phase 2). Everything else must be complete and functional.
```

---

## PHASE 2 — Self-Study Engine (Interactive Practice + Progress Tracking)

Paste this entire prompt into Claude after Phase 1 is complete and deployed:

---

```
You are continuing to build CoachPrash.com. Phase 1 is complete — the Flask app has the full project structure, database schema, authentication with access codes, custom admin panel, all public pages (Home, About, Subjects, Contact, Testimonials, Blog/Resources), and is deployed on Railway with PostgreSQL. This is Phase 2: building the Self-Study Engine.

Refer to the existing project structure from Phase 1. You are modifying and adding to the existing codebase. Do NOT recreate files that already exist unless you need to modify them. For files you modify, show the complete updated file.

=== WHAT PHASE 2 BUILDS ===
The interactive self-study system: concept explainers with KaTeX rendering, practice quizzes (MCQ + fill-in-blank), instant grading with AJAX, progressive hints, step-by-step solutions, progress tracking dashboard, and freemium content gating.

=== EXISTING ARCHITECTURE (from Phase 1) ===
- Blueprint-based Flask app with app factory pattern
- Models: User, AccessCode, Subject, Topic, Concept, ProblemSet, Problem, Choice, Hint, StepByStepSolution, StudentProgress, AttemptLog, Testimonial, BlogPost, ContactMessage
- Auth: Flask-Login with access code registration, free/premium tiers
- Admin panel at /admin/* with full CRUD for all content
- KaTeX loaded via CDN in base.html
- PostgreSQL on Railway
- Bold & Academic theme with navy (#1B365D), crimson (#C41E3A), gold (#F4A100)

=== STUDY BLUEPRINT (app/blueprints/study/) ===

Replace the placeholder study blueprint with the full self-study engine.

URL structure:
- /subjects/<subject_slug>/<topic_slug>/                         -> Topic overview (list of concepts)
- /subjects/<subject_slug>/<topic_slug>/<concept_slug>/          -> Concept explainer page
- /subjects/<subject_slug>/<topic_slug>/<concept_slug>/practice/ -> Practice quiz for this concept
- /api/practice/check     -> AJAX endpoint for answer checking
- /api/practice/hint      -> AJAX endpoint for revealing next hint
- /api/practice/solution  -> AJAX endpoint for revealing solution
- /progress/              -> Student progress dashboard (login required)

=== CONCEPT EXPLAINER PAGE ===

Layout:
- Breadcrumb navigation: Subjects > Math > Algebra 1 > Solving Linear Equations
- Left sidebar (desktop) / top accordion (mobile): table of contents for all concepts in this topic, with current concept highlighted, and completion checkmarks for logged-in students
- Main content area: rendered concept HTML with KaTeX math rendering
- At the bottom: "Practice This Concept" CTA button linking to the practice page
- Navigation: Previous Concept / Next Concept arrows
- If concept is premium and user is free tier: show first 2 paragraphs with a blur overlay on the rest + "Upgrade to Premium to continue reading" CTA

Content rendering:
- content_html is stored pre-rendered but KaTeX rendering happens client-side via auto-render extension
- Wrap math in \( \) for inline and \[ \] for display math
- Support embedded diagrams via placeholder <div class="diagram-placeholder" data-description="..."> elements (future: replace with actual diagrams)

Microlearning display:
- Show estimated reading time badge at the top: "~5 min read"
- Progress bar at the top of the page that fills as user scrolls (visual engagement)

=== PRACTICE QUIZ ENGINE ===

Build an interactive, single-page quiz experience using vanilla JavaScript (no React/Vue — keep it simple with fetch() calls to Flask API endpoints).

Quiz page layout:
- Breadcrumb navigation
- Problem counter: "Problem 3 of 10"
- Progress bar showing completion
- Problem display area (renders LaTeX via KaTeX)
- For MCQ: radio button choices (A, B, C, D) styled as clickable cards
- For fill-in-blank: text input field with a "Submit Answer" button
- Below the problem: "Get a Hint" button and "Show Solution" button (initially hidden until after first attempt)
- Feedback area: shows correct/incorrect with explanation after submission
- "Next Problem" button appears after answering

Answer checking behavior (via AJAX — no page reloads):
1. Student selects/types answer and clicks Submit
2. POST to /api/practice/check with {problem_id, submitted_answer}
3. Server validates answer:
   - MCQ: compare selected choice_id against Choice where is_correct=True
   - Fill-in-blank: case-insensitive string comparison with correct_answer (strip whitespace). Support multiple acceptable answers separated by "||" in the correct_answer field (e.g., "2x+3||2x + 3||2*x+3")
4. Response: {is_correct: bool, correct_answer: str, explanation: str|null}
5. If correct: green highlight, confetti animation (CSS-only, subtle), auto-advance after 1.5s
6. If incorrect: red highlight, show correct answer, keep "Get a Hint" and "Show Solution" buttons visible
7. Log attempt to AttemptLog table (if user is logged in)

Hint system (via AJAX):
1. "Get a Hint" button shows hint #1
2. Button changes to "Next Hint" if more hints exist
3. Each hint revealed increments hints_used on the current attempt
4. Hints render LaTeX via KaTeX
5. POST to /api/practice/hint with {problem_id, hint_number}
6. Response: {hint_text: str, has_more_hints: bool}

Step-by-step solution (via AJAX):
1. "Show Solution" button (available after submitting an answer, or directly for premium users)
2. For free users: show solution only after attempting the problem
3. For premium users: solution available immediately
4. If solution is gated to premium tier and user is free: show "Upgrade to Premium" message
5. POST to /api/practice/solution with {problem_id}
6. Response: {steps: [{step_number, text_html}], access_allowed: bool}
7. Display steps in an expandable accordion, one step at a time, with "Show Next Step" button

Quiz completion:
- After all problems in the set: show results summary
  - Score: "You got 7 out of 10 correct (70%)"
  - Time spent (tracked via JS timer)
  - Per-problem breakdown: correct/incorrect, hints used
  - "Retry Incorrect Problems" button (filters to only missed problems)
  - "Next Concept" button
- If logged in: update StudentProgress for this concept
  - Set status to 'completed' if score >= 70%
  - Set mastery_score to (correct / total)
  - Save last_accessed

=== FREEMIUM GATING LOGIC ===

Implement these access rules as a decorator and/or utility function. Enforce server-side (not just UI hiding).

Free tier gets:
- All concept explainers marked as access_tier='free'
- First 3 problems of any problem set (regardless of set tier)
- No step-by-step solutions (shown as "Premium feature" teaser)
- No progress tracking (shown as "Sign up for Premium to track progress" teaser)
- Hint #1 only (subsequent hints gated)

Premium tier gets:
- All concept explainers
- All problems in all problem sets
- All step-by-step solutions
- Full progress tracking and mastery scores
- All hints

Not logged in:
- Same as free tier but also no attempt logging
- Gentle "Create a free account" prompts after every 3rd problem

Gating UI (never show a blank wall — always show what they're missing):
- Premium-gated concept: show first ~200 words, then blur overlay with lock icon and "Unlock with Premium" CTA
- Premium-gated problems: show "3 more problems available with Premium" card after the free problems
- Premium-gated solutions: show "Step-by-step solution available with Premium" with a lock icon
- Premium-gated hints: show "Additional hints available with Premium" after hint #1

=== PROGRESS DASHBOARD (/progress/) ===

Login required. Show the student's learning journey.

Layout:
- Header: "Your Learning Progress" with student name
- Overall stats cards:
  - Total concepts completed
  - Total problems attempted
  - Overall accuracy percentage
  - Current streak (consecutive days with at least 1 problem attempted)
- Subject-by-subject breakdown:
  - Accordion for each subject the student has interacted with
  - Inside: list of topics with progress bars (% concepts completed)
  - Inside each topic: list of concepts with status badge (not started / in progress / completed) and mastery score
- Recent activity feed: last 10 problem attempts with timestamp, problem title, and correct/incorrect

=== JAVASCRIPT FILES (app/static/js/) ===

Create these JS files:

practice.js:
- Quiz engine logic (fetch-based AJAX, no page reloads)
- Answer submission and feedback display
- Hint reveal system
- Solution step-through
- Timer tracking
- Progress bar updates
- Confetti animation on correct answer (CSS keyframes, not a library)
- KaTeX re-rendering after dynamic content insertion (call renderMathInElement after DOM updates)

reading-progress.js:
- Scroll-based reading progress bar for concept explainer pages
- Auto-mark concept as "in progress" when user scrolls past 50% (if logged in, via AJAX)

=== NEW/UPDATED TEMPLATES ===

Create these templates:

templates/study/
├── topic_overview.html      # List of concepts in a topic with progress indicators
├── concept_detail.html      # Concept explainer with sidebar TOC
├── practice.html            # Quiz interface (single-page app)
└── premium_teaser.html      # Partial: premium upgrade CTA block

templates/progress/
└── dashboard.html           # Student progress dashboard

=== ADMIN PANEL UPDATES ===

Update the admin content management to support the new study features:

Content editor improvements:
- Add a "Preview" button next to every content textarea that renders KaTeX in a modal
- When creating/editing a Problem, show a live preview of how the problem will look to students
- When creating a ProblemSet, allow manual display_order editing

- Add a "Bulk Import" page at /admin/content/import that accepts JSON in this format:
  {
    "subject_slug": "mathematics",
    "topic_slug": "algebra-1",
    "concepts": [
      {
        "title": "...",
        "content_raw": "...",
        "estimated_minutes": 5,
        "access_tier": "free",
        "problem_sets": [
          {
            "title": "...",
            "access_tier": "free",
            "problems": [
              {
                "question_raw": "...",
                "problem_type": "mcq",
                "difficulty": "easy",
                "choices": [
                  {"text": "...", "is_correct": false},
                  {"text": "...", "is_correct": true}
                ],
                "hints": ["First hint", "Second hint"],
                "solution_steps": ["Step 1...", "Step 2..."]
              }
            ]
          }
        ]
      }
    ]
  }
  Validate the JSON, show a preview of what will be imported, and require confirmation before committing to the database.

Analytics additions to admin dashboard:
- "Practice Analytics" section:
  - Total attempts today / this week / this month
  - Average accuracy by subject
  - Most attempted problems (top 10)
  - Most failed problems (top 10)

=== CSS ADDITIONS ===

Add to style.css:
- Quiz card styles (problem display, choice cards with hover/selected/correct/incorrect states)
- Hint reveal animation (slide-down)
- Solution step accordion styles
- Reading progress bar (thin bar at top of page)
- Quiz progress bar (thicker, within quiz interface)
- Confetti animation keyframes
- Blur overlay for premium content with lock icon badge
- Progress dashboard styles (stat cards, progress bars, activity feed)
- Breadcrumb navigation styles
- Responsive adjustments for all new components

=== API DESIGN ===

All /api/* endpoints return JSON. Errors return appropriate HTTP status codes with {"error": "message"} body. Use Flask's jsonify(). Protect API endpoints with CSRF tokens passed via X-CSRFToken header from a meta tag in base.html.

=== WHAT TO DELIVER ===

Produce every new file and every modified file with complete, working code. Ensure:
1. All AJAX interactions work without page reloads
2. KaTeX renders correctly in dynamically inserted content (call renderMathInElement after DOM updates)
3. Freemium gating is airtight — server-side enforcement, not just UI hiding
4. Progress tracking logs every attempt accurately
5. The admin bulk import works correctly with the JSON format specified
6. Mobile responsive for all new pages
7. No external JS libraries — vanilla JS only (except KaTeX CDN)
8. All new routes have proper error handling
```

---

## PHASE 3 — Content Loading, SEO, Security & Launch Polish

Paste this entire prompt into Claude after Phase 2 is complete and working:

---

```
You are continuing to build CoachPrash.com. Phase 1 (foundation) and Phase 2 (self-study engine) are complete. This is Phase 3: loading real demo content, polishing the UI, adding SEO fundamentals, security hardening, and preparing for soft launch.

=== WHAT PHASE 3 DELIVERS ===
1. Professional demo content for one sample topic from each of the 5 subject areas
2. Polished placeholder assets and refined copy
3. SEO fundamentals (titles, meta, sitemap, robots.txt)
4. Error pages (404, 500, 403)
5. Security hardening (rate limiting, sanitization, headers)
6. Performance basics (caching, pagination, indexes)
7. Launch checklist

=== DEMO CONTENT TO CREATE ===

Create content JSON files (using the Phase 2 bulk import format) for each of these 5 sample topics. Each topic should have 3-4 concepts with 1 problem set per concept (5-8 problems each). Content must be mathematically/scientifically accurate. Use LaTeX notation (\( \) for inline, \[ \] for display) for all math.

IMPORTANT: Make the first concept in each topic free-tier and the rest premium. Make the first problem set in each topic free and the rest premium. This demonstrates the freemium model.

1. MATH — Algebra 1: "Solving Linear Equations"
   Concepts:
   a) "What is a Linear Equation?" (free) — definition, forms (slope-intercept, standard, point-slope), real-world examples
      Problem set: 6 problems (3 MCQ, 3 fill-in-blank) — identifying linear equations, converting between forms
   b) "Solving One-Step Equations" (premium) — addition/subtraction, multiplication/division property of equality
      Problem set: 8 problems mixing MCQ and fill-in-blank, progressive difficulty
   c) "Solving Multi-Step Equations" (premium) — distributing, combining like terms, variables on both sides
      Problem set: 8 problems, include 2 "hard" difficulty
   d) "Word Problems with Linear Equations" (premium) — translating English to equations, solving, interpreting
      Problem set: 5 problems, all fill-in-blank

2. PHYSICS — Honors Physics: "Newton's Laws of Motion"
   Concepts:
   a) "Newton's First Law: Inertia" (free) — definition, examples, frames of reference, \( F_{net} = 0 \) equilibrium
      Problem set: 5 problems — conceptual MCQ about inertia scenarios
   b) "Newton's Second Law: F = ma" (premium) — derivation, units, free body diagrams
      Problem set: 8 problems — calculation-based (given F find a, given m and a find F, multi-force problems)
   c) "Newton's Third Law: Action-Reaction" (premium) — pairs, common misconceptions, applications
      Problem set: 6 problems — identifying action-reaction pairs, conceptual analysis
   d) "Applying Newton's Laws" (premium) — combined problems, inclined planes, tension, normal force
      Problem set: 6 problems — multi-step calculation problems

3. CHEMISTRY — Honors Chemistry: "The Mole Concept"
   Concepts:
   a) "What is a Mole?" (free) — Avogadro's number (\( 6.022 \times 10^{23} \)), analogy to "dozen", molar mass
      Problem set: 6 problems — conversions between moles, particles, and grams
   b) "Molar Mass Calculations" (premium) — using periodic table, molecular compounds, formula mass
      Problem set: 6 problems — calculating molar mass from formulas
   c) "Stoichiometry Basics" (premium) — mole ratios from balanced equations, mole-to-mole conversions
      Problem set: 8 problems — given balanced equation, calculate moles of product/reactant

4. COMPUTER SCIENCE — AP CS A (Java): "Arrays and ArrayLists"
   Concepts:
   a) "Introduction to Arrays" (free) — declaration, initialization, indexing, length, traversal, common errors (ArrayIndexOutOfBoundsException)
      Problem set: 6 problems — code tracing (MCQ: "What does this code output?"), fill-in-blank for syntax
   b) "Array Algorithms" (premium) — linear search, finding max/min, computing sum/average, reversing
      Problem set: 8 problems — code completion and output prediction
   c) "ArrayLists" (premium) — ArrayList vs arrays, add/remove/get/set/size, autoboxing, traversal with for-each
      Problem set: 6 problems — MCQ on behavior, fill-in-blank for method calls
   d) "Common Array/ArrayList Patterns" (premium) — removing elements during traversal, parallel arrays, 2D array intro
      Problem set: 5 problems — AP exam style questions

   Use Java code blocks (<pre><code class="language-java">) for code. Do NOT use LaTeX for code. DO use LaTeX for any math expressions.

5. TEST PREP — SAT Math: "Heart of Algebra"
   Concepts:
   a) "Linear Equations and Inequalities" (free) — SAT-specific strategies, common trap answers, time management tips
      Problem set: 6 problems — formatted like actual SAT questions with 4 answer choices
   b) "Systems of Linear Equations" (premium) — substitution, elimination, no-solution/infinite-solution recognition
      Problem set: 8 problems — SAT-style
   c) "Linear Functions and Graphs" (premium) — slope interpretation, intercept meaning, parallel/perpendicular lines
      Problem set: 6 problems — graph interpretation (describe graphs verbally using diagram placeholders)

CONTENT QUALITY REQUIREMENTS:
- Every explanation must be accurate and grade-appropriate
- Use encouraging, clear language (not dry textbook voice — think helpful coach, not professor)
- Include "Key Takeaway" callout boxes at the end of each concept (wrap in <div class="callout callout-key">)
- Include "Common Mistake" warning boxes where relevant (wrap in <div class="callout callout-warning">)
- Hints should guide thinking, not give away the answer (e.g., "What operation undoes multiplication?" not "Divide both sides by 3")
- Solutions should explain WHY each step works, not just show the mechanics
- For every problem: include 2 hints and a 3-4 step solution

=== SEED DATA UPDATES ===

Update seed.py to:
1. Load all 5 content JSON files via the bulk import logic from Phase 2
2. Replace the 5 placeholder testimonials with 8 realistic ones:
   - Mix of grade levels (8th grade through college freshman)
   - Mix of subjects mentioned
   - All 4-5 star ratings
   - Specific and believable, e.g.: "Coach Prash helped me go from a C to an A in AP Calculus BC. His step-by-step approach to integration techniques finally made everything click."
3. Replace the 2 placeholder blog posts with 4 substantive ones:
   - "5 Strategies to Ace AP Calculus AB" (~400 words, practical study tips, include some LaTeX examples)
   - "How to Study Effectively for the SAT Math Section" (~400 words, test prep advice)
   - "Why Every Student Should Learn to Code" (~350 words, advocacy piece)
   - "Understanding the Mole: Chemistry's Most Important Concept" (~400 words, educational content with LaTeX, doubles as teaser for self-study content)
4. Create demo student accounts for testing:
   - demo_free@coachprash.com (password: demo123, free tier)
   - demo_premium@coachprash.com (password: demo123, premium tier)
   With pre-populated progress data (a few completed concepts, some attempt logs) so the progress dashboard has content to display
5. Remain idempotent — safe to re-run

=== ERROR PAGES ===

Register as Flask error handlers in the app factory:

404 — "Page Not Found":
- Friendly message: "Oops! We couldn't find what you're looking for."
- Suggestions: link to Home, link to Subjects, search suggestion
- Styled consistently with the rest of the site

500 — "Something Went Wrong":
- Apology message: "We're experiencing a hiccup. Please try refreshing the page."
- Link to Contact page to report persistent issues
- Do NOT show technical details

403 — "Access Denied":
- If it's a premium content issue: explain and link to upgrade info
- Otherwise: "You don't have permission to access this page."

=== SEO FUNDAMENTALS ===

1. Update base.html <head>:
   - Dynamic <title>: {% block title %}CoachPrash — STEM Tutoring & Practice{% endblock %}
   - Dynamic meta description: {% block meta_description %}Expert STEM coaching...{% endblock %}
   - <meta name="viewport" content="width=device-width, initial-scale=1.0">
   - Open Graph tags (og:title, og:description, og:type, og:url, og:site_name)
   - Canonical URL tag
   - Favicon: generate a simple "CP" text favicon as a data URI (navy background, white text)

2. Set unique <title> and meta description for every page/template:
   - Home: "CoachPrash — Expert STEM Tutoring & Interactive Practice for All Levels"
   - About: "About CoachPrash — Your Dedicated STEM Tutor"
   - Subjects catalog: "STEM Subjects — Math, Physics, Chemistry, CS, Test Prep | CoachPrash"
   - Each topic: "Learn [Topic Name] | [Subject] | CoachPrash"
   - Each concept: "[Concept Title] — [Topic Name] | CoachPrash"
   - Blog posts: "[Post Title] | CoachPrash Resources"
   - Progress: "My Progress | CoachPrash"

3. Create /robots.txt (served by Flask route):
   - Allow all crawlers
   - Disallow: /admin/, /api/, /progress/
   - Sitemap: https://coachprash.com/sitemap.xml

4. Create /sitemap.xml (dynamically generated by Flask route):
   - Include: home, about, contact, testimonials, resources page
   - Include: all active subjects and topics
   - Include: all free-tier concepts (don't include premium-only in sitemap)
   - Include: all published blog posts
   - Set appropriate lastmod, changefreq, priority values

=== SECURITY HARDENING ===

1. Rate limiting (add Flask-Limiter to requirements.txt):
   - /login: 5 attempts per minute per IP
   - /register: 3 attempts per minute per IP
   - /contact: 2 submissions per minute per IP
   - /api/*: 60 requests per minute per user/IP

2. Input sanitization:
   - Use nh3 (add to requirements.txt) for any admin-submitted HTML content
   - Verify Jinja2 autoescaping is enabled on all templates

3. Security headers (add via @app.after_request):
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Content-Security-Policy: default-src 'self'; script-src 'self' cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' fonts.googleapis.com 'unsafe-inline'; font-src fonts.gstatic.com; img-src 'self' data:;
   - Referrer-Policy: strict-origin-when-cross-origin

4. CSRF: verify Flask-WTF CSRF is applied to all POST forms and API endpoints

=== UI POLISH ===

1. Loading states:
   - CSS-only loading spinner for AJAX requests in the practice engine
   - Show spinner during answer checking, hint loading, solution loading

2. Empty states:
   - Progress dashboard with no activity: "Start your learning journey" message with link to Subjects
   - Subject with no published topics: "Content coming soon" card
   - Blog with no posts: "Check back soon for study tips and resources"

3. Micro-interactions:
   - Button hover animations (subtle scale + shadow transition)
   - Card hover lift effect (translateY(-2px) + shadow increase)
   - Smooth scroll for anchor links
   - Flash messages styled as toast notifications that auto-dismiss after 5 seconds (vanilla JS)

4. Footer (add to base.html):
   - 3-column layout: Quick Links | Subjects | Connect
   - Quick Links: Home, About, Subjects, Resources, Contact
   - Subjects: Math, Physics, Chemistry, CS, Test Prep (link to each subject page)
   - Connect: Email placeholder, social media icon placeholders (Font Awesome or Unicode icons)
   - Bottom bar: "© 2026 CoachPrash. All rights reserved."
   - Responsive: stack columns on mobile

5. Callout box styles (for content):
   - .callout-key: light gold background, gold left border, "Key Takeaway" header
   - .callout-warning: light red background, crimson left border, "Common Mistake" header
   - .callout-tip: light green background, green left border, "Tip" header

=== PERFORMANCE ===

1. Cache-Control headers for static assets (1 year, with cache-busting via query param ?v=hash)
2. Lazy-load images (loading="lazy" attribute)
3. Pagination for all list views (20 items per page) — subjects, topics, blog posts, admin tables
4. Database indexes: create a migration for any missing indexes on slug fields, foreign keys, is_active, created_at

=== UPDATED REQUIREMENTS.TXT ===
Add these to existing requirements:
Flask-Limiter==3.*
nh3==0.2.*

=== WHAT TO DELIVER ===

1. All 5 content JSON files (in a /content/ directory) — complete, accurate, well-written educational content
2. Updated seed.py with all new seed data (testimonials, blog posts, demo accounts, content loading)
3. Error page templates (404.html, 500.html, 403.html)
4. Updated base.html with SEO tags, security headers, footer, and toast JS
5. Routes for robots.txt and sitemap.xml
6. Updated requirements.txt
7. All CSS additions (callouts, loading spinner, empty states, footer, toasts, micro-interactions)
8. Any modified Python files
9. A LAUNCH_CHECKLIST.md file with:
   - Pre-launch verification steps (test every page, test free vs premium, test admin panel, test on mobile)
   - Environment variables to set on Railway
   - Post-launch monitoring steps
   - Content expansion roadmap (what to build next)

The site should be ready for CoachPrash to show to potential students and parents after this phase.
```

---

## FUTURE EXPANSION — Phase Descriptions

These are brief descriptions for future phases. When ready, expand each into a full prompt following the pattern above.

### Phase 4: Stripe Payment Integration
Integrate Stripe for premium subscriptions. Add a StripeCustomer model linked to User. Create a /pricing page with Free vs Premium comparison table. Implement Stripe Checkout for monthly ($19.99/mo) and annual ($149.99/yr) plans. Handle webhooks for subscription creation, renewal, cancellation, and failed payment. Replace access-code-based premium upgrade with Stripe while keeping access codes as a secondary option (for gifted/comped accounts). Add subscription management to the student dashboard and admin panel.

### Phase 5: Calendar & Scheduling System
Add a scheduling system for 1-on-1 tutoring sessions. Models: TutoringSession (datetime, duration, subject, topic, student, status, meeting_link, notes), Availability (recurring weekly slots the coach sets). Student-facing: browse available slots, book a session, view upcoming/past sessions, cancel/reschedule (24hr policy). Coach-facing (admin): set availability, view calendar, confirm/cancel sessions, add session notes. Send confirmation emails using Flask-Mail with SendGrid. Integrate with Google Calendar API for the coach's calendar.

### Phase 6: Adaptive Practice Engine
Build an adaptive practice system that adjusts problem difficulty based on student performance. Algorithm: track mastery_score per concept using a modified Elo-like system — when a student answers correctly, increase their estimated ability; when incorrect, decrease. Select next problem based on the gap between student ability and problem difficulty (target ~70% success rate for optimal learning). Create AdaptivePath model that generates a recommended sequence of concepts and problem sets for each student. Show "Recommended Next" on the progress dashboard.

### Phase 7: Full Content Expansion
Load full content for all remaining subjects and topics. Priority order: (1) all Math courses, (2) all Physics courses, (3) all Test Prep, (4) CS courses, (5) Chemistry. Each topic needs 4-6 concepts with 6-10 problems each. Follow the same quality standards as the demo content. Create a content style guide document for consistency.

### Phase 8: Student Analytics & Parent Portal
Create a parent/guardian portal. Parents register with an access code linked to their child's account. They can view (read-only): progress dashboard, recent activity, mastery scores, time spent studying. Add email digest option (weekly summary sent via Flask-Mail). For the admin: create a comprehensive analytics dashboard with charts (Chart.js) showing enrollment trends, engagement metrics, content effectiveness (which concepts have lowest mastery), and revenue metrics.

---

## How to Use This Document

1. **Phase 1**: Copy the Phase 1 prompt above and paste it into Claude Pro. Execute it. Deploy to Railway. Verify the site works.
2. **Phase 2**: Once Phase 1 is deployed and working, paste the Phase 2 prompt. Execute it. Test the self-study engine.
3. **Phase 3**: Once Phase 2 is working, paste the Phase 3 prompt. Execute it. Run through the launch checklist.
4. **Future phases**: When ready, expand the brief descriptions above into full prompts and execute them one at a time.

Each phase is designed to be independently deployable and testable. You can take breaks between phases — each prompt is self-contained and references the architecture established in Phase 1.
