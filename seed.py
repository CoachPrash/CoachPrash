import os
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.content import Subject, Topic
from app.models.access import AccessCode
from app.models import Testimonial, BlogPost
from app.utils.content_loader import load_content_json


def run_seed():
    from flask import current_app
    try:
        current_app._get_current_object()
        _seed_data()
    except RuntimeError:
        app = create_app()
        with app.app_context():
            _seed_data()


def _seed_data():
    print('Seeding database...')

    # --- Admin User ---
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@coachprash.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            username='CoachPrash',
            role='admin',
            tier='premium',
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f'  Created admin user: {admin_email}')
    else:
        print(f'  Admin user already exists: {admin_email}')

    # --- Subjects & Topics ---
    subjects_data = [
        {
            'name': 'Mathematics',
            'slug': 'mathematics',
            'icon': '🔢',
            'description': 'From arithmetic fundamentals to college-level calculus and linear algebra. Build a strong mathematical foundation at every level.',
            'display_order': 1,
            'topics': [
                ('Arithmetic', 'arithmetic', 'elementary', 'Master the building blocks: addition, subtraction, multiplication, division, fractions, and decimals.'),
                ('Algebra 1', 'algebra-1', 'middle_school', 'Linear equations, inequalities, graphing, and an introduction to functions.'),
                ('Geometry', 'geometry', 'high_school', 'Points, lines, angles, triangles, circles, area, volume, and geometric proofs.'),
                ('Algebra 2', 'algebra-2', 'high_school', 'Polynomials, rational expressions, exponentials, logarithms, and complex numbers.'),
                ('Precalculus', 'precalculus', 'high_school', 'Advanced functions, trigonometry, sequences, series, and limits.'),
                ('Calculus \u2014 Honors', 'calculus-honors', 'high_school', 'Honors-level introduction to limits, derivatives, and integrals.'),
                ('AP Calculus AB', 'ap-calculus-ab', 'ap', 'Limits, derivatives, integrals, and the Fundamental Theorem of Calculus. Full AP exam preparation.'),
                ('AP Calculus BC', 'ap-calculus-bc', 'ap', 'All AB topics plus parametric, polar, vector functions, and series. Comprehensive AP exam prep.'),
                ('Statistics \u2014 Honors', 'statistics-honors', 'high_school', 'Data analysis, probability, distributions, and inference at the honors level.'),
                ('AP Statistics', 'ap-statistics', 'ap', 'Exploring data, sampling, probability, inference, and regression. AP exam focused.'),
                ('Discrete Mathematics', 'discrete-mathematics', 'college', 'Combinatorics, graph theory, logic, proofs, and number theory.'),
                ('Multivariable Calculus', 'multivariable-calculus', 'college', 'Partial derivatives, multiple integrals, vector calculus, and applications.'),
                ('Linear Algebra', 'linear-algebra', 'college', 'Vectors, matrices, linear transformations, eigenvalues, and vector spaces.'),
            ],
        },
        {
            'name': 'Physics',
            'slug': 'physics',
            'icon': '\u269b\ufe0f',
            'description': 'Mechanics, electricity & magnetism, and beyond. Develop physical intuition and problem-solving skills.',
            'display_order': 2,
            'topics': [
                ('Honors Physics', 'honors-physics', 'high_school', 'Kinematics, dynamics, energy, momentum, waves, and thermodynamics at the honors level.'),
                ('AP Physics 1: Mechanics', 'ap-physics-1-mechanics', 'ap', 'Algebra-based mechanics: kinematics, forces, energy, momentum, rotation, and oscillations.'),
                ('AP Physics 2: E&M', 'ap-physics-2-em', 'ap', 'Algebra-based electricity, magnetism, optics, and modern physics.'),
                ('AP Physics C: Mechanics', 'ap-physics-c-mechanics', 'ap', 'Calculus-based mechanics with rigorous problem-solving and free-response preparation.'),
                ('AP Physics C: E&M', 'ap-physics-c-em', 'ap', 'Calculus-based electricity and magnetism: electric fields, circuits, magnetic fields, and induction.'),
            ],
        },
        {
            'name': 'Chemistry',
            'slug': 'chemistry',
            'icon': '🧪',
            'description': 'Atomic structure, chemical reactions, stoichiometry, and more. Build a solid understanding of chemistry.',
            'display_order': 3,
            'topics': [
                ('Honors Chemistry', 'honors-chemistry', 'high_school', 'Atomic theory, periodic trends, bonding, reactions, stoichiometry, and solutions.'),
                ('Advanced Chemistry', 'advanced-chemistry', 'high_school', 'Equilibrium, thermodynamics, kinetics, acids/bases, and electrochemistry.'),
            ],
        },
        {
            'name': 'Computer Science',
            'slug': 'computer-science',
            'icon': '💻',
            'description': 'From programming fundamentals to algorithms and data structures. Learn to think computationally.',
            'display_order': 4,
            'topics': [
                ('AP Computer Science Principles', 'ap-cs-principles', 'ap', 'Big ideas of computing: abstraction, data, algorithms, programming, internet, and impact.'),
                ('AP Computer Science A \u2014 Java', 'ap-cs-a-java', 'ap', 'Object-oriented programming in Java: classes, inheritance, arrays, recursion, and sorting.'),
                ('Algorithms and Data Structures', 'algorithms-data-structures', 'college', 'Searching, sorting, trees, graphs, dynamic programming, and algorithm analysis.'),
            ],
        },
        {
            'name': 'Test Prep',
            'slug': 'test-prep',
            'icon': '📝',
            'description': 'Targeted preparation for SAT and ACT exams. Strategies, practice, and confidence building.',
            'display_order': 5,
            'topics': [
                ('SAT Mathematics', 'sat-mathematics', 'high_school', 'Heart of Algebra, Problem Solving & Data Analysis, Passport to Advanced Math, and Additional Topics.'),
                ('ACT Mathematics', 'act-mathematics', 'high_school', 'Pre-Algebra, Algebra, Geometry, and Trigonometry sections of the ACT.'),
                ('ACT Science', 'act-science', 'high_school', 'Data representation, research summaries, and conflicting viewpoints passages.'),
            ],
        },
    ]

    for sdata in subjects_data:
        subject = Subject.query.filter_by(slug=sdata['slug']).first()
        if not subject:
            subject = Subject(
                name=sdata['name'],
                slug=sdata['slug'],
                icon=sdata['icon'],
                description=sdata['description'],
                display_order=sdata['display_order'],
            )
            db.session.add(subject)
            db.session.flush()
            print(f'  Created subject: {subject.name}')

        for t_order, (t_name, t_slug, t_diff, t_desc) in enumerate(sdata['topics']):
            topic = Topic.query.filter_by(subject_id=subject.id, slug=t_slug).first()
            if not topic:
                topic = Topic(
                    subject_id=subject.id,
                    name=t_name,
                    slug=t_slug,
                    description=t_desc,
                    difficulty_level=t_diff,
                    display_order=t_order + 1,
                )
                db.session.add(topic)

    db.session.commit()
    print('  Subjects and topics seeded.')

    # --- Load Content JSON Files ---
    content_dir = os.path.join(os.path.dirname(__file__), 'content')
    content_files = [
        'math_algebra1_linear_equations.json',
        'physics_honors_newtons_laws.json',
        'chemistry_honors_mole_concept.json',
        'cs_apcs_arrays_arraylists.json',
        'testprep_sat_heart_of_algebra.json',
    ]
    for fname in content_files:
        fpath = os.path.join(content_dir, fname)
        if not os.path.exists(fpath):
            print(f'  Content file not found, skipping: {fname}')
            continue
        try:
            result = load_content_json(fpath)
            if result is None:
                print(f'  Content already loaded, skipping: {fname}')
            else:
                print(f'  Loaded {fname}: {result["concepts"]} concepts, '
                      f'{result["problems"]} problems')
        except Exception as e:
            print(f'  Error loading {fname}: {e}')

    # --- Testimonials ---
    if Testimonial.query.count() == 0:
        testimonials = [
            Testimonial(
                student_name='Sarah M.',
                student_grade='11th Grade',
                content='Coach Prash helped me go from a C to an A in AP Calculus BC. His step-by-step approach to integration techniques finally made everything click. I actually enjoy calculus now!',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='James L.',
                student_grade='10th Grade',
                content='I was struggling with Honors Physics until I started working with Coach Prash. He breaks down complex problems into manageable steps and always makes sure I understand the underlying concepts before moving on.',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='Priya K.',
                student_grade='12th Grade',
                content='Thanks to Coach Prash, I scored a 790 on the SAT Math section. His targeted practice sets and test-taking strategies made all the difference. I felt so confident walking into the exam.',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='David R.',
                student_grade='College Freshman',
                content='The AP CS A preparation I received was outstanding. Coach Prash taught me not just how to code, but how to think like a programmer. I earned a 5 on the exam and felt well-prepared for my university CS courses.',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='Emily C.',
                student_grade='9th Grade',
                content='Coach Prash makes Geometry fun and understandable. I actually look forward to our sessions now. My confidence in math has grown so much this year!',
                rating=5,
                is_featured=False,
            ),
            Testimonial(
                student_name='Marcus T.',
                student_grade='11th Grade',
                content='Honors Chemistry was my hardest class until Coach Prash showed me how to approach stoichiometry problems systematically. My grade went from a B- to an A. His practice problems are really well designed.',
                rating=4,
                is_featured=False,
            ),
            Testimonial(
                student_name='Aisha N.',
                student_grade='8th Grade',
                content='I used to dread math class, but Coach Prash helped me see that algebra is actually like solving puzzles. He is patient and explains things in different ways until it makes sense. My Algebra 1 grade improved by two letter grades.',
                rating=5,
                is_featured=False,
            ),
            Testimonial(
                student_name='Kevin W.',
                student_grade='12th Grade',
                content='Coach Prash helped me prepare for the AP Statistics exam in just two months. His clear explanations of hypothesis testing and confidence intervals were exactly what I needed. Scored a 4 on the exam!',
                rating=4,
                is_featured=False,
            ),
        ]
        db.session.add_all(testimonials)
        db.session.commit()
        print('  Testimonials seeded (8 total).')
    else:
        print('  Testimonials already exist, skipping.')

    # --- Blog Posts ---
    if BlogPost.query.count() == 0:
        blog_content_1 = (
            '<h2>1. Master the Fundamentals First</h2>'
            '<p>Before diving into derivatives and integrals, make sure your algebra and trigonometry skills are rock solid. '
            'Many AP Calculus mistakes come from algebraic errors, not calculus concepts. Spend time reviewing:</p>'
            '<ul><li>Factoring polynomials and rational expressions</li>'
            '<li>Trigonometric identities (especially Pythagorean identities)</li>'
            '<li>Function composition and transformation</li>'
            '<li>Exponent and logarithm rules</li></ul>'
            '<p>A strong precalculus foundation makes calculus feel like a natural next step rather than a foreign language.</p>'
            '<h2>2. Understand, Don\'t Just Memorize</h2>'
            '<p>Learn <em>why</em> formulas work. Understanding the derivation of the power rule or the chain rule '
            'makes it easier to apply them in unfamiliar situations. When you understand the logic behind a rule, '
            'you can reconstruct it even if your memory fails during the exam.</p>'
            '<p>For example, instead of just memorizing \\(\\frac{d}{dx}[x^n] = nx^{n-1}\\), understand that it comes '
            'from the limit definition of the derivative. This deeper understanding pays dividends on free-response questions.</p>'
            '<h2>3. Practice Free-Response Questions Early</h2>'
            '<p>Don\'t wait until April to start practicing FRQs. The AP exam tests your ability to communicate '
            'mathematical reasoning clearly, and that takes practice. Key tips for FRQs:</p>'
            '<ul><li>Show all your work \u2014 partial credit is real and significant</li>'
            '<li>Use proper notation (don\'t drop the \\(dx\\) in integrals)</li>'
            '<li>Label your answers clearly</li>'
            '<li>If you use a calculator, write the setup before the numerical answer</li></ul>'
            '<h2>4. Use the Fundamental Theorem of Calculus</h2>'
            '<p>This theorem connects derivatives and integrals and is arguably the most important concept in the course. '
            'Make sure you understand both parts:</p>'
            '<ul><li><strong>Part 1:</strong> If \\(F(x) = \\int_a^x f(t)\\,dt\\), then \\(F\'(x) = f(x)\\)</li>'
            '<li><strong>Part 2:</strong> \\(\\int_a^b f(x)\\,dx = F(b) - F(a)\\) where \\(F\\) is any antiderivative of \\(f\\)</li></ul>'
            '<p>These ideas appear in nearly every section of the AP exam.</p>'
            '<h2>5. Review Consistently</h2>'
            '<p>Spend 20-30 minutes each day reviewing previous topics. Calculus is cumulative \u2014 '
            'every new concept builds on what came before. Use spaced repetition: review older topics less frequently '
            'but keep them in rotation. A little bit of review every day is far more effective than cramming the night before a test.</p>'
        )
        blog_content_2 = (
            '<h2>Start Early and Plan Ahead</h2>'
            '<p>Give yourself at least 2-3 months of focused preparation. Create a study schedule that covers '
            'all four math domains: Heart of Algebra, Problem Solving & Data Analysis, Passport to Advanced Math, '
            'and Additional Topics in Math.</p>'
            '<p>Break your schedule into weekly goals. For example: Week 1-2 on linear equations, Week 3-4 on '
            'systems of equations, and so on. This prevents last-minute panic and builds confidence gradually.</p>'
            '<h2>Know the Test Format</h2>'
            '<p>The SAT Math section has two modules, both of which allow a calculator. '
            'Understanding the format helps you manage your time effectively:</p>'
            '<ul><li>Module 1: 22 questions in 35 minutes (roughly 1.5 minutes per question)</li>'
            '<li>Module 2: 22 questions in 35 minutes (adaptive difficulty based on Module 1)</li>'
            '<li>Mix of multiple-choice and student-produced response (grid-in) questions</li></ul>'
            '<h2>Focus on Your Weak Areas</h2>'
            '<p>Take a full practice test first to identify where you lose the most points. Then focus your study time '
            'on those specific areas rather than reviewing topics you already know well. Common trouble spots include:</p>'
            '<ul><li>Systems of equations with no solution or infinitely many solutions</li>'
            '<li>Interpreting slope and y-intercept in context</li>'
            '<li>Quadratic equations and their graphs</li>'
            '<li>Percent increase/decrease problems</li></ul>'
            '<h2>Practice Under Real Conditions</h2>'
            '<p>Time yourself. Take full-length practice tests in one sitting. This builds stamina and helps you '
            'develop pacing strategies for test day. Simulate real conditions: no phone, no extra breaks, '
            'and the same calculator you\'ll use on test day.</p>'
            '<h2>Review Every Mistake</h2>'
            '<p>After each practice session, go through every wrong answer. Understand <em>why</em> you got it wrong '
            'and how to approach similar problems correctly. Keep an error log \u2014 write down the topic, what you got wrong, '
            'and the correct approach. Review this log weekly. You\'ll notice patterns in your mistakes, and addressing '
            'those patterns is the fastest way to improve your score.</p>'
        )
        blog_content_3 = (
            '<h2>Read the Problem Twice</h2>'
            '<p>Physics problems are notorious for containing important details in seemingly throwaway phrases. '
            'Before reaching for equations, read the problem carefully and identify:</p>'
            '<ul><li>What quantities are given (with units!)</li>'
            '<li>What quantity you need to find</li>'
            '<li>What physical situation is being described</li>'
            '<li>Any implicit information (e.g., "starts from rest" means initial velocity = 0)</li></ul>'
            '<h2>Draw a Diagram</h2>'
            '<p>Almost every physics problem benefits from a visual representation. Draw free-body diagrams for '
            'force problems, motion diagrams for kinematics, and circuit diagrams for electricity. A good diagram '
            'helps you see relationships that are hard to spot from text alone.</p>'
            '<p>Label everything: forces, velocities, angles, distances. Include a coordinate system with clearly '
            'defined positive directions.</p>'
            '<h2>Choose Your Equations Wisely</h2>'
            '<p>Don\'t just grab the first equation you see with the right variables. Ask yourself:</p>'
            '<ul><li>Does this equation apply to the situation described?</li>'
            '<li>Do I know enough variables to solve it?</li>'
            '<li>Am I using consistent units throughout?</li></ul>'
            '<p>Sometimes you\'ll need to combine two or three equations. That\'s normal \u2014 most real physics problems '
            'require building a chain of reasoning, not just plugging into one formula.</p>'
            '<h2>Check Your Units</h2>'
            '<p><strong>Dimensional analysis</strong> is your best friend. If your answer for velocity comes out in '
            'kg\u00b7m, something went wrong. Carry units through every calculation and verify that your final answer '
            'has the correct units. This simple habit catches a surprising number of errors.</p>'
            '<h2>Estimate Before You Calculate</h2>'
            '<p>Before punching numbers into your calculator, estimate the order of magnitude of your answer. '
            'If you\'re calculating the speed of a car and get 50,000 m/s, you know something is off. '
            'This intuition develops with practice and saves you from careless mistakes on exams.</p>'
        )
        blog_content_4 = (
            '<h2>CS Is Everywhere</h2>'
            '<p>Computer science is no longer just for people who want to be software engineers. '
            'Whether you want to be a doctor, a business leader, an artist, or a scientist, understanding '
            'computational thinking will give you a significant advantage in your career.</p>'
            '<ul><li><strong>Medicine:</strong> AI assists in diagnosis, genomics uses massive data processing</li>'
            '<li><strong>Business:</strong> Data analytics drives decision-making at every level</li>'
            '<li><strong>Art & Music:</strong> Digital tools, generative AI, and interactive media</li>'
            '<li><strong>Science:</strong> Simulations, data analysis, and computational modeling</li></ul>'
            '<h2>Computational Thinking Is a Life Skill</h2>'
            '<p>At its core, computer science teaches you how to break complex problems into smaller, '
            'manageable parts. This skill \u2014 called <strong>decomposition</strong> \u2014 applies far beyond programming:</p>'
            '<ul><li>Planning a large project by breaking it into milestones</li>'
            '<li>Debugging a process by isolating where things go wrong</li>'
            '<li>Organizing information efficiently</li></ul>'
            '<p>These thinking patterns make you a better problem-solver in every domain.</p>'
            '<h2>You Don\'t Need to Be a "Math Person"</h2>'
            '<p>One of the biggest myths about CS is that you need to be a math genius. While some areas of '
            'computer science involve heavy math, many don\'t. Web development, user experience design, '
            'database management, and cybersecurity all emphasize logic and creativity over advanced mathematics.</p>'
            '<p>If you can think logically and are willing to learn from your mistakes (debugging is 90% of coding!), '
            'you can succeed in computer science.</p>'
            '<h2>Start Small, Build Up</h2>'
            '<p>You don\'t need to build the next social media platform on day one. Start with:</p>'
            '<ol><li>Simple programs that solve real problems you care about</li>'
            '<li>Modifying existing code to understand how it works</li>'
            '<li>Building progressively more complex projects</li>'
            '<li>Collaborating with others on group projects</li></ol>'
            '<p>Every expert programmer started with "Hello, World!" The journey of a thousand programs begins '
            'with a single line of code.</p>'
            '<h2>AP CS A: A Great Starting Point</h2>'
            '<p>If you\'re a high school student considering CS, AP Computer Science A is an excellent choice. '
            'You\'ll learn Java \u2014 a widely-used, industry-standard language \u2014 and build a foundation in '
            'object-oriented programming that transfers to virtually any other language. Plus, a good AP score '
            'can earn you college credit and place you into more advanced courses.</p>'
        )
        posts = [
            BlogPost(
                author_id=admin.id,
                title='5 Tips for Acing AP Calculus',
                slug='5-tips-for-acing-ap-calculus',
                excerpt='Practical strategies to help you succeed in AP Calculus AB or BC, from mastering fundamentals to conquering free-response questions.',
                content_raw=blog_content_1,
                content_html=blog_content_1,
                is_published=True,
                published_at=datetime.now(timezone.utc) - timedelta(days=21),
            ),
            BlogPost(
                author_id=admin.id,
                title='How to Study Effectively for the SAT',
                slug='how-to-study-effectively-for-the-sat',
                excerpt='A practical guide to SAT Math preparation strategies that actually work, from study planning to test-day confidence.',
                content_raw=blog_content_2,
                content_html=blog_content_2,
                is_published=True,
                published_at=datetime.now(timezone.utc) - timedelta(days=14),
            ),
            BlogPost(
                author_id=admin.id,
                title="A Beginner's Guide to Physics Problem-Solving",
                slug='beginners-guide-to-physics-problem-solving',
                excerpt='Five essential strategies for tackling physics problems with confidence, from reading carefully to checking your units.',
                content_raw=blog_content_3,
                content_html=blog_content_3,
                is_published=True,
                published_at=datetime.now(timezone.utc) - timedelta(days=7),
            ),
            BlogPost(
                author_id=admin.id,
                title='Why Computer Science Matters for Every Student',
                slug='why-computer-science-matters-for-every-student',
                excerpt='Computer science is not just for future software engineers. Here is why every student should consider learning to code.',
                content_raw=blog_content_4,
                content_html=blog_content_4,
                is_published=True,
                published_at=datetime.now(timezone.utc) - timedelta(days=3),
            ),
        ]
        db.session.add_all(posts)
        db.session.commit()
        print('  Blog posts seeded (4 total).')
    else:
        print('  Blog posts already exist, skipping.')

    # --- Demo Students ---
    demo_premium_email = 'demo.student@example.com'
    demo_free_email = 'demo.free@example.com'

    if not User.query.filter_by(email=demo_premium_email).first():
        demo_premium = User(
            email=demo_premium_email,
            username='DemoStudent',
            role='student',
            tier='premium',
        )
        demo_premium.set_password('demo1234')
        db.session.add(demo_premium)
        print(f'  Created demo premium student: {demo_premium_email}')

    if not User.query.filter_by(email=demo_free_email).first():
        demo_free = User(
            email=demo_free_email,
            username='DemoFree',
            role='student',
            tier='free',
        )
        demo_free.set_password('demo1234')
        db.session.add(demo_free)
        print(f'  Created demo free student: {demo_free_email}')

    db.session.commit()

    # --- Access Codes ---
    if AccessCode.query.count() == 0:
        codes = [
            AccessCode(
                code='FREEACCS',
                tier='free',
                max_uses=None,
                created_by=admin.id,
                is_active=True,
            ),
            AccessCode(
                code='PREM2026',
                tier='premium',
                max_uses=10,
                created_by=admin.id,
                is_active=True,
            ),
            AccessCode(
                code='EXPIRED1',
                tier='premium',
                max_uses=5,
                expires_at=datetime.now(timezone.utc) - timedelta(days=30),
                created_by=admin.id,
                is_active=True,
            ),
        ]
        db.session.add_all(codes)
        db.session.commit()
        print('  Access codes seeded: FREEACCS (free), PREM2026 (premium, 10 uses), EXPIRED1 (expired)')
    else:
        print('  Access codes already exist, skipping.')

    print('Seeding complete!')


if __name__ == '__main__':
    run_seed()
