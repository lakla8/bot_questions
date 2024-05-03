import logging
import os
import time
import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.handlers import CallbackQueryHandler
from models import User, language_setup, check_user_new, lang_setup_phrase, clear

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_2")

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=TELEGRAM_TOKEN)
    await dp.start_polling(bot)

dp = Dispatcher()

user_data = []


def update_inline_markup(markup, callback, pos: int, user):
    key = markup.inline_keyboard
    for row in range(len(key)):
        if key[row][0].callback_data in callback:
            if "✓" in key[row][0].text:
                user.temp_ans.remove(key[row][0].text)
                text = questions[pos][row]
            else:
                text = questions[pos][row] + u'\u2713'
                user.temp_ans.append(text)
            key[row][0].text = text
            break

    markup.buttons = key
    return markup


def inline_markup(pos: int, flq=False):
    markup = InlineKeyboardBuilder()
    if catch_phrase in questions[pos][-1]:
        flq = True
    for text_ in questions[pos]:
        text = text_
        if flq:
            text = text_ + ":mtm"
        markup.row(InlineKeyboardButton(text=text_, callback_data=text))
    return markup.as_markup()


def lang_markup():
    markup = InlineKeyboardBuilder()
    markup.button(text="RUS", callback_data="RUS")
    markup.button(text="ENG", callback_data="ENG")
    return markup.as_markup()


@dp.message(Command('restart'))
async def restart(message: types.Message):
    user_index = check_user_new(message.from_user.id, user_data)
    if user_index is not False:
        user = user_data[user_index]
        user_data.remove(user)
    await command_start_handler(message)


@dp.message(Command("help"))
async def helper(message: types.Message):
    await message.answer("Введите /start - чтобы продолжить опрос\nВведите /restart - начать опрос заново")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if check_user_new(message.from_user.id, user_data) is False:
        user_data.append(User(message.from_user.id, message.from_user.username))
    user = user_data[check_user_new(message.from_user.id, user_data)]
    user.pos = 0
    user.answers = []
    await message.answer("Выберите язык/Choose your language", reply_markup=lang_markup())


@dp.callback_query(lambda call: call.data in ["RUS", "ENG"])
async def on_callback_query(call: types.CallbackQuery):
    global replics, questions, catch_phrase, write_phrase, lang_question, skip_phrases
    user_index = check_user_new(call.from_user.id, user_data)
    if user_index is False:
        await call.message.delete()
        return
    user = user_data[user_index]
    if "RUS" == call.data:
        replics, questions = language_setup("resources/replics.txt", "resources/question.txt")
        catch_phrase, write_phrase, lang_question, skip_phrases = lang_setup_phrase(True)
        await call.message.edit_text(
            "Спасибо, что согласились принять участие! Изучаем потребности людей, которые находятся в поиске работы в других странах, а также потребностей карьерных консультантов и компаний, которые помогают искать работу."
        )
        time.sleep(2)
        await call.message.answer(replics[user.pos], reply_markup=inline_markup(user.pos))
    else:
        replics, questions = language_setup("resources/replics_eng.txt", "resources/question_eng.txt")
        catch_phrase, write_phrase, lang_question, skip_phrases = lang_setup_phrase(False)
        await call.message.edit_text(
            "Thank you for agreeing to take part! We study the needs of people looking for work in other countries, likewise the needs of career consultants and companies that help with job searches."
        )
        time.sleep(2)
        await call.message.answer(replics[user.pos], reply_markup=inline_markup(user.pos))


@dp.callback_query(lambda call: call.data.find("mtm") > -1)
async def on_callback_query_1(call: types.CallbackQuery):
    user_index = check_user_new(call.from_user.id, user_data)
    if user_index is False:
        await call.message.delete()
        return
    user = user_data[user_index]
    if write_phrase in call.data:
        user.writing_status = abs(user.writing_status - 1)
    elif clear(call.data) in skip_phrases and user.skip_position():
        user.skip_status = abs(user.skip_status - 1)   ##эта штука ломается при двух нажатиях

    if catch_phrase in call.data and len(user.temp_ans) > 0:
        if user.skip_status:
            user.temp_ans = []
            user.answers.append(call.data)
            user.pos = user.skip()
            user.skip_status = 0
            await call.message.edit_text(replics[user.pos], reply_markup=inline_markup(user.pos))
            return
        user.pos += 1
        if user.writing_status:
            await call.message.edit_text(lang_question)
        else:
            user.answers.append(user.temp_ans)
            user.temp_ans = []
            await call.message.edit_text(replics[user.pos], reply_markup=inline_markup(user.pos))
    if catch_phrase in call.data and len(user.temp_ans) == 0:
        pass
    else:
        await call.message.edit_reply_markup(reply_markup=update_inline_markup(call.message.reply_markup, call.data, user.pos, user))


@dp.callback_query(lambda call: True)
async def on_callback_query_2(call: types.CallbackQuery):
    user_index = check_user_new(call.from_user.id, user_data)
    if user_index is False:
        await call.message.delete()
        return
    user = user_data[user_index]
    if clear(call.data) in skip_phrases and user.skip_position():
        user.temp_ans = []
        user.answers.append(call.data)
        user.pos = user.skip()
        user.skip_status = 0
        await call.message.edit_text(replics[user.pos], reply_markup=inline_markup(user.pos))
    else:
        user.answers.append([call.data])
        user.pos += 1
        if user.check_end(len(questions)):
            await call.message.edit_text(replics[user.pos])
        else:
            await call.message.edit_text(replics[user.pos], reply_markup=inline_markup(user.pos))


@dp.message()
async def text_answer(message: types.Message):
    user_index = check_user_new(message.from_user.id, user_data)
    if user_index is False:
        await restart(message)
        return
    user = user_data[user_index]
    if user.writing_status:
        user.temp_ans.append(message.text)
        user.answers.append(user.temp_ans)
        user.temp_ans = []
        user.writing_status = 0
        user.pos += 1
        await message.answer(replics[user.pos], reply_markup=inline_markup(user.pos))
    elif user.end_bool:
        user.answers.append([message.text])
        await message.answer(replics[user.pos + 2])
        user.save(replics)
    elif user.check_end(len(questions)):
        user.answers.append([message.text])
        user.end_bool = True
        await message.answer(replics[user.pos + 1])
    else:
        await message.answer("напишите /start чтобы начать заново")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())