import os
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOADS_DIR
from parsers import parse_file, supported_extensions

router = Router()

@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    doc = message.document
    file_name = doc.file_name or "file"
    ext = os.path.splitext(file_name)[1].lower()
    
    if ext not in supported_extensions():
        await message.answer(
            f"form {ext} is not supported. \n"
            f"Supported formats: txt"
        )
        return
    
    msg = await message.answer("I am reading...")
    file_path = os.path.join(DOWNLOADS_DIR, f"{message.from_user.id}_{file_name}")
    await bot.download(doc, destination = file_path)
    
    questions = parse_file(file_path)
    
    if not questions:
        await msg.edit_text(
            "WHERE IS YOUR QUESTIONS???. \n"
            "CHECK YOUR FILE AND TRY AGAIN MAN OR WOMAN oror try use /help"
        )
        return
    
    await msg.edit_text(
        f"Find it <b>{len(questions)}</b> questions\n\n"
        f"Soon i will send you alll questions"
    )