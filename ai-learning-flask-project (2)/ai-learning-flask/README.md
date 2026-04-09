# AI Learning Path — Flask Project
## Team: Aman Kumar, Anshita Goel, Darpan Yaduvanshi | UIC | Mrs. Ashima Sood

---

## ✅ PROBLEM SOLVED: Login → Dashboard Redirect

### KAISE KAAM KARTA HAI (Flow):

```
Student login kare
    ↓
app.py /login route → DB mein user check kare
    ↓
user.role == 'student'? → /student/dashboard
user.role == 'teacher'? → /teacher/dashboard
```

---

## 🚀 CHALANE KE STEPS

### Step 1 — Install packages
```bash
pip install -r requirements.txt
```

### Step 2 — Run karo
```bash
python app.py
```

### Step 3 — Browser mein kholo
```
http://localhost:5000
```

### Step 4 — Demo accounts se login karo

| Role | Email | Password |
|------|-------|----------|
| 👨‍🎓 Student | student@demo.com | demo123 |
| 👩‍🏫 Teacher | teacher@demo.com | demo123 |

---

## 📁 FILE STRUCTURE

```
flask-project/
├── app.py                          ← Main file (routes + DB)
├── requirements.txt
├── templates/
│   ├── login.html                  ← Login + Signup page
│   ├── student/
│   │   ├── dashboard.html          ← Student dashboard
│   │   ├── subjects.html
│   │   ├── quiz.html
│   │   ├── path.html
│   │   ├── notes.html
│   │   ├── chatbot.html
│   │   └── profile.html
│   └── teacher/
│       ├── dashboard.html          ← Teacher dashboard
│       ├── students.html
│       ├── quiz.html
│       ├── reports.html
│       ├── chatbot.html
│       └── profile.html
└── instance/
    └── learning.db                 ← Auto-banta hai
```

---

## 🔑 ROLE-BASED REDIRECT (app.py mein)

```python
# Login ke baad yeh code check karta hai:

if user.role == 'teacher':
    return redirect(url_for('teacher_dashboard'))  # → /teacher/dashboard
else:
    return redirect(url_for('student_dashboard'))   # → /student/dashboard
```

---

## ⚠️ COMMON PROBLEMS & FIXES

| Problem | Fix |
|---------|-----|
| "student login ke baad dashboard nahi khulta" | Role hidden input sahi hai? `<input name="role" value="student">` |
| "teacher ka dashboard student ko dikh raha hai" | `@login_required(role='student')` decorator lagao |
| "login ke baad same page pe reh jaata hai" | `return redirect(url_for('student_dashboard'))` check karo |
| DB error | `python app.py` dobara chalao — DB auto-create hoga |

---

## 🔥 CLAUDE API KEY (optional)

`.env` file banao:
```
CLAUDE_API_KEY=sk-ant-...apni-key...
```

Bina API key ke bhi sab features kaam karenge except AI chatbot/notes.
