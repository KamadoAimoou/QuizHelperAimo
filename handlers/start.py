from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from database.db import get_user_quizzes

router = Router()


@router.message(CommandStart())
async def start_command_handler(message: Message):
    await message.answer(
        f"Привет, <b>{message.from_user.first_name}</b>! 👋\n\n"
        "Я бот для прохождения тестов. Вот что я умею:\n\n"
        "📎 Отправь файл (TXT, PDF, DOCX) или фото — я распознаю вопросы и запущу тест\n"
        "📋 /my_quizzes — посмотреть твои загруженные тесты\n"
        "❓ /help — подробная справка по форматам файлов"
    )


@router.message(Command("help"))
async def help_command_handler(message: Message):
    await message.answer(
        "<b>Поддерживаемые форматы файлов</b>\n\n"

        "📄 <b>PDF с жёлтой подсветкой</b> — просто отправь PDF, правильный ответ определяется автоматически по выделению\n\n"

        "📝 <b>DOCX с подсветкой</b> — выдели правильный ответ жёлтым цветом в Word, бот распознает его\n\n"

        "📋 <b>TXT / DOCX / PDF — формат 1: явный ответ</b>\n"
        "<code>1. Вопрос\n"
        "A) Вариант 1\n"
        "B) Вариант 2\n"
        "C) Вариант 3\n"
        "D) Вариант 4\n"
        "Ответ: B</code>\n\n"

        "📋 <b>Формат 2: звёздочка перед правильным</b>\n"
        "<code>1. Вопрос\n"
        "A) Вариант 1\n"
        "*B) Правильный ответ\n"
        "C) Вариант 3\n"
        "D) Вариант 4</code>\n\n"

        "📋 <b>Формат 3: цифры вместо букв</b>\n"
        "<code>1. Вопрос\n"
        "1) Вариант 1\n"
        "2) Вариант 2\n"
        "3) Вариант 3\n"
        "4) Вариант 4\n"
        "Правильный ответ: 2</code>\n\n"

        "🖼 <b>Фото / JPG / PNG</b> — сфотографируй лист, бот распознает текст через OCR\n\n"

        "⚠️ Между вопросами оставляй <b>пустую строку</b>"
    )


@router.message(Command("my_quizzes"))
async def my_quizzes_handler(message: Message):
    quizzes = await get_user_quizzes(message.from_user.id)

    if not quizzes:
        await message.answer("У тебя пока нет загруженных тестов.\n\nОтправь файл, чтобы создать первый!")
        return

    await message.answer(f"<b>Твои тесты ({len(quizzes)} шт.):</b>")

    for quiz in quizzes:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=f"▶️ Пройти ({quiz['total']} вопросов)",
                callback_data=f"start_quiz:{quiz['id']}"
            )
        ]])
        created = quiz["created_at"].strftime("%d.%m.%Y %H:%M")
        await message.answer(
            f"📝 <b>{quiz['title']}</b>\n"
            f"Вопросов: {quiz['total']} | Добавлен: {created}",
            reply_markup=keyboard
        )
