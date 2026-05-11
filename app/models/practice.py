import uuid
from datetime import datetime, timezone
from app.extensions import db


class ProblemSet(db.Model):
    __tablename__ = 'problem_sets'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concept_id = db.Column(db.String(36), db.ForeignKey('concepts.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    access_tier = db.Column(db.String(20), nullable=False, default='free')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    problems = db.relationship('Problem', backref='problem_set', lazy='dynamic', order_by='Problem.display_order')

    def __repr__(self):
        return f'<ProblemSet {self.title}>'


class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    problem_set_id = db.Column(db.String(36), db.ForeignKey('problem_sets.id'), nullable=False)
    question_html = db.Column(db.Text, nullable=False, default='')
    question_raw = db.Column(db.Text, nullable=False, default='')
    problem_type = db.Column(db.String(20), nullable=False, default='mcq')
    correct_answer = db.Column(db.String(500), nullable=True)
    points = db.Column(db.Integer, nullable=False, default=1)
    difficulty = db.Column(db.String(20), nullable=False, default='medium')
    display_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    choices = db.relationship('Choice', backref='problem', lazy='dynamic', order_by='Choice.display_order')
    hints = db.relationship('Hint', backref='problem', lazy='dynamic', order_by='Hint.display_order')
    solution = db.relationship('StepByStepSolution', backref='problem', uselist=False)
    attempts = db.relationship('AttemptLog', backref='problem', lazy='dynamic')

    def __repr__(self):
        return f'<Problem {self.id}>'


class Choice(db.Model):
    __tablename__ = 'choices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), nullable=False)
    choice_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Choice {self.choice_text[:30]}>'


class Hint(db.Model):
    __tablename__ = 'hints'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), nullable=False)
    hint_text = db.Column(db.Text, nullable=False)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    cost_points = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Hint {self.id}>'


class StepByStepSolution(db.Model):
    __tablename__ = 'step_by_step_solutions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    problem_id = db.Column(db.String(36), db.ForeignKey('problems.id'), unique=True, nullable=False)
    steps_json = db.Column(db.JSON, nullable=False, default=list)
    access_tier = db.Column(db.String(20), nullable=False, default='premium')

    def __repr__(self):
        return f'<Solution for Problem {self.problem_id}>'
