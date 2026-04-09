from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role          = db.Column(db.String(10), nullable=False, default='student')
    subject       = db.Column(db.String(100))
    class_level   = db.Column(db.String(20), nullable=True)  # e.g. "Class 5", "Class 10"
    points        = db.Column(db.Integer, default=0)
    level         = db.Column(db.String(20), default='Beginner')
    firebase_uid  = db.Column(db.String(200), nullable=True)   # ✅ FIXED: Google login ke liye
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    quiz_results  = db.relationship('QuizResult', backref='user', lazy=True)
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True)
    notes         = db.relationship('Note', backref='user', lazy=True)

class QuizResult(db.Model):
    __tablename__ = 'quiz_results'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject     = db.Column(db.String(50), nullable=False)
    score       = db.Column(db.Integer)
    total       = db.Column(db.Integer)
    percentage  = db.Column(db.Float)
    weak_topics = db.Column(db.Text)
    taken_at    = db.Column(db.DateTime, default=datetime.utcnow)

class LearningPath(db.Model):
    __tablename__ = 'learning_paths'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    path_data  = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    __tablename__ = 'badges'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id  = db.Column(db.String(50))
    name      = db.Column(db.String(100))
    icon      = db.Column(db.String(10))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

class Note(db.Model):
    __tablename__ = 'notes'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject     = db.Column(db.String(50))
    file_name   = db.Column(db.String(200))
    content     = db.Column(db.Text)
    ai_analysis = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class AINote(db.Model):
    __tablename__ = 'ai_notes'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject    = db.Column(db.String(50))
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role    = db.Column(db.String(10))
    content = db.Column(db.Text)
    subject = db.Column(db.String(50))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)