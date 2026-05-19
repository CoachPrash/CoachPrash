import uuid
from datetime import datetime, timezone
from app.extensions import db


class MessageThread(db.Model):
    __tablename__ = 'message_threads'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages = db.relationship('Message', backref='thread', lazy='dynamic',
                               order_by='Message.created_at')
    participants = db.relationship('MessageParticipant', backref='thread', lazy='dynamic')

    def __repr__(self):
        return f'<MessageThread {self.subject}>'


class MessageParticipant(db.Model):
    __tablename__ = 'message_participants'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = db.Column(db.String(36), db.ForeignKey('message_threads.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)

    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint('thread_id', 'user_id', name='uq_thread_participant'),
    )

    def __repr__(self):
        return f'<MessageParticipant thread={self.thread_id} user={self.user_id}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = db.Column(db.String(36), db.ForeignKey('message_threads.id'), nullable=False, index=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', foreign_keys=[sender_id])

    def __repr__(self):
        return f'<Message {self.id} in thread {self.thread_id}>'
