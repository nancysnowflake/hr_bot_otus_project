from telegram import Update, ParseMode
from telegram.ext import CallbackContext
import database
import menu
import os
import random
import string

# здесь будем хранить текущий заданный вопрос
user = {}


def text_handler(update: Update, context: CallbackContext) -> None:
    deps = database.get_departments()

    # если запросили список отделов
    for d in deps:
        if d['name'] == update.message.text:
            vacancies = menu.vacancies(d['name'])
            if vacancies is None:
                update.message.reply_text(
                    fr'К сожалению в данном отделе нет свободных вакансий',
                )
            else:
                update.message.reply_text(
                    fr'Доступные вакансии',
                    reply_markup=vacancies,
                )
            return

    # если ответ на вопрос
    telegram_id = update.effective_user.id
    if telegram_id in user:
        answer_handler(update.message.text, telegram_id, update.message, context)


def start_handler(update: Update, _: CallbackContext) -> None:
    telegram_user = database.get_user(update.effective_user.id)
    if telegram_user is None:
        database.insert_user(update.effective_user.id, update.effective_user.name, update.effective_user.full_name)

    admins = database.get_admins()
    for admin in admins:
        if admin['telegram_username'] == update.effective_user.name:
            database.update_admin(
                update.effective_user.id,
                update.effective_chat.id,
                update.effective_user.name,
            )
            break

    deps = []
    for d in database.get_departments():
        deps.append(fr'<b>{d["name"]}</b>')
    dep_list = os.linesep.join(deps)

    update.message.reply_html(
        fr'Привет, <b>{update.effective_user.full_name}</b>{os.linesep}'
        fr'Я бот помощник, если ты ищешь работу, то выбери отдел, который тебя интересует.{os.linesep}'
        fr'{dep_list}',
        reply_markup=menu.departments(),
    )


def respond_callback_handler(update: Update, _: CallbackContext) -> None:
    global user
    query = update.callback_query
    query.answer()

    vacancy_id = query.data.replace('respond_', '')

    telegram_id = update.effective_user.id
    question = database.get_next_question(vacancy_id, 0)
    user[telegram_id] = {}
    user[telegram_id]['last_question'] = question['id']
    user[telegram_id]['last_priority'] = question['priority']
    user[telegram_id]['vacancy_id'] = vacancy_id
    user[telegram_id]['interview_id'] = random_string(10)

    query.message.reply_text(
        text=question['question'],
        reply_markup=menu.answer_variants(question['id'])
    )


def answer_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    answer = query.data.replace('answer_', '')
    answer_handler(answer, update.effective_user.id, query.message, context)


# https://stackoverflow.com/questions/62253718/how-can-i-receive-file-in-python-telegram-bot
def file_handler(update: Update, context: CallbackContext) -> None:
    global user
    telegram_id = update.effective_user.id
    if telegram_id not in user:
        return

    username = update.effective_user.username
    file_name = fr'cv/{username}_{update.message.document.file_name}'
    with open(file_name, 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)

    database.update_user_cv(telegram_id, file_name)
    answer_handler(file_name, telegram_id, update.message, context)


def answer_handler(answer, telegram_id, message, context):
    global user
    if telegram_id not in user:
        return

    question_id = user[telegram_id]['last_question']
    priority = user[telegram_id]['last_priority']
    interview_id = user[telegram_id]['interview_id']
    vacancy_id = user[telegram_id]['vacancy_id']

    database.insert_answer(interview_id, telegram_id, question_id, answer)
    question = database.get_next_question(vacancy_id, priority, answer)
    if question is None:
        # вопросы закончились
        database.insert_respond(interview_id, telegram_id, vacancy_id)
        send_message_to_admins(context, telegram_id)
        del user[telegram_id]
        message.reply_text(text='Спасибо! Мы ответим Вам в ближайшее время')
        return

    user[telegram_id]['last_question'] = question['id']
    user[telegram_id]['last_priority'] = question['priority']
    message.reply_text(
        text=question['question'],
        reply_markup=menu.answer_variants(question['id'])
    )


def vacancy_handler(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    vacancy_id = query.data.replace('vacancy_id_', '')

    vacancy = database.get_vacancy(vacancy_id)
    if vacancy is None:
        query.message.reply_text(
            fr'Извините, но похоже, что кандидат на эту вакансию уже найден.',
        )
        return

    salary = ''
    if vacancy['min_salary'] > 0:
        salary = fr'от {vacancy["min_salary"]}₽ '
    if vacancy['max_salary'] > 0:
        salary += fr'до {vacancy["max_salary"]}₽'
    if vacancy['min_salary'] == 0 and vacancy['max_salary'] == 0:
        salary = 'по договоренности'

    query.message.reply_html(
        fr'<b>Вакансия:</b> {vacancy["name"]}{os.linesep}'
        fr'<b>Вам предстоит:</b> {vacancy["description_vacancy"]}{os.linesep}'
        fr'<b>Мы ожидаем, что вы:</b> {vacancy["requirements"]}{os.linesep}'
        fr'<b>Работа у нас - это:</b> {vacancy["description_company"]}{os.linesep}'
        fr'<b>Зарплата:</b> {salary}{os.linesep}',
        reply_markup=menu.respond(vacancy_id)
    )


def send_message_to_admins(context: CallbackContext, telegram_id):
    global user
    admins = database.get_admins()
    vacancy_id = user[telegram_id]['vacancy_id']
    interview_id = user[telegram_id]['interview_id']
    telegram_user = database.get_user(telegram_id)
    for admin in admins:
        if admin['chat_id'] > 0:
            vacancy = database.get_vacancy(vacancy_id)
            text = fr'Новый отклик на вакансию {vacancy["name"]}!{os.linesep}'
            answers = database.get_answers(interview_id)

            for answer in answers:
                text += fr'<b>{answer["question"]}</b>{os.linesep}' \
                       fr'{answer["answer"]}{os.linesep}'

            context.bot.send_message(
                chat_id=admin['chat_id'],
                text=text,
                parse_mode=ParseMode.HTML
            )
            if telegram_user["cv_path"] != "":
                with open(telegram_user["cv_path"], "rb") as file:
                    context.bot.send_document(
                        chat_id=admin["chat_id"],
                        document=file,
                        filename=os.path.basename(telegram_user["cv_path"]),
                    )


# https://pynative.com/python-generate-random-string/
def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))
