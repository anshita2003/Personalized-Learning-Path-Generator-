"""
Deep Learning Skill Analyzer
Neural Network: Input(6 subjects) -> Hidden Layers -> Output(4 skill levels)
Beginner / Intermediate / Advanced / Expert
"""
import numpy as np
import os
import json

# Try TensorFlow, fallback to rule-based
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

SUBJECTS = [
    'Data Science', 'Artificial Intelligence',
    'Machine Learning', 'SQL & Databases',
    'Generative AI', 'Deep Learning'
]
LEVELS    = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'skill_model.h5')

# ── Build Deep Learning Model ──────────────────────
def build_model():
    model = keras.Sequential([
        layers.Input(shape=(6,)),
        layers.Dense(64, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(4, activation='softmax')
    ])
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

# ── Generate synthetic training data ───────────────
def generate_training_data(n=3000):
    X, y = [], []
    for _ in range(n):
        level = np.random.randint(0, 4)
        if level == 0:   base = np.random.uniform(0,  40, 6)
        elif level == 1: base = np.random.uniform(35, 65, 6)
        elif level == 2: base = np.random.uniform(60, 85, 6)
        else:            base = np.random.uniform(78,100, 6)
        noise = np.random.uniform(-8, 8, 6)
        scores = np.clip(base + noise, 0, 100)
        X.append(scores / 100.0)
        y.append(level)
    return np.array(X), np.array(y)

# ── Train and save model ────────────────────────────
def train_and_save():
    if not TF_AVAILABLE:
        print("TensorFlow not available — using rule-based model")
        return False
    print("Training Deep Learning model...")
    X, y = generate_training_data(3000)
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    model = build_model()
    model.fit(
        X_train, y_train,
        epochs=30, batch_size=32,
        validation_data=(X_val, y_val),
        verbose=1
    )
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return True

# ── Load model ──────────────────────────────────────
_model = None
def load_model():
    global _model
    if _model is not None:
        return _model
    if TF_AVAILABLE and os.path.exists(MODEL_PATH):
        _model = keras.models.load_model(MODEL_PATH)
    return _model

# ── Rule-based fallback ─────────────────────────────
def rule_based_level(avg_score):
    if avg_score >= 80: return 3
    if avg_score >= 65: return 2
    if avg_score >= 45: return 1
    return 0

# ── Predict skill level ─────────────────────────────
def predict_skill_level(scores_dict):
    """
    scores_dict: {'Data Science': 72, 'Machine Learning': 58, ...}
    Returns: level_string, confidence_float, all_probs_list
    """
    vector = [scores_dict.get(s, 0) for s in SUBJECTS]
    avg    = np.mean([v for v in vector if v > 0]) if any(vector) else 0

    model = load_model()
    if model is not None:
        arr   = np.array(vector).reshape(1, -1) / 100.0
        probs = model.predict(arr, verbose=0)[0]
        level_idx = int(np.argmax(probs))
        confidence = float(probs[level_idx])
    else:
        level_idx  = rule_based_level(avg)
        confidence = 0.85
        probs      = [0.0] * 4
        probs[level_idx] = confidence

    return LEVELS[level_idx], confidence, probs if isinstance(probs, list) else probs.tolist()

# ── Analyze all quiz results ────────────────────────
def analyze_skills(quiz_results):
    """quiz_results: list of dicts with 'subject' and 'percentage'"""
    subject_data = {}
    for r in quiz_results:
        s = r['subject']
        if s not in subject_data:
            subject_data[s] = []
        subject_data[s].append(r['percentage'])
    return {s: round(sum(v)/len(v)) for s, v in subject_data.items()}

# ── Generate learning path ──────────────────────────
def generate_learning_path(scores):
    path = []
    for subject, score in sorted(scores.items(), key=lambda x: x[1]):
        if score < 60:
            priority = 'high'
            steps = [
                f'Read AI-generated notes for {subject}',
                'Watch introductory videos',
                'Solve 10 practice problems',
                f'Retake {subject} quiz'
            ]
        elif score < 75:
            priority = 'medium'
            steps = [
                'Review advanced concepts',
                'Solve 5 challenging problems',
                'Retake quiz'
            ]
        else:
            priority = 'low'
            steps = ['Explore advanced topics', 'Teach others']
        path.append({'subject': subject, 'score': score,
                     'priority': priority, 'steps': steps,
                     'completed': False})
    return path

# ── Points and badges ───────────────────────────────
def calculate_points(quiz_results):
    total = 0
    for r in quiz_results:
        p = r['percentage']
        if p >= 90: total += 100
        elif p >= 75: total += 70
        elif p >= 60: total += 40
        else: total += 10
    return total

def get_level_from_points(points):
    if points >= 1000: return 'Expert'
    if points >= 500:  return 'Advanced'
    if points >= 200:  return 'Intermediate'
    return 'Beginner'

def check_badges(quiz_results, existing_badges):
    earned = list(existing_badges)
    ids    = [b['badge_id'] for b in earned]
    def add(bid, name, icon, desc):
        if bid not in ids:
            earned.append({'badge_id': bid, 'name': name,
                           'icon': icon, 'desc': desc})
    if len(quiz_results) >= 1:
        add('first-quiz', 'Quiz Starter', '🎯', 'Completed first quiz')
    if len(quiz_results) >= 5:
        add('5-quizzes', 'Quiz Warrior', '⚔️', '5 quizzes completed')
    if len(quiz_results) >= 10:
        add('10-quizzes', 'Quiz Master', '🏆', '10 quizzes completed')
    if any(r['percentage'] == 100 for r in quiz_results):
        add('perfect', 'Perfect Score', '💯', 'Scored 100%')
    strong = [r for r in quiz_results if r['percentage'] >= 80]
    if len(set(r['subject'] for r in strong)) >= 3:
        add('tri-master', 'Tri-Master', '🌟', '3 subjects mastered')
    return earned

if __name__ == '__main__':
    train_and_save()
