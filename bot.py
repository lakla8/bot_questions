import telebot, logging, os, time
from dotenv import load_dotenv
from models import User, language_setup, check_user_new
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
except Exception as e:
    logging.error(f"An error occurred: {e}")

user_data = []
replics, questions = language_setup("resources/replics.txt", "resources/question.txt")
catch_phrase = "ОТПРАВИТЬ"
write_phrase = "Друг"
lang_question = "Напишите, пожалуйста, Ваш вариант"
logger = telebot.logger


def update_inline_markup(callback: str, pos: int, user):
    markup = InlineKeyboardMarkup()
    for index in range(len(questions[pos])):
        if questions[pos][index] in callback:
            if u'\u2713' in callback:
                user.temp_ans.remove(callback[:-4])
                text = questions[pos][index]
            else:
                text = questions[pos][index] + u'\u2713'
                user.temp_ans.append(text)
            markup.add(InlineKeyboardButton(text=text, callback_data=text + ":mtm"))
        else:
            if questions[pos][index] + u'\u2713' in user.temp_ans:
                text = questions[pos][index] + u'\u2713'
            else:
                text = questions[pos][index]
            markup.add(InlineKeyboardButton(text=text, callback_data=text + ":mtm"))
    return markup


def inline_markup(pos: int, flq=False):
    markup = InlineKeyboardMarkup()
    if catch_phrase in questions[pos][-1]:
        flq = True
    for index in range(len(questions[pos])):
        text = questions[pos][index]
        if flq:
            text = text + ":mtm"
        markup.add(InlineKeyboardButton(text=questions[pos][index], callback_data=text))
    return markup


def lang_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="RUS", callback_data="RUS"),
               InlineKeyboardButton(text="ENG", callback_data="ENG"))
    return markup


@bot.message_handler(commands=['restart'])
def restart(message):
    if check_user_new(message.from_user.id, user_data) is True:
        user = user_data[check_user_new(message.from_user.id, user_data)]
        user_data.remove(user)
    starting_message(message)


@bot.message_handler(commands=['help'])
def helper(message):
    bot.send_message(message.from_user.id, "Введите /start - чтобы продолжить опрос\nВведите /restart - начать опрос заново")


@bot.message_handler(commands=['start'])
def starting_message(message):
    if check_user_new(message.from_user.id, user_data) is False:
        user_data.append(User(message.from_user.id, message.from_user.username))
    user = user_data[check_user_new(message.from_user.id, user_data)]
    user.pos = 0
    user.answers = []
    bot.send_message(user.id, "Выберите язык/Choose your language", reply_markup=lang_markup())


@bot.callback_query_handler(func=lambda call: True)
def on_callback_query(call):
    global replics, questions, catch_phrase, write_phrase, lang_question
    if check_user_new(call.from_user.id, user_data) is False:
        bot.delete_message(call.message.chat.id, call.message.id)
        restart(call)
        return
    user = user_data[check_user_new(call.from_user.id, user_data)]
    if call.data == "RUS" or call.data == "ENG":
        if "RUS" == call.data:
            replics, questions = language_setup("resources/replics.txt", "resources/question.txt")
            catch_phrase = "ОТПРАВИТЬ"
            write_phrase = "Друг"
            lang_question = "Напишите, пожалуйста, Ваш вариант"
            bot.edit_message_text("Спасибо, что согласились принять участие! Изучаем потребности людей, которые находятся в поиске работы в других странах, а также потребностей карьерных консультантов и компаний, которые помогают искать работу.", call.message.chat.id, call.message.id)
            time.sleep(2)
            bot.send_message(user.id, replics[user.pos], reply_markup=inline_markup(user.pos))
        else:
            replics, questions = language_setup("resources/replics_eng.txt", "resources/question_eng.txt")
            catch_phrase = "SEND"
            write_phrase = "Other"
            lang_question = "Write your answer, please"
            bot.edit_message_text("Thank you for agreeing to take part! We study the needs of people looking for work in other countries, likewise the needs of career consultants and companies that help with job searches.", call.message.chat.id, call.message.id)
            time.sleep(2)
            bot.send_message(user.id, replics[user.pos], reply_markup=inline_markup(user.pos))
    elif call.data.find(":mtm") != -1:
        if write_phrase in call.data:
            user.writing_status = abs(user.writing_status - 1)
        if catch_phrase in call.data and len(user.temp_ans) > 0:
            user.pos += 1
            if user.writing_status:
                bot.edit_message_text(lang_question, call.message.chat.id, call.message.id)
            else:
                user.answers.append(user.temp_ans)
                user.temp_ans = []
                bot.edit_message_text(replics[user.pos], call.message.chat.id, call.message.id, reply_markup=inline_markup(user.pos))
        elif catch_phrase in call.data:
            pass
        else:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=update_inline_markup(call.data, user.pos, user))

    else:
        user.answers.append([call.data])
        user.pos += 1
        if user.check_end(len(questions)):
            bot.edit_message_text(replics[user.pos], call.message.chat.id, call.message.id)
        else:
            bot.edit_message_text(replics[user.pos], call.message.chat.id, call.message.id, reply_markup=inline_markup(user.pos))


@bot.message_handler(content_types=['text'])
def text_answer(message):
    if check_user_new(message.from_user.id, user_data) is False:
        restart(message)
        return
    user = user_data[check_user_new(message.from_user.id, user_data)]
    if user.writing_status:
        user.temp_ans.append(message.text)
        user.answers.append(user.temp_ans)
        user.temp_ans = []
        user.writing_status = 0
        user.pos += 1
        bot.send_message(user.id, replics[user.pos], reply_markup=inline_markup(user.pos))
    elif user.end_bool:
        user.answers.append([message.text])
        bot.send_message(user.id, replics[user.pos + 2])
        user.save(replics)
    elif user.check_end(len(questions)):
        user.answers.append([message.text])
        user.end_bool = True
        bot.send_message(user.id, replics[user.pos + 1])
    else:
        bot.send_message(user.id, "напишите /start чтобы начать заново")


bot.infinity_polling()
