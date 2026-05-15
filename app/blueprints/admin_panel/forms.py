from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField,
    BooleanField, PasswordField, DateTimeLocalField
)
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange


class StudentEditForm(FlaskForm):
    tier = SelectField('Tier', choices=[('free', 'Free'), ('premium', 'Premium')])
    is_active = BooleanField('Active')


class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    icon = StringField('Icon', validators=[Optional(), Length(max=50)])
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)


class TopicForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=150)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional()])
    difficulty_level = SelectField(
        'Difficulty',
        choices=[
            ('elementary', 'Elementary'),
            ('middle_school', 'Middle School'),
            ('high_school', 'High School'),
            ('ap', 'AP'),
            ('college', 'College'),
        ],
    )
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)


class ConceptForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    content_raw = TextAreaField('Content (Markdown + LaTeX)', validators=[Optional()])
    estimated_minutes = IntegerField(
        'Estimated Minutes', default=5, validators=[NumberRange(min=1, max=60)]
    )
    access_tier = SelectField(
        'Access Tier', choices=[('free', 'Free'), ('premium', 'Premium')]
    )
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)


class ProblemSetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    access_tier = SelectField(
        'Access Tier', choices=[('free', 'Free'), ('premium', 'Premium')]
    )
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)


class ProblemForm(FlaskForm):
    question_raw = TextAreaField('Question (supports LaTeX)', validators=[DataRequired()])
    problem_type = SelectField(
        'Type', choices=[('mcq', 'Multiple Choice'), ('fill_in_blank', 'Fill in the Blank'), ('frq', 'Free Response (FRQ)')]
    )
    correct_answer = StringField('Correct Answer (for fill-in-blank)', validators=[Optional()])
    difficulty = SelectField(
        'Difficulty', choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    )
    points = IntegerField('Points', default=1, validators=[NumberRange(min=1)])
    display_order = IntegerField('Display Order', default=0)


class AccessCodeForm(FlaskForm):
    code = StringField('Code (leave blank to auto-generate)', validators=[Optional(), Length(max=8)])
    tier = SelectField('Tier', choices=[('free', 'Free'), ('premium', 'Premium')])
    max_uses = IntegerField('Max Uses (leave blank for unlimited)', validators=[Optional()])
    expires_at = DateTimeLocalField('Expires At (optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])


class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    content_raw = TextAreaField('Content (Markdown + LaTeX)', validators=[Optional()])
    excerpt = StringField('Excerpt', validators=[Optional(), Length(max=500)])
    is_published = BooleanField('Published')


class ResourceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    resource_type = SelectField(
        'Type',
        choices=[
            ('google_slides', 'Google Slides'),
            ('google_docs', 'Google Docs'),
            ('video_link', 'Video Link'),
            ('pdf_link', 'PDF Link'),
            ('external_link', 'External Link'),
        ],
    )
    url = StringField('Sharing URL', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    access_tier = SelectField(
        'Access Tier', choices=[('free', 'Free'), ('premium', 'Premium')]
    )
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)


class TestimonialForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(max=100)])
    student_grade = StringField('Grade (e.g., 11th Grade)', validators=[Optional(), Length(max=50)])
    content = TextAreaField('Testimonial', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', default=5, validators=[NumberRange(min=1, max=5)])
    is_featured = BooleanField('Featured')
    is_active = BooleanField('Active', default=True)
