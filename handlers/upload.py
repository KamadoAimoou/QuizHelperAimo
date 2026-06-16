import os
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOADS_DIR
from parsers import parse_file, supported_extensions
from database.db import create_quiz, save_questions

router = Router()

_EMPTY_HINTS: dict[str, str] = {
    '.pdf': (
        "Не нашёл вопросы в PDF.\n\n"
        "Убедись, что:\n"
        "• правильный ответ выделен <b>жёлтым цветом</b>, или\n"
        "• после каждого вопроса написано <code>Ответ: B</code>"
    ),
    '.docx': (
        "Не нашёл вопросы в DOCX.\n\n"
        "Убедись, что:\n"
        "• правильный ответ выделен <b>жёлтым</b> в Word, или\n"
        "• после каждого вопроса написано <code>Ответ: B</code>"
    ),
    '.txt': (
        "Не нашёл вопросы в TXT.\n\n"
        "Добавь после каждого вопроса строку <code>Ответ: B</code>\n"
        "или отметь правильный вариант звёздочкой: <code>*B) текст</code>"
    ),
}
_EMPTY_DEFAULT = "😕 Не нашёл вопросы в файле.\n\nПроверь формат через /help"
_PHOTO_EMPTY   = "😕 Не распознал вопросы. Попробуй более чёткое фото с хорошим освещением."


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    doc  = message.document
    name = doc.file_name or 'file'
    ext  = os.path.splitext(name)[1].lower()

    if ext not in supported_extensions():
        await message.answer(
            f"❌ Формат <code>{ext}</code> не поддерживается.\n"
            f"Отправь файл: TXT, PDF, DOCX, JPG или PNG"
        )
        return

    msg       = await message.answer("⏳ Читаю файл…")
    file_path = os.path.join(DOWNLOADS_DIR, f"{message.from_user.id}_{name}")
    await bot.download(doc, destination=file_path)

    questions = parse_file(file_path)

    if not questions:
        hint = _EMPTY_HINTS.get(ext, _EMPTY_DEFAULT)
        await msg.edit_text(hint)
        return

    quiz_id = await create_quiz(message.from_user.id, name, len(questions))
    await save_questions(quiz_id, questions)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"▶️ Начать тест ({len(questions)} вопросов)",
            callback_data=f"start_quiz:{quiz_id}",
        )
    ]])
    await msg.edit_text(
        f"✅ Нашёл <b>{len(questions)}</b> вопросов!\n\nГотов начать?",
        reply_markup=keyboard,
    )


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    msg       = await message.answer("⏳ Распознаю текст на изображении…")
    photo     = message.photo[-1]
    file_path = os.path.join(DOWNLOADS_DIR, f"{message.from_user.id}_photo.jpg")
    await bot.download(photo, destination=file_path)

    questions = parse_file(file_path)

    if not questions:
        await msg.edit_text(_PHOTO_EMPTY)
        return

    quiz_id = await create_quiz(message.from_user.id, "photo_quiz", len(questions))
    await save_questions(quiz_id, questions)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"▶️ Начать тест ({len(questions)} вопросов)",
            callback_data=f"start_quiz:{quiz_id}",
        )
    ]])
    await msg.edit_text(
        f"✅ Нашёл <b>{len(questions)}</b> вопросов!\n\nГотов начать?",
        reply_markup=keyboard,
    )
