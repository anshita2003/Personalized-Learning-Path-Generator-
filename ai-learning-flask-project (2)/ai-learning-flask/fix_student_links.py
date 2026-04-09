import os
import re

d = 'c:/Users/User/Desktop/ai-learning-flask-project (2)/ai-learning-flask/templates/student'

reps = {
    '"student_dashboard.html"': '"/student/dashboard"',
    '"{{ student_dashboard.html }}"': '"/student/dashboard"',
    '"student_profile.html"': '"/student/profile"',
    '"student_quiz.html"': '"/student/quiz/General"',
    '"student_subjects.html"': '"/student/subjects"',
    '"student_chatbot.html"': '"/student/chatbot"',
    '"student_path.html"': '"/student/path"',
    '"student_notes.html"': '"/student/notes"',
    '"login.html"': '"/logout"',
}

for root, dirs, files in os.walk(d):
    for fl in files:
        if fl.endswith('.html'):
            p = os.path.join(root, fl)
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    c = f.read()
                changed = False
                for k, v in reps.items():
                    if k in c:
                        c = c.replace(k, v)
                        changed = True
                if changed:
                    with open(p, 'w', encoding='utf-8') as f:
                        f.write(c)
                    print(f'Updated {fl}')
            except Exception as e:
                print(e)
