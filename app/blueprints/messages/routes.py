import logging
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app.blueprints.messages import messages_bp
from app.blueprints.messages.forms import ComposeForm, ReplyForm
from app.models.user import User
from app.models.messaging import MessageThread, MessageParticipant, Message
from app.extensions import db, limiter

logger = logging.getLogger(__name__)


@messages_bp.route('/')
@login_required
def inbox():
    # Get all threads where current user is a participant
    thread_ids = db.session.query(MessageParticipant.thread_id).filter_by(
        user_id=current_user.id
    ).subquery()

    threads = MessageThread.query.filter(
        MessageThread.id.in_(db.session.query(thread_ids.c.thread_id))
    ).order_by(MessageThread.updated_at.desc()).all()

    thread_data = []
    for thread in threads:
        latest = thread.messages.order_by(Message.created_at.desc()).first()
        unread = thread.messages.filter(
            Message.sender_id != current_user.id,
            Message.is_read == False,  # noqa: E712
        ).count()
        other_participants = MessageParticipant.query.filter(
            MessageParticipant.thread_id == thread.id,
            MessageParticipant.user_id != current_user.id,
        ).all()
        other_names = [p.user.username for p in other_participants if p.user]
        thread_data.append({
            'thread': thread,
            'latest': latest,
            'unread': unread,
            'other_names': ', '.join(other_names) or 'Unknown',
        })

    return render_template('messages/inbox.html', thread_data=thread_data)


@messages_bp.route('/thread/<thread_id>')
@login_required
def view_thread(thread_id):
    # Verify participation
    participant = MessageParticipant.query.filter_by(
        thread_id=thread_id, user_id=current_user.id
    ).first()
    if not participant:
        abort(403)

    thread = db.session.get(MessageThread, thread_id)
    if not thread:
        abort(404)

    # Mark unread messages as read
    unread = Message.query.filter(
        Message.thread_id == thread_id,
        Message.sender_id != current_user.id,
        Message.is_read == False,  # noqa: E712
    ).all()
    for msg in unread:
        msg.is_read = True
    if unread:
        db.session.commit()

    messages = thread.messages.order_by(Message.created_at.asc()).all()
    form = ReplyForm()

    return render_template('messages/thread.html', thread=thread, messages=messages, form=form)


@messages_bp.route('/thread/<thread_id>/reply', methods=['POST'])
@login_required
@limiter.limit("20/minute")
def reply_to_thread(thread_id):
    participant = MessageParticipant.query.filter_by(
        thread_id=thread_id, user_id=current_user.id
    ).first()
    if not participant:
        abort(403)

    thread = db.session.get(MessageThread, thread_id)
    if not thread:
        abort(404)

    form = ReplyForm()
    if form.validate_on_submit():
        msg = Message(
            thread_id=thread_id,
            sender_id=current_user.id,
            body=form.body.data.strip(),
        )
        db.session.add(msg)
        thread.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info('Message reply: user=%s, thread=%s', current_user.username, thread_id)
    else:
        flash('Message cannot be empty.', 'danger')

    return redirect(url_for('messages.view_thread', thread_id=thread_id))


@messages_bp.route('/compose', methods=['GET', 'POST'])
@login_required
@limiter.limit("10/minute", methods=["POST"])
def compose():
    form = ComposeForm()

    # Populate recipient choices based on role
    if current_user.is_admin:
        users = User.query.filter(
            User.id != current_user.id,
            User.is_active == True,  # noqa: E712
        ).order_by(User.username).all()
        form.recipient_id.choices = [(u.id, f'{u.username} ({u.role})') for u in users]
    else:
        # Students and parents can only message the admin
        admins = User.query.filter_by(role='admin').all()
        form.recipient_id.choices = [(a.id, f'{a.username} (Coach)') for a in admins]

    # Pre-select recipient from query param
    preset_to = request.args.get('to')
    if preset_to and request.method == 'GET':
        form.recipient_id.data = preset_to

    if form.validate_on_submit():
        recipient_id = form.recipient_id.data
        recipient = db.session.get(User, recipient_id)
        if not recipient:
            flash('Recipient not found.', 'danger')
            return render_template('messages/compose.html', form=form)

        # Create thread
        thread = MessageThread(subject=form.subject.data.strip())
        db.session.add(thread)
        db.session.flush()

        # Add participants
        for uid in [current_user.id, recipient_id]:
            p = MessageParticipant(thread_id=thread.id, user_id=uid)
            db.session.add(p)

        # Add first message
        msg = Message(
            thread_id=thread.id,
            sender_id=current_user.id,
            body=form.body.data.strip(),
        )
        db.session.add(msg)
        db.session.commit()

        logger.info('New message thread: from=%s, to=%s, subject=%s',
                    current_user.username, recipient.username, thread.subject)
        flash('Message sent!', 'success')
        return redirect(url_for('messages.view_thread', thread_id=thread.id))

    return render_template('messages/compose.html', form=form)
