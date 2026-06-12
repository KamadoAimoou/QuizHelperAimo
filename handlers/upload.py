import os
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOADS_DIR
from parsers import parse_file, supported_extensions
from database.db import create_quiz, save_questions

router = Router()


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    doc = message.document
    file_name = doc.file_name or "file"
    ext = os.path.splitext(file_name)[1].lower()

    if ext not in supported_extensions():
        await message.answer(
            f"❌ Формат {ext} не поддерживается.\n"
            f"Отправь: TXT, PDF, DOCX, JPG, PNG"
        )
        return

    msg = await message.answer("⏳ Читаю файл...")

    file_path = os.path.join(DOWNLOADS_DIR, f"{message.from_user.id}_{file_name}")
    await bot.download(doc, destination=file_path)

    questions = parse_file(file_path)

    if not questions:
        await msg.edit_text(
            "😕 Не нашёл вопросы в файле.\n"
            "Проверь формат через /help"
        )
        return

    # Сохраняем в PostgreSQL
    quiz_id = await create_quiz(message.from_user.id, file_name, len(questions))
    await save_questions(quiz_id, questions)

    # Кнопка начать тест
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"▶️ Начать тест ({len(questions)} вопросов)",
            callback_data=f"start_quiz:{quiz_id}"
        )
    ]])

    await msg.edit_text(
        f"✅ Нашёл <b>{len(questions)}</b> вопросов!\n\nГотов начать?",
        reply_markup=keyboard
    )


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    msg = await message.answer("⏳ Распознаю текст на изображении...")

    photo = message.photo[-1]
    file_path = os.path.join(DOWNLOADS_DIR, f"{message.from_user.id}_photo.jpg")
    await bot.download(photo, destination=file_path)

    questions = parse_file(file_path)

    if not questions:
        await msg.edit_text("😕 Не нашёл вопросы. Попробуй более чёткое фото.")
        return

    quiz_id = await create_quiz(message.from_user.id, "photo_quiz", len(questions))
    await save_questions(quiz_id, questions)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"▶️ Начать тест ({len(questions)} вопросов)",
            callback_data=f"start_quiz:{quiz_id}"
        )
    ]])

    await msg.edit_text(
        f"✅ Нашёл <b>{len(questions)}</b> вопросов!\n\nГотов начать?",
        reply_markup=keyboard
    )