# Classes available for student signup
CLASS_LEVELS = [f"Class {i}" for i in range(1, 13)]

# Maps class ranges to which subject IDs are appropriate
CLASS_SUBJECTS = {
    'Class 1':  ['math', 'english', 'science'],
    'Class 2':  ['math', 'english', 'science'],
    'Class 3':  ['math', 'english', 'science', 'evs'],
    'Class 4':  ['math', 'english', 'science', 'evs'],
    'Class 5':  ['math', 'english', 'science', 'social'],
    'Class 6':  ['math', 'english', 'science', 'history', 'geo'],
    'Class 7':  ['math', 'english', 'science', 'history', 'geo'],
    'Class 8':  ['math', 'english', 'science', 'history', 'geo', 'cs'],
    'Class 9':  ['math', 'english', 'science', 'history', 'geo', 'cs'],
    'Class 10': ['math', 'english', 'science', 'history', 'geo', 'cs'],
    'Class 11': ['math', 'science', 'cs', 'english', 'history', 'geo'],
    'Class 12': ['math', 'science', 'cs', 'english', 'history', 'geo'],
}

SUBJECTS = [
    {'id': 'math',    'name': 'Mathematics',      'icon': '📐', 'color': '#6366f1', 'desc': 'Numbers, algebra, geometry'},
    {'id': 'science', 'name': 'Science',           'icon': '🔬', 'color': '#059669', 'desc': 'Physics, chemistry, biology'},
    {'id': 'english', 'name': 'English',           'icon': '📖', 'color': '#f59e0b', 'desc': 'Grammar, reading, writing'},
    {'id': 'history', 'name': 'History',           'icon': '🏛️', 'color': '#ef4444', 'desc': 'Ancient, medieval, modern history'},
    {'id': 'geo',     'name': 'Geography',         'icon': '🌍', 'color': '#06b6d4', 'desc': 'Maps, rivers, countries'},
    {'id': 'cs',      'name': 'Computer Science',  'icon': '💻', 'color': '#8b5cf6', 'desc': 'Python, algorithms, data structures'},
    {'id': 'evs',     'name': 'Environmental Studies', 'icon': '🌱', 'color': '#10b981', 'desc': 'Nature, environment, ecology'},
    {'id': 'social',  'name': 'Social Studies',    'icon': '🏘️', 'color': '#f97316', 'desc': 'Community, civics, culture'},
]

QUIZ_QUESTIONS = {
    'Mathematics': [
        {'q': 'What is the value of x in: 2x + 6 = 14?', 'opts': ['x = 3', 'x = 4', 'x = 7', 'x = 10'], 'ans': 1},
        {'q': 'Area of a circle with radius 7 (π ≈ 3.14)?', 'opts': ['153.86', '144', '49', '22'], 'ans': 0},
        {'q': 'What is the HCF of 12 and 18?', 'opts': ['3', '6', '9', '12'], 'ans': 1},
        {'q': 'sin(90°) = ?', 'opts': ['0', '0.5', '1', '−1'], 'ans': 2},
        {'q': 'Sum of angles in a triangle?', 'opts': ['90°', '180°', '270°', '360°'], 'ans': 1},
    ],
    'Science': [
        {'q': 'Chemical formula of water?', 'opts': ['H2O', 'CO2', 'O2', 'NaCl'], 'ans': 0},
        {'q': 'Which gas do plants absorb during photosynthesis?', 'opts': ['Oxygen', 'Nitrogen', 'Carbon Dioxide', 'Hydrogen'], 'ans': 2},
        {'q': "Newton's 2nd Law of Motion?", 'opts': ['F = ma', 'E = mc²', 'v = u + at', 'PV = nRT'], 'ans': 0},
        {'q': 'Which organ purifies blood in the human body?', 'opts': ['Heart', 'Lungs', 'Kidney', 'Liver'], 'ans': 2},
        {'q': 'Atomic number of Carbon?', 'opts': ['6', '8', '12', '14'], 'ans': 0},
    ],
    'English': [
        {'q': 'Which sentence is correct?', 'opts': ["She don't like apples.", "She doesn't likes apples.", "She doesn't like apples.", "She not like apples."], 'ans': 2},
        {'q': 'Synonym of "Happy"?', 'opts': ['Sad', 'Joyful', 'Angry', 'Tired'], 'ans': 1},
        {'q': 'The noun in: "The cat sat on the mat."', 'opts': ['sat', 'on', 'cat', 'The'], 'ans': 2},
        {'q': 'Antonym of "Ancient"?', 'opts': ['Old', 'Historic', 'Modern', 'Past'], 'ans': 2},
        {'q': 'Correct spelling?', 'opts': ['Accomodation', 'Accommodation', 'Acommodation', 'Acomodation'], 'ans': 1},
    ],
    'History': [
        {'q': 'Who founded the Mughal Empire?', 'opts': ['Akbar', 'Humayun', 'Babur', 'Aurangzeb'], 'ans': 2},
        {'q': 'Year India gained independence?', 'opts': ['1945', '1947', '1950', '1952'], 'ans': 1},
        {'q': 'Who gave the slogan "Do or Die"?', 'opts': ['Nehru', 'Bose', 'Gandhi', 'Tilak'], 'ans': 2},
        {'q': 'Battle of Plassey was fought in?', 'opts': ['1757', '1764', '1800', '1857'], 'ans': 0},
        {'q': 'Who wrote the Indian National Anthem?', 'opts': ['Bankim Chandra', 'Rabindranath Tagore', 'Sarojini Naidu', 'Aurobindo'], 'ans': 1},
    ],
    'Geography': [
        {'q': 'Longest river in India?', 'opts': ['Yamuna', 'Godavari', 'Ganga', 'Brahmaputra'], 'ans': 2},
        {'q': 'Capital of India?', 'opts': ['Mumbai', 'Delhi', 'Kolkata', 'Chennai'], 'ans': 1},
        {'q': 'Ocean to the south of India?', 'opts': ['Atlantic', 'Pacific', 'Indian', 'Arctic'], 'ans': 2},
        {'q': 'Mount Everest is in which country?', 'opts': ['India', 'China', 'Nepal', 'Bhutan'], 'ans': 2},
        {'q': 'Largest state of India by area?', 'opts': ['Maharashtra', 'Uttar Pradesh', 'Rajasthan', 'Madhya Pradesh'], 'ans': 2},
    ],
    'Computer Science': [
        {'q': 'Which is a loop statement in Python?', 'opts': ['if', 'while', 'def', 'class'], 'ans': 1},
        {'q': 'CPU stands for?', 'opts': ['Central Processing Unit', 'Computer Power Unit', 'Central Program Utility', 'Core Processing Unit'], 'ans': 0},
        {'q': 'Output of print(2**3) in Python?', 'opts': ['6', '8', '5', '9'], 'ans': 1},
        {'q': 'Data type for True/False values?', 'opts': ['int', 'string', 'boolean', 'float'], 'ans': 2},
        {'q': 'Comment symbol in Python?', 'opts': ['//', '/*', '#', '--'], 'ans': 2},
    ],
    'Environmental Studies': [
        {'q': 'Which gas makes up most of Earth\'s atmosphere?', 'opts': ['Oxygen', 'Carbon Dioxide', 'Nitrogen', 'Hydrogen'], 'ans': 2},
        {'q': 'What is the process of water changing into vapor called?', 'opts': ['Condensation', 'Evaporation', 'Precipitation', 'Transpiration'], 'ans': 1},
        {'q': 'Which is a renewable source of energy?', 'opts': ['Coal', 'Petroleum', 'Solar', 'Natural Gas'], 'ans': 2},
        {'q': 'Trees are cut down in a process called?', 'opts': ['Afforestation', 'Deforestation', 'Reforestation', 'Erosion'], 'ans': 1},
        {'q': 'The top layer of the Earth is called?', 'opts': ['Mantle', 'Core', 'Crust', 'Magma'], 'ans': 2},
    ],
    'Social Studies': [
        {'q': 'How many states are there in India?', 'opts': ['25', '28', '29', '31'], 'ans': 1},
        {'q': 'Panchayati Raj works at which level of government?', 'opts': ['Central', 'State', 'Local/Village', 'District'], 'ans': 2},
        {'q': 'The Constitution of India was adopted on?', 'opts': ['15 Aug 1947', '26 Jan 1950', '26 Nov 1949', '2 Oct 1950'], 'ans': 1},
        {'q': 'Who is the head of the state government?', 'opts': ['President', 'Prime Minister', 'Governor', 'Chief Minister'], 'ans': 3},
        {'q': 'Right to Education Act was passed in?', 'opts': ['2002', '2005', '2009', '2012'], 'ans': 2},
    ],
}

