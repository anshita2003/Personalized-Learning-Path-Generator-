import os
import re

d = 'c:/Users/User/Desktop/ai-learning-flask-project (2)/ai-learning-flask/templates/teacher'

reps = {
    '"teacher_dashboard.html"': '"/teacher/dashboard"',
    '"{{ teacher_dashboard.html }}"': '"/teacher/dashboard"',
    '"teacher_profile.html"': '"/teacher/profile"',
    '"teacher_quiz.html"': '"/teacher/quiz/General"',
    '"teacher_reports.html"': '"/teacher/reports"',
    '"teacher_students.html"': '"/teacher/students"',
    '"teacher_chatbot.html"': '"/teacher/chatbot"',
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
