from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
import database


def vacancies(department_name):
    vacs = database.get_vacancies(department_name)
    if len(vacs) == 0:
        return None

    keyboard = []
    for v in vacs:
        vacancy_id = v['id']
        keyboard.append(InlineKeyboardButton(v['name'], callback_data=fr'vacancy_id_{vacancy_id}'))

    return InlineKeyboardMarkup([keyboard])


def departments():
    deps = database.get_departments()
    buttons = []
    group = []
    i = 0

    while i < len(deps):
        if i % 4 == 0:
            buttons.append(group)
            group = []
        group.append(KeyboardButton(deps[i]['name']))
        i += 1
    buttons.append(group)
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def answer_variants(question_id):
    variants = database.get_answer_variants(question_id)
    if len(variants) == 0:
        return None

    keyboard = []
    for v in variants:
        keyboard.append(InlineKeyboardButton(v['answer'], callback_data=fr'answer_{v["answer"]}'))

    return InlineKeyboardMarkup([keyboard])


def respond(vacancy_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('Откликнуться', callback_data=fr'respond_{vacancy_id}')]])


