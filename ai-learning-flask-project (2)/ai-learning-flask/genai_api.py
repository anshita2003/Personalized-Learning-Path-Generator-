"""
genai_api.py — Gemini AI Agent for AI Learning Platform
=========================================================
Uses: google-genai (NEW official SDK — replaces deprecated google-generativeai)
Powers:
  1. Quiz Generator      — Auto-generates class-level MCQs
  2. Learning Path AI    — Personalized path from quiz scores
  3. AI Notes Generator  — Smart study notes per subject
  4. AI Chatbot          — Doubt-clearing tutor agent
  5. Note Analyzer       — Analyzes uploaded student notes
"""

import os
import json
import re
import random
import requests

# ── Load API Key ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBC9zZZDuYB48G9i3H-3bqSLoMBYbwScOQ")
GEMINI_MODEL = "gemini-flash-latest"

print(f"[Gemini] Using Direct REST API with model: {GEMINI_MODEL}")

# ─────────────────────────────────────────────────────────────────────────────
# CORE CALL — Direct REST API Call (No SDK needed, bypasses all pip errors)
# ─────────────────────────────────────────────────────────────────────────────
def call_general_ai(prompt, system=None, return_error=False):
    """Directly calls the Gemini REST API avoiding package dependencies."""
    if not GEMINI_API_KEY:
        err = "API Key is missing in .env!"
        print(f"[Gemini Error] {err}")
        return err if return_error else None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    if system:
        payload["system_instruction"] = {
            "parts": [{"text": system}]
        }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            try:
                err_data = response.json()
                msg = err_data.get('error', {}).get('message', str(response.text))
            except:
                msg = response.text
            err = f"API Error {response.status_code}: {msg}"
            print(f"[Gemini Error] {err}")
            return err if return_error else None
            
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            err = f"Unexpected response format: {data}"
            print(f"[Gemini REST Error] {err}")
            return err if return_error else None
            
    except Exception as e:
        err = f"Network Exception: {str(e)}"
        print(f"[Gemini REST Exception] {err}")
        return err if return_error else None


# ── Clean JSON helper ─────────────────────────────────────────────────────────
def _clean_json(text):
    if not text:
        return text
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()


# ── Subject ID → Full Name mapping ───────────────────────────────────────────
SUBJECT_NAMES = {
    'math':    'Mathematics',
    'science': 'Science',
    'english': 'English',
    'history': 'History',
    'geo':     'Geography',
    'cs':      'Computer Science',
    'evs':     'Environmental Studies',
    'social':  'Social Studies',
    'Mathematics':      'Mathematics',
    'Science':          'Science',
    'English':          'English',
    'History':          'History',
    'Geography':        'Geography',
    'Computer Science': 'Computer Science',
    'General':          'General Knowledge',
}

def _subject_full_name(subject_id):
    return SUBJECT_NAMES.get(subject_id, subject_id)


# ... (Keeping Quiz and Path Generators same) ...

# ══════════════════════════════════════════════════════════════════════════════
# 1. QUIZ GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_quiz_api(subject, class_level="Class 8"):
    full_subject = _subject_full_name(subject)
    topic_seeds = ["core concepts", "application problems", "tricky questions", "real-life examples", "NCERT based"]
    seed_topic = random.choice(topic_seeds)

    system = f"""You are an expert educational quiz maker for Indian school students.
Generate exactly 5 UNIQUE multiple-choice questions about '{full_subject}' for a student in '{class_level}'.
Focus on: {seed_topic}
Rules:
- Each question MUST be different — no repeats
- Adjust difficulty: Class 1-5 = basic, Class 6-8 = NCERT, Class 9-10 = board level, Class 11-12 = advanced
- All 4 options must be plausible
- The correct answer must be factually correct
Output ONLY a valid JSON array. NO markdown.
Format: [{{"q":"Question?","o":["A","B","C","D"],"a":2}}]"""

    prompt = f"Generate 5 unique {seed_topic} MCQ questions for {full_subject}, {class_level} student."
    return call_general_ai(prompt, system=system)


# ══════════════════════════════════════════════════════════════════════════════
# 2. LEARNING PATH GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_learning_path_ai(scores, class_level="Class 8"):
    if not scores: return _default_starter_path(class_level)
    system = f"""You are an AI learning coach for a {class_level} student. Create a PERSONALIZED learning path.
Priority: 0-39=critical, 40-59=high, 60-74=medium, 75-89=low, 90-100=mastered
Output ONLY a valid JSON array. NO markdown."""
    prompt = f"Scores: {json.dumps(scores)}\nGenerate path."
    try:
        text = call_general_ai(prompt, system=system)
        if text: return json.loads(_clean_json(text))
    except Exception: pass
    return _rule_based_path(scores)

def _default_starter_path(class_level):
    return [{"subject": "Math", "score": 0, "priority": "high", "status": "Take a quiz to unlock path!", "steps": ["Attempt a quiz"], "completed": False}]

def _rule_based_path(scores):
    return [{"subject": k, "score": v, "priority": "medium", "status": "Revise basics", "steps": ["Practice problems"], "completed": False} for k, v in scores.items()]


# ══════════════════════════════════════════════════════════════════════════════
# 3. AI NOTES GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_ai_notes(subject, class_level="Class 8", score=50, role="student"):
    full_subject = _subject_full_name(subject)
    system = f"""You are an educational content writer. Generate notes for '{full_subject}', '{class_level}' student (Score: {score}%). Use Markdown."""
    prompt = f"Write notes for '{full_subject}'."
    res = call_general_ai(prompt, system=system, return_error=True)
    return res if res else f"## {full_subject}\n\n*Error generating notes.*"


# ══════════════════════════════════════════════════════════════════════════════
# 4. AI CHATBOT
# ══════════════════════════════════════════════════════════════════════════════
def chatbot_reply_api(message, subject="General", role="student", class_level="Class 8"):
    """AI tutor chatbot that passes exactly what Google says back to UI."""
    full_subject = _subject_full_name(subject)
    system = f"""You are a friendly AI tutor helping a {role} studying {full_subject} at {class_level} level. Be encouraging and give step-by-step math explanations."""
    
    result = call_general_ai(message, system=system, return_error=True)
    # Return whatever Google's API returned (either the AI answer, or the 429 Quota Exceeded error message)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 5. NOTE ANALYZER
# ══════════════════════════════════════════════════════════════════════════════
def analyze_notes_api(content):
    system = """Analyze notes. Format: ## Summary, ## Key Concepts, ## Missing Areas, ## Suggestions."""
    prompt = f"Analyze:\n{content}"
    res = call_general_ai(prompt, system=system, return_error=True)
    return res if res else "Could not analyze notes."
