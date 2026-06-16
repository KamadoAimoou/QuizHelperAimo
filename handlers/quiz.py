from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, PollAnswer,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from parsers.base import strip_option_prefix
from database.db import (
    create_session, get_active_session, get_question,
    update_session, finish_session, save_answer,
    get_session_answers, get_all_questions, get_quiz,
)

router = Router()

# Telegram limits for native polls
_MAX_POLL_QUESTION = 300
_MAX_OPTION_TEXT = 100

# poll_id -> {session_id, quiz_id, question_id, correct_option, chat_id, message_id}
# In-memory only: if the bot restarts mid-quiz, any poll awaiting an answer is lost
# and that one question won't be scored — acceptable trade-off for this bot's scale.
_ACTIVE_POLLS: dict[str, dict] = {}


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + "…"


@router.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz(callback: CallbackQuery, bot: Bot):
    quiz_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    session_id = await create_session(user_id, quiz_id)
    question = await get_question(quiz_id, 0)
    quiz = await get_quiz(quiz_id)

    if not question:
        await callback.message.edit_text("Вопросы не найдены!")
        return

    await callback.message.edit_text(
        f"Начинаем! Всего вопросов: <b>{quiz['total']}</b>\n\nУдачи!"
    )
    await send_question_poll(bot, chat_id, session_id, quiz_id, question, 0, quiz["total"])
    await callback.answer()


async def send_question_poll(bot: Bot, chat_id: int, session_id: int, quiz_id: int,
                              question: dict, index: int, total: int):
    raw_options = question.get("options", [])
    if len(raw_options) < 2:
        await bot.send_message(chat_id, "⚠️ Ошибка: у вопроса меньше двух вариантов ответа.")
        return

    options = [strip_option_prefix(o) or o for o in raw_options]
    options = [_truncate(o, _MAX_OPTION_TEXT) for o in options]

    correct = question["correct_option"]
    if correct >= len(options):
        correct = 0  # defensive fallback, should not happen

    header = f"{index + 1}/{total}. "
    full_question = header + question["question_text"]

    if len(full_question) <= _MAX_POLL_QUESTION:
        poll_question = full_question
    else:
        # Question too long for a Telegram poll (300 char limit) — send full text
        # separately, keep the poll question itself short.
        await bot.send_message(
            chat_id,
            f"<b>Вопрос {index + 1} из {total}</b>\n\n{question['question_text']}"
        )
        poll_question = header + "(текст вопроса выше) ⬆️"

    sent = await bot.send_poll(
        chat_id,
        question=poll_question,
        question_parse_mode=None,   # raw text — polls only support custom-emoji entities
        options=options,            # plain strings carry no parse_mode of their own
        type="quiz",
        correct_option_id=correct,
        is_anonymous=False,
    )

    _ACTIVE_POLLS[sent.poll.id] = {
        "session_id": session_id,
        "quiz_id": quiz_id,
        "question_id": question["id"],
        "correct_option": correct,
        "chat_id": chat_id,
        "message_id": sent.message_id,
    }


@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, bot: Bot):
    info = _ACTIVE_POLLS.pop(poll_answer.poll_id, None)
    if info is None or not poll_answer.option_ids:
        return

    chosen = poll_answer.option_ids[0]
    is_correct = chosen == info["correct_option"]

    session = await get_active_session(poll_answer.user.id)
    if not session or session["id"] != info["session_id"]:
        return  # stale poll from an abandoned/replaced session

    new_score = session["score"] + (1 if is_correct else 0)
    new_index = session["current_index"] + 1

    await save_answer(info["session_id"], info["question_id"], chosen, is_correct)
    await update_session(info["session_id"], new_index, new_score)

    try:
        await bot.stop_poll(info["chat_id"], info["message_id"])
    except Exception:
        pass  # poll already closed/inaccessible — not fatal

    quiz = await get_quiz(info["quiz_id"])
    if new_index >= quiz["total"]:
        await finish_quiz(bot, info["chat_id"], info["session_id"], info["quiz_id"], new_score, quiz["total"])
    else:
        next_q = await get_question(info["quiz_id"], new_index)
        await send_question_poll(bot, info["chat_id"], info["session_id"], info["quiz_id"],
                                  next_q, new_index, quiz["total"])


async def finish_quiz(bot: Bot, chat_id: int, session_id: int, quiz_id: int, score: int, total: int):
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Пройти ещё раз", callback_data=f"start_quiz:{quiz_id}")
    ]])

    await bot.send_message(chat_id, result, reply_markup=keyboard)
