from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import (
    create_session, get_active_session, get_question,
    update_session, finish_session, save_answer,
    get_session_answers, get_all_questions, get_quiz
)
import asyncpg
from config import DATABASE_URL

router = Router()


@router.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz(callback: CallbackQuery):
    quiz_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    session_id = await create_session(user_id, quiz_id)
    question = await get_question(quiz_id, 0)
    quiz = await get_quiz(quiz_id)

    if not question:
        await callback.message.edit_text("Вопросы не найдены!")
        return

    await callback.message.edit_text(
        f"Начинаем! Всего вопросов: <b>{quiz['total']}</b>\n\nУдачи!"
    )
    await send_question(callback.message, session_id, quiz_id, question, 0, quiz["total"])
    await callback.answer()


async def send_question(message, session_id: int, quiz_id: int, question: dict, index: int, total: int):
    letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
    options = question.get("options", [])

    # Защита от пустого списка
    if not options:
        await message.answer("Ошибка: варианты ответов не найдены.")
        return

    options_text = ""
    for i, opt in enumerate(options):
        clean = opt.lstrip("ABCDEFGHabcdefgh123456789).").strip()
        if i < len(letters):
            options_text += f"{letters[i]}) {clean}\n"

    buttons = []
    for i in range(len(options)):
        if i < len(letters):
            buttons.append([InlineKeyboardButton(
                text=letters[i],
                callback_data=f"answer:{session_id}:{question['id']}:{i}"
            )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"<b>Вопрос {index + 1} из {total}</b>\n\n"
        f"{question['question_text']}\n\n"
        f"{options_text}",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("answer:"))
async def handle_answer(callback: CallbackQuery):
    parts = callback.data.split(":")
    session_id = int(parts[1])
    question_id = int(parts[2])
    chosen = int(parts[3])

    session = await get_active_session(callback.from_user.id)
    if not session:
        await callback.answer("Сессия не найдена. Начни тест заново.")
        return

    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT * FROM questions WHERE id=$1", question_id)
    await conn.close()

    if not row:
        await callback.answer("Вопрос не найден.")
        return

    options = row["options"].split("|")
    correct = row["correct_option"]
    is_correct = (chosen == correct)

    new_score = session["score"] + (1 if is_correct else 0)
    new_index = session["current_index"] + 1

    await save_answer(session_id, question_id, chosen, is_correct)
    await update_session(session_id, new_index, new_score)

    letters = ["A", "B", "C", "D", "E", "F", "G", "H"]

    if is_correct:
        await callback.answer("Правильно!", show_alert=False)
    else:
        await callback.answer(
            f"Неверно. Правильный ответ: {letters[correct]}",
            show_alert=True
        )

    await callback.message.edit_reply_markup(reply_markup=None)

    quiz = await get_quiz(session["quiz_id"])
    if new_index >= quiz["total"]:
        await finish_quiz(callback.message, session_id, session["quiz_id"], new_score, quiz["total"])
    else:
        next_q = await get_question(session["quiz_id"], new_index)
        await send_question(callback.message, session_id, session["quiz_id"], next_q, new_index, quiz["total"])


async def finish_quiz(message, session_id: int, quiz_id: int, score: int, total: int):
    await finish_session(session_id)

    answers = await get_session_answers(session_id)
    questions = await get_all_questions(quiz_id)

    percent = round(score / total * 100) if total > 0 else 0

    if percent >= 90:
        grade = "Отлично!"
    elif percent >= 70:
        grade = "Хорошо!"
    elif percent >= 50:
        grade = "Неплохо, но есть куда расти"
    else:
        grade = "Нужно повторить материал"

    result = (
        f"<b>Тест завершён!</b>\n\n"
        f"Правильно: <b>{score}</b> из <b>{total}</b>\n"
        f"Результат: <b>{percent}%</b>\n"
        f"{grade}\n\n"
        f"<b>Разбор:</b>\n\n"
    )

    letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        icon = "✅" if a["is_correct"] else "❌"
        correct_letter = letters[q["correct_option"]] if q["correct_option"] < len(letters) else "?"
        result += f"{icon} <b>Вопрос {i}:</b> {q['question_text']}\n"
        if not a["is_correct"]:
            your_letter = letters[a["chosen_option"]] if a["chosen_option"] < len(letters) else "?"
            result += f"   Твой: {your_letter} | Правильно: <b>{correct_letter}</b>\n"
        else:
            result += f"   Ответ: <b>{correct_letter}</b>\n"
        result += "\n"

    await message.answer(result)