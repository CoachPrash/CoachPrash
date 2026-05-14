from flask_login import current_user


def can_access_concept(user, concept):
    """Check if user can access a concept based on tier."""
    if concept.access_tier == 'free':
        return True
    return user.is_authenticated and user.is_premium


def can_access_problem(user, problem_index):
    """Check if user can access a problem by its 0-based index in the set."""
    if user.is_authenticated and user.is_premium:
        return True
    return problem_index < 3


def can_access_hint(user, hint_index):
    """Check if user can access a hint by its 0-based index."""
    if user.is_authenticated and user.is_premium:
        return True
    return hint_index == 0


def can_access_solution(user):
    """Check if user can access step-by-step solutions."""
    return user.is_authenticated and user.is_premium


def can_track_progress(user):
    """Check if user can track learning progress."""
    return user.is_authenticated and user.is_premium


def register_access_helpers(app):
    """Register freemium access helpers as Jinja2 context processors."""
    @app.context_processor
    def inject_access_helpers():
        return dict(
            can_access_concept=can_access_concept,
            can_access_problem=can_access_problem,
            can_access_hint=can_access_hint,
            can_access_solution=can_access_solution,
            can_track_progress=can_track_progress,
        )
