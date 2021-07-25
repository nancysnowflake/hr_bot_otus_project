import sqlite3

conn = sqlite3.connect('database.sqlite', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''create table if not exists users
(
    telegram_id integer,
    telegram_username string,
    telegram_full_name string,
    cv_path string
)''')

cursor.execute('''create table if not exists admins
(
    telegram_id integer DEFAULT 0,
    chat_id integer DEFAULT 0,
    telegram_username string
)''')

cursor.execute('''create table if not exists responds
(
    telegram_id integer,
    vacancy_id integer
)''')

cursor.execute('''create table if not exists departments
(
    id integer PRIMARY KEY AUTOINCREMENT,
    name string
)''')


cursor.execute('''create table if not exists vacancies
(
    id integer PRIMARY KEY AUTOINCREMENT,
    name string,
    description_vacancy string,
    description_company string,
    requirements string,
    department_id integer,
    min_salary integer DEFAULT 0,
    max_salary integer DEFAULT 0
)''')


cursor.execute('''create table if not exists questions
(
    id integer PRIMARY KEY AUTOINCREMENT,
    priority integer,
    question string,
    vacancy_id integer DEFAULT 0,
    variant_id integer DEFAULT 0
)''')


cursor.execute('''create table if not exists answer_variants
(
    id integer PRIMARY KEY AUTOINCREMENT,
    question_id integer,
    answer string
)''')


cursor.execute('''create table if not exists answers
(
    id integer PRIMARY KEY AUTOINCREMENT,
    interview_id string,
    telegram_id integer,
    question_id integer,
    answer string
)''')


def get_user(telegram_id):
    cursor.execute('''select * from users where telegram_id = ?''', (telegram_id,))
    return cursor.fetchone()


def update_admin(telegram_id, chat_id, telegram_username):
    cursor.execute('''
    update admins set telegram_id = ?, chat_id = ?
    where telegram_username = ?''', (telegram_id, chat_id, telegram_username,))
    conn.commit()


def update_user_cv(telegram_id, file_name):
    cursor.execute('''
    update users set cv_path = ?
    where telegram_id = ?''', (file_name, telegram_id,))
    conn.commit()


def get_departments():
    cursor.execute('''select * from departments''')
    return cursor.fetchall()


def insert_user(telegram_id, telegram_name, telegram_full_name):
    cursor.execute('''
    insert into users(telegram_id, telegram_username, telegram_full_name)
    values(?, ?, ?)''', (telegram_id, telegram_name, telegram_full_name,))
    conn.commit()


def get_vacancy(vacancy_id):
    cursor.execute('''select * from vacancies where id = ?''', (vacancy_id,))
    return cursor.fetchone()


def get_vacancies(department_name):
    cursor.execute('''
    select *
    from vacancies v join departments d on d.id = v.department_id
    where d.name = ?''', (department_name,))
    return cursor.fetchall()


def get_next_question(vacancy_id, priority, previous_answer=''):
    cursor.execute('''
    select * from questions
    where (vacancy_id = 0 or vacancy_id = ?) and previous_answer = ? and priority > ?
    order by priority''', (vacancy_id, previous_answer, priority,))
    questions = cursor.fetchall()

    if previous_answer != '' and len(questions) == 0:
        cursor.execute('''
            select * from questions
            where (vacancy_id = 0 or vacancy_id = ?) and previous_answer = '' and priority > ?
            order by priority''', (vacancy_id, priority,))
        questions = cursor.fetchall()

    if len(questions) == 0:
        return None

    return questions[0]


def get_answers(interview_id):
    cursor.execute('''
        select distinct q.question, a.answer from answers a
        join questions q on q.id = a.question_id
        where a.interview_id = ?''', (interview_id,))
    return cursor.fetchall()


def get_answer_variants(question_id):
    cursor.execute('''
    select * from answer_variants
    where question_id = ?''', (question_id,))
    return cursor.fetchall()


def insert_answer(interview_id, telegram_id, question_id, answer):
    cursor.execute('''
    insert into answers(interview_id, telegram_id, question_id, answer)
    values(?, ?, ?, ?)''', (interview_id, telegram_id, question_id, answer,))
    conn.commit()


def insert_respond(interview_id, telegram_id, vacancy_id):
    cursor.execute('''
    insert into responds(interview_id, telegram_id, vacancy_id)
    values(?, ?, ?)''', (interview_id, telegram_id, vacancy_id,))
    conn.commit()


def get_admins():
    cursor.execute('''select * from admins''')
    return cursor.fetchall()
