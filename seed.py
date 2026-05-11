import os
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.content import Subject, Topic
from app.models.access import AccessCode
from app.models import Testimonial, BlogPost


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

    # --- Testimonials ---
    if Testimonial.query.count() == 0:
        testimonials = [
            Testimonial(
                student_name='Sarah M.',
                student_grade='11th Grade',
                content='Coach Prash helped me go from a C to an A in AP Calculus BC. His step-by-step approach to integration techniques finally made everything click.',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='James L.',
                student_grade='10th Grade',
                content='I was struggling with Honors Physics until I started working with Coach Prash. He breaks down complex problems into manageable steps and always makes sure I understand the underlying concepts.',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='Priya K.',
                student_grade='12th Grade',
                content='Thanks to Coach Prash, I scored a 790 on the SAT Math section. His targeted practice and test-taking strategies made all the difference.',
                rating=5,
                is_featured=True,
            ),
            Testimonial(
                student_name='David R.',
                student_grade='College Freshman',
                content='The AP CS A preparation I received was outstanding. I earned a 5 on the exam and felt well-prepared for my university CS courses.',
                rating=4,
                is_featured=False,
            ),
            Testimonial(
                student_name='Emily C.',
                student_grade='9th Grade',
                content='Coach Prash makes Geometry fun and understandable. I actually look forward to our sessions now. My confidence in math has grown so much!',
                rating=5,
                is_featured=False,
            ),
        ]
        db.session.add_all(testimonials)
        db.session.commit()
        print('  Testimonials seeded.')
    else:
        print('  Testimonials already exist, skipping.')

    # --- Blog Posts ---
    if BlogPost.query.count() == 0:
        blog_content_1 = (
            '<h2>1. Master the Fundamentals First</h2>'
            '<p>Before diving into derivatives and integrals, make sure your algebra and trigonometry skills are rock solid. '
            'Many AP Calculus mistakes come from algebraic errors, not calculus concepts.</p>'
            '<h2>2. Understand, Don\'t Just Memorize</h2>'
            '<p>Learn <em>why</em> formulas work. Understanding the derivation of the power rule or the chain rule '
            'makes it easier to apply them in unfamiliar situations.</p>'
            '<h2>3. Practice Free-Response Questions Early</h2>'
            '<p>Don\'t wait until April to start practicing FRQs. The AP exam tests your ability to communicate '
            'mathematical reasoning clearly, and that takes practice.</p>'
            '<h2>4. Use the Fundamental Theorem of Calculus</h2>'
            '<p>This theorem connects derivatives and integrals. Make sure you understand both parts and can apply them '
            'in various contexts.</p>'
            '<h2>5. Review Consistently</h2>'
            '<p>Spend 20-30 minutes each day reviewing previous topics. Calculus is cumulative \u2014 '
            'every new concept builds on what came before.</p>'
        )
        blog_content_2 = (
            '<h2>Start Early and Plan Ahead</h2>'
            '<p>Give yourself at least 2-3 months of focused preparation. Create a study schedule that covers '
            'all four math domains: Heart of Algebra, Problem Solving & Data Analysis, Passport to Advanced Math, '
            'and Additional Topics.</p>'
            '<h2>Know the Test Format</h2>'
            '<p>The SAT Math section has two parts: calculator and no-calculator. Practice both. '
            'Get comfortable solving problems efficiently without a calculator.</p>'
            '<h2>Focus on Your Weak Areas</h2>'
            '<p>Take a practice test first to identify where you lose the most points. Then focus your study time '
            'on those specific areas rather than reviewing topics you already know well.</p>'
            '<h2>Practice Under Real Conditions</h2>'
            '<p>Time yourself. Take full-length practice tests in one sitting. This builds stamina and helps you '
            'develop pacing strategies for test day.</p>'
            '<h2>Review Every Mistake</h2>'
            '<p>After each practice session, go through every wrong answer. Understand <em>why</em> you got it wrong '
            'and how to approach similar problems correctly.</p>'
        )
        posts = [
            BlogPost(
                author_id=admin.id,
                title='5 Tips for Acing AP Calculus',
                slug='5-tips-for-acing-ap-calculus',
                excerpt='Practical strategies to help you succeed in AP Calculus AB or BC.',
                content_raw=blog_content_1,
                content_html=blog_content_1,
                is_published=True,
                published_at=datetime.now(timezone.utc) - timedelta(days=7),
            ),
            BlogPost(
                author_id=admin.id,
                title='How to Study Effectively for the SAT',
                slug='how-to-study-effectively-for-the-sat',
                excerpt='A practical guide to SAT Math preparation strategies that actually work.',
                content_raw=blog_content_2,
                content_html=blog_content_2,
                is_published=True,
                published_at=datetime.now(timezone.utc) - timedelta(days=3),
            ),
        ]
        db.session.add_all(posts)
        db.session.commit()
        print('  Blog posts seeded.')
    else:
        print('  Blog posts already exist, skipping.')

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
