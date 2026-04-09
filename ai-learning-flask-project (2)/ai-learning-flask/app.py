import os, json, re
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User, QuizResult, LearningPath, Badge, Note, AINote, ChatMessage
from database.seed_data import QUIZ_QUESTIONS, SUBJECTS, CLASS_LEVELS, CLASS_SUBJECTS
from ml.deep_model import (analyze_skills, predict_skill_level,
                            generate_learning_path, calculate_points,
                            get_level_from_points, check_badges)

# ── Firebase import ───────────────────────────────────────
from firebase_init import init_firebase, verify_token

# ── App setup ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ai-learning-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ai_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')

# ── Firebase initialize ───────────────────────────────────
init_firebase()

from genai_api import (
    call_general_ai, analyze_notes_api, chatbot_reply_api,
    generate_quiz_api, generate_learning_path_ai, generate_ai_notes
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Helpers ───────────────────────────────────────────────
def get_user_quiz_results(user_id):
    results = QuizResult.query.filter_by(user_id=user_id).all()
    return [{'subject': r.subject, 'score': r.score,
             'total': r.total, 'percentage': r.percentage,
             'taken_at': r.taken_at} for r in results]

def call_ai(prompt, system=None, max_tokens=800):
    return call_general_ai(prompt, system)

def update_user_progress(user):
    results = get_user_quiz_results(user.id)
    if not results:
        return
    scores = analyze_skills(results)
    level_name, conf, probs = predict_skill_level(scores)
    points = calculate_points(results)
    user.points = points
    user.level  = get_level_from_points(points)
    existing_path = LearningPath.query.filter_by(user_id=user.id).first()
    class_lvl = getattr(user, 'class_level', 'General')
    path = generate_learning_path_ai(scores, class_level=class_lvl)
    if existing_path:
        existing_path.path_data = json.dumps(path)
    else:
        db.session.add(LearningPath(user_id=user.id, path_data=json.dumps(path)))
    existing = [{'badge_id': b.badge_id, 'name': b.name,
                 'icon': b.icon} for b in Badge.query.filter_by(user_id=user.id).all()]
    new_badges = check_badges(results, existing)
    for b in new_badges:
        if not Badge.query.filter_by(user_id=user.id, badge_id=b['badge_id']).first():
            db.session.add(Badge(user_id=user.id, badge_id=b['badge_id'],
                                 name=b['name'], icon=b['icon']))
    db.session.commit()

# ══════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))

    if request.method == 'POST':
        # ✅ FIXED: Accept both JSON (from login.html fetch) and form POST
        is_json  = request.is_json
        data     = request.get_json() if is_json else request.form

        email    = data.get('email', '').strip()
        password = data.get('password', '')
        remember = data.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            redirect_url = url_for(f"{user.role}.dashboard")
            # ✅ JSON response for fetch call in login.html
            if is_json:
                return jsonify({'success': True, 'redirect': redirect_url})
            return redirect(redirect_url)

        # Wrong credentials
        if is_json:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        flash('Invalid email or password', 'error')

    return render_template('login.html', class_levels=CLASS_LEVELS)


# ── Firebase Google Login Route ────────────────────────────
@app.route('/firebase-login', methods=['POST'])
def firebase_login():
    if current_user.is_authenticated:
        return jsonify({'success': True, 'redirect': url_for(f"{current_user.role}.dashboard")})

    data = request.get_json() or {}
    email = data.get('email')
    firebase_uid = data.get('uid')
    name = data.get('name')
    role = data.get('role', 'student')

    if not email:
        return jsonify({'success': False, 'error': 'No email provided from Google Login'}), 400

    if not name:
        name = email.split('@')[0]

    user = User.query.filter_by(email=email).first()

    if not user:
        # Brand new user — needs to fill signup info
        return jsonify({
            'success': True,
            'needs_info': True,
            'email': email,
            'name': name,
            'uid': firebase_uid,
            'role': role
        })

    # Link firebase uid if not already linked
    if not user.firebase_uid:
        user.firebase_uid = firebase_uid
        db.session.commit()

    # Check if the existing user has an incomplete profile
    profile_incomplete = (
        not user.name or
        (user.role == 'student' and not user.class_level) or
        (user.role == 'teacher' and not getattr(user, 'subject', None))
    )

    if profile_incomplete:
        return jsonify({
            'success': True,
            'needs_info': True,
            'email': email,
            'name': user.name or name,
            'uid': firebase_uid,
            'role': user.role   # keep their existing role
        })

    login_user(user, remember=True)
    return jsonify({
        'success': True,
        'redirect': url_for(f"{user.role}.dashboard")
    })

@app.route('/firebase-register', methods=['POST'])
def firebase_register():
    data = request.get_json() or {}
    email = data.get('email')
    name = data.get('name')
    uid = data.get('uid')
    role = data.get('role', 'student')
    subject = data.get('subject', '')
    class_level = data.get('class_level', '')

    if not email or not name:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Create brand new user
        random_pwd = os.urandom(24).hex()
        user = User(
            name=name, email=email,
            password_hash=generate_password_hash(random_pwd),
            role=role, firebase_uid=uid,
            subject=subject,
            class_level=class_level if role == 'student' else None
        )
        db.session.add(user)
    else:
        # Update existing user's incomplete profile
        user.name = name
        user.role = role
        if not user.firebase_uid:
            user.firebase_uid = uid
        if role == 'student':
            user.class_level = class_level
            user.subject = ''
        else:
            user.subject = subject
            user.class_level = None

    db.session.commit()
    login_user(user, remember=True)
    return jsonify({
        'success': True,
        'redirect': url_for(f"{user.role}.dashboard")
    })

@app.route('/signup', methods=['GET'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))
    return render_template('login.html', active_tab='signup', class_levels=CLASS_LEVELS)

@app.route('/register', methods=['POST'])
def register():
    # ✅ FIXED: Accept both JSON (from login.html fetch) and form POST
    is_json  = request.is_json
    data     = request.get_json() if is_json else request.form

    name        = data.get('name', '').strip()
    email       = data.get('email', '').strip()
    password    = data.get('password', '')
    role        = data.get('role', 'student')
    subject     = data.get('subject', '')
    class_level = data.get('class_level', '').strip()

    if User.query.filter_by(email=email).first():
        if is_json:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        flash('Email already registered', 'error')
        return redirect(url_for('login'))

    user = User(name=name, email=email,
                password_hash=generate_password_hash(password),
                role=role, subject=subject, class_level=class_level if role=='student' else None)
    db.session.add(user)
    db.session.commit()

    if is_json:
        return jsonify({'success': True, 'message': 'Account created! Please log in.'})
        
    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ══════════════════════════════════════════════════════════
# STUDENT BLUEPRINT
# ══════════════════════════════════════════════════════════
from flask import Blueprint
student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
def student_auth():
    # ✅ FIXED: Manually check auth instead of stacking @login_required
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'student':
        return redirect(url_for('teacher.dashboard'))

@student_bp.route('/dashboard')
def dashboard():
    results    = get_user_quiz_results(current_user.id)
    scores     = analyze_skills(results) if results else {}
    level_name, conf, probs = predict_skill_level(scores)
    badges     = Badge.query.filter_by(user_id=current_user.id).all()
    path_row   = LearningPath.query.filter_by(user_id=current_user.id).first()
    weak       = sorted([(s,v) for s,v in scores.items() if v < 60], key=lambda x: x[1])
    return render_template('student/student_dashboard.html',
        user=current_user, results=results[:6], scores=scores,
        level_name=level_name, conf=round(conf*100), probs=probs,
        badges=badges, weak_topics=weak,
        path=json.loads(path_row.path_data) if path_row else [])

@student_bp.route('/subjects')
def subjects():
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results) if results else {}
    return render_template('student/student_subjects.html',
        user=current_user, subjects=SUBJECTS, scores=scores)

@student_bp.route('/api/generate-quiz')
def api_generate_quiz():
    subject_id  = request.args.get('subject', 'math')
    class_level = getattr(current_user, 'class_level', None) or 'Class 8'

    # Map subject ID → full name for AI
    from genai_api import _subject_full_name
    full_subject = _subject_full_name(subject_id)

    response = generate_quiz_api(full_subject, class_level)
    if response:
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()
        try:
            questions = json.loads(cleaned)
            if isinstance(questions, list) and len(questions) > 0:
                return jsonify({'success': True, 'questions': questions[:5], 'ai': True})
        except Exception as e:
            print("Failed to parse AI quiz JSON:", e)
            print("AI Response was:", response[:500])

    # Fallback to seed data if AI fails
    from database.seed_data import QUIZ_QUESTIONS
    fallback = QUIZ_QUESTIONS.get(full_subject, [])
    if not fallback:
        # Try partial match
        for k, v in QUIZ_QUESTIONS.items():
            if subject_id.lower() in k.lower() or k.lower().startswith(subject_id.lower()[:4]):
                fallback = v
                break
    formatted = [{'q': q['q'], 'o': q['opts'], 'a': int(q['ans'])} for q in fallback]
    return jsonify({'success': False, 'questions': formatted, 'ai': False})

@student_bp.route('/quiz/<subject>')
def quiz(subject):
    class_level = getattr(current_user, 'class_level', None) or 'Class 8'
    # Filter subjects available for this student's class level
    allowed_ids = CLASS_SUBJECTS.get(class_level, [s['id'] for s in SUBJECTS])
    class_subjects = [s for s in SUBJECTS if s['id'] in allowed_ids]
    # Fallback: if class map doesn't match, show all
    if not class_subjects:
        class_subjects = SUBJECTS
    return render_template('student/student_quiz.html',
        user=current_user, subject=subject,
        subjects=class_subjects, class_level=class_level)

@student_bp.route('/quiz/submit', methods=['POST'])
def quiz_submit():
    data       = request.get_json()
    subject    = data.get('subject')
    score      = int(data.get('score', 0))
    total      = int(data.get('total', 5))
    percentage = round((score / total) * 100) if total else 0
    weak       = data.get('weak', [])
    
    qr = QuizResult(user_id=current_user.id, subject=subject,
                    score=score, total=total, percentage=percentage,
                    weak_topics=json.dumps(weak))
    db.session.add(qr)
    db.session.commit()
    update_user_progress(current_user)
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results)
    level_name, conf, _ = predict_skill_level(scores)
    return jsonify({'score': score, 'total': total, 'percentage': percentage, 'level': level_name})

@student_bp.route('/path')
def path():
    # Always regenerate path fresh from AI based on latest quiz results
    results   = get_user_quiz_results(current_user.id)
    scores    = analyze_skills(results) if results else {}
    class_lvl = getattr(current_user, 'class_level', None) or 'Class 8'

    # Generate fresh AI path
    ai_path = generate_learning_path_ai(scores, class_level=class_lvl)

    # Save/update in DB
    path_row = LearningPath.query.filter_by(user_id=current_user.id).first()
    if path_row:
        path_row.path_data  = json.dumps(ai_path)
        path_row.updated_at = __import__('datetime').datetime.utcnow()
    else:
        db.session.add(LearningPath(user_id=current_user.id, path_data=json.dumps(ai_path)))
    db.session.commit()

    return render_template('student/student_path.html', user=current_user,
        path=ai_path, class_level=class_lvl)

@student_bp.route('/ai-notes/<subject>')
def ai_notes(subject):
    class_level = getattr(current_user, 'class_level', None) or 'Class 8'
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results)
    score   = scores.get(subject, 50)

    # Always generate fresh AI notes (delete old cached version)
    existing = AINote.query.filter_by(user_id=current_user.id, subject=subject).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    notes = generate_ai_notes(subject, class_level=class_level, score=score, role='student')
    if not notes:
        notes = f'## {subject}\n\n*AI notes unavailable right now. Please try again.*'

    db.session.add(AINote(user_id=current_user.id, subject=subject, notes=notes))
    db.session.commit()
    return jsonify({'notes': notes})

@student_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        subject  = request.form.get('subject', '')
        file     = request.files.get('file')
        if file and file.filename:
            content  = file.read().decode('utf-8', errors='ignore')
            analysis = analyze_notes_api(content[:3000]) or 'Add Gemini API key.'
            db.session.add(Note(user_id=current_user.id, subject=subject,
                                file_name=file.filename, content=content[:5000],
                                ai_analysis=analysis))
            db.session.commit()
        return redirect(url_for('student.notes'))
    all_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return render_template('student/student_notes.html', user=current_user,
        notes=all_notes, subjects=SUBJECTS)

@student_bp.route('/chatbot')
def chatbot():
    history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.sent_at).all()
    return render_template('student/student_chatbot.html', user=current_user,
        history=history, subjects=SUBJECTS)

@student_bp.route('/chatbot/send', methods=['POST'])
def chatbot_send():
    data       = request.get_json()
    msg        = data.get('message', '').strip()
    subject    = data.get('subject', 'General')
    class_level = getattr(current_user, 'class_level', None) or 'Class 8'
    reply = chatbot_reply_api(msg, subject=subject, role='student', class_level=class_level)
    db.session.add(ChatMessage(user_id=current_user.id, role='user', content=msg, subject=subject))
    db.session.add(ChatMessage(user_id=current_user.id, role='assistant', content=reply, subject=subject))
    db.session.commit()
    return jsonify({'reply': reply})

@student_bp.route('/profile')
def profile():
    results  = get_user_quiz_results(current_user.id)
    scores   = analyze_skills(results) if results else {}
    level_name, conf, probs = predict_skill_level(scores)
    badges   = Badge.query.filter_by(user_id=current_user.id).all()
    path_row = LearningPath.query.filter_by(user_id=current_user.id).first()
    return render_template('student/student_profile.html', user=current_user,
        results=results, scores=scores, level_name=level_name,
        conf=round(conf*100), probs=probs, badges=badges,
        path=json.loads(path_row.path_data) if path_row else [])

app.register_blueprint(student_bp)

# ══════════════════════════════════════════════════════════
# TEACHER BLUEPRINT
# ══════════════════════════════════════════════════════════
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.before_request
def teacher_auth():
    # ✅ FIXED: Manually check auth instead of stacking @login_required
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'teacher':
        return redirect(url_for('student.dashboard'))

@teacher_bp.route('/dashboard')
def dashboard():
    results  = get_user_quiz_results(current_user.id)
    scores   = analyze_skills(results) if results else {}
    level_name, conf, probs = predict_skill_level(scores)
    badges   = Badge.query.filter_by(user_id=current_user.id).all()
    path_row = LearningPath.query.filter_by(user_id=current_user.id).first()
    weak     = sorted([(s,v) for s,v in scores.items() if v < 60], key=lambda x: x[1])
    return render_template('teacher/teacher_dashboard.html',
        user=current_user, results=results[:6], scores=scores,
        level_name=level_name, conf=round(conf*100), probs=probs,
        badges=badges, weak_topics=weak,
        path=json.loads(path_row.path_data) if path_row else [])

@teacher_bp.route('/students')
def students():
    return render_template('teacher/teacher_students.html', user=current_user)

@teacher_bp.route('/reports')
def reports():
    return render_template('teacher/teacher_reports.html', user=current_user)

@teacher_bp.route('/subjects')
def subjects():
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results) if results else {}
    return render_template('teacher/teacher_subjects.html',
        user=current_user, subjects=SUBJECTS, scores=scores)

@teacher_bp.route('/quiz/<subject>')
def quiz(subject):
    # For teachers, we still fetch questions to show them in the manage list
    questions = QUIZ_QUESTIONS.get(subject, [])
    return render_template('teacher/teacher_quiz.html',
        user=current_user, subject=subject, questions=questions, subjects=SUBJECTS)

@teacher_bp.route('/quiz/submit', methods=['POST'])
def quiz_submit():
    data       = request.get_json()
    subject    = data.get('subject')
    score      = int(data.get('score', 0))
    total      = int(data.get('total', 5))
    percentage = round((score / total) * 100) if total else 0
    weak       = data.get('weak', [])
    
    qr = QuizResult(user_id=current_user.id, subject=subject,
                    score=score, total=total, percentage=percentage,
                    weak_topics=json.dumps(weak))
    db.session.add(qr)
    db.session.commit()
    update_user_progress(current_user)
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results)
    level_name, conf, _ = predict_skill_level(scores)
    return jsonify({'score': score, 'total': total, 'percentage': percentage, 'level': level_name})

@teacher_bp.route('/path')
def path():
    path_row = LearningPath.query.filter_by(user_id=current_user.id).first()
    return render_template('teacher/teacher_path.html', user=current_user,
        path=json.loads(path_row.path_data) if path_row else [])

@teacher_bp.route('/ai-notes/<subject>')
def ai_notes(subject):
    class_level = 'Class 10'  # default for teachers
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results)
    score   = scores.get(subject, 50)

    existing = AINote.query.filter_by(user_id=current_user.id, subject=subject).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    notes = generate_ai_notes(subject, class_level=class_level, score=score, role='teacher')
    if not notes:
        notes = f'## {subject}\n\n*AI notes unavailable right now. Please try again.*'

    db.session.add(AINote(user_id=current_user.id, subject=subject, notes=notes))
    db.session.commit()
    return jsonify({'notes': notes})

@teacher_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        subject  = request.form.get('subject', '')
        file     = request.files.get('file')
        if file and file.filename:
            content  = file.read().decode('utf-8', errors='ignore')
            analysis = analyze_notes_api(content[:3000]) or 'Add Gemini API key.'
            db.session.add(Note(user_id=current_user.id, subject=subject,
                                file_name=file.filename, content=content[:5000],
                                ai_analysis=analysis))
            db.session.commit()
        return redirect(url_for('teacher.notes'))
    all_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return render_template('teacher/teacher_notes.html', user=current_user,
        notes=all_notes, subjects=SUBJECTS)

@teacher_bp.route('/chatbot')
def chatbot():
    history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.sent_at).all()
    return render_template('teacher/teacher_chatbot.html', user=current_user,
        history=history, subjects=SUBJECTS)

@teacher_bp.route('/chatbot/send', methods=['POST'])
def chatbot_send():
    data    = request.get_json()
    msg     = data.get('message', '').strip()
    subject = data.get('subject', 'General')
    reply = chatbot_reply_api(msg, subject=subject, role='teacher', class_level='Advanced')
    db.session.add(ChatMessage(user_id=current_user.id, role='user', content=msg, subject=subject))
    db.session.add(ChatMessage(user_id=current_user.id, role='assistant', content=reply, subject=subject))
    db.session.commit()
    return jsonify({'reply': reply})

@teacher_bp.route('/profile')
def profile():
    results  = get_user_quiz_results(current_user.id)
    scores   = analyze_skills(results) if results else {}
    level_name, conf, probs = predict_skill_level(scores)
    badges   = Badge.query.filter_by(user_id=current_user.id).all()
    path_row = LearningPath.query.filter_by(user_id=current_user.id).first()
    return render_template('teacher/teacher_profile.html', user=current_user,
        results=results, scores=scores, level_name=level_name,
        conf=round(conf*100), badges=badges,
        path=json.loads(path_row.path_data) if path_row else [])

app.register_blueprint(teacher_bp)

@app.route('/<role>/<path:filename>')
def legacy_html_redirect(role, filename):
    if role in ['student', 'teacher'] and filename.endswith('.html'):
        name = filename.replace(f"{role}_", "").replace('.html', '')
        if name == 'quiz': return redirect(url_for(f"{role}.quiz", subject='General'))
        try: return redirect(url_for(f"{role}.{name}"))
        except: pass
    return "Not Found", 404

# ── Init DB ───────────────────────────────────────────────
with app.app_context():
    db.create_all()

# ══════════════════════════════════════════════════════════
# CLEAN REST API ROUTES
# ══════════════════════════════════════════════════════════

# ── /api/test-ai — Verify Gemini is connected ────────────
@app.route('/api/test-ai')
def test_ai():
    try:
        result = call_general_ai("Say: AI is working! (one sentence only)")
        return jsonify({'status': 'ok', 'response': result, 'model': 'gemini-2.0-flash'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ── /api/subjects — Class-based subject list ─────────────
@app.route('/api/subjects')
@login_required
def api_subjects():
    """Returns subjects filtered by logged-in student's class level."""
    class_level = request.args.get('class_level') or getattr(current_user, 'class_level', None) or 'Class 8'
    from database.seed_data import CLASS_SUBJECTS, SUBJECTS
    allowed_ids = CLASS_SUBJECTS.get(class_level, [s['id'] for s in SUBJECTS])
    class_subjects = [s for s in SUBJECTS if s['id'] in allowed_ids]
    if not class_subjects:
        class_subjects = SUBJECTS
    return jsonify({
        'class_level': class_level,
        'subjects': class_subjects
    })

# ── /api/ai-notes — AI Notes generation ─────────────────
@app.route('/api/ai-notes')
@login_required
def api_ai_notes():
    """Generate AI notes for a given subject and class."""
    subject    = request.args.get('subject', 'Mathematics')
    class_level = request.args.get('class_level') or getattr(current_user, 'class_level', None) or 'Class 8'
    results = get_user_quiz_results(current_user.id)
    scores  = analyze_skills(results)
    score   = scores.get(subject, 50)
    notes   = generate_ai_notes(subject, class_level=class_level, score=score, role=current_user.role)
    return jsonify({
        'subject': subject,
        'class_level': class_level,
        'notes': notes,
        'score': score
    })

# ── /api/learning-path — AI Learning Path ───────────────
@app.route('/api/learning-path')
@login_required
def api_learning_path():
    """Returns AI-generated learning path for logged-in student."""
    results   = get_user_quiz_results(current_user.id)
    scores    = analyze_skills(results) if results else {}
    class_lvl = getattr(current_user, 'class_level', None) or 'Class 8'
    path      = generate_learning_path_ai(scores, class_level=class_lvl)
    return jsonify({
        'class_level': class_lvl,
        'path': path,
        'based_on': scores
    })

# ── /api/chat — AI Chatbot ───────────────────────────────
@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """AI chatbot endpoint for both students and teachers."""
    data       = request.get_json() or {}
    message    = data.get('message', '').strip()
    subject    = data.get('subject', 'General')
    class_level = getattr(current_user, 'class_level', None) or 'Class 8'
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    reply = chatbot_reply_api(message, subject=subject, role=current_user.role, class_level=class_level)
    return jsonify({'reply': reply, 'subject': subject})

# ── /api/analyze-notes — Notes analyzer ─────────────────
@app.route('/api/analyze-notes', methods=['POST'])
@login_required
def api_analyze_notes():
    """Analyzes uploaded note content using AI."""
    data    = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    analysis = analyze_notes_api(content[:3000])
    return jsonify({'analysis': analysis})

if __name__ == '__main__':
    app.run(debug=True, port=5000)