import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                total INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_option INTEGER NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                quiz_id INTEGER NOT NULL REFERENCES quizzes(id),
                current_index INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                is_finished BOOLEAN DEFAULT FALSE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_answers (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                question_id INTEGER NOT NULL REFERENCES questions(id),
                chosen_option INTEGER NOT NULL,
                is_correct BOOLEAN NOT NULL
            );
        """)


# ── Quizzes ──────────────────────────────────────────────────

async def create_quiz(user_id: int, title: str, total: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO quizzes (user_id, title, total) VALUES ($1, $2, $3) RETURNING id",
            user_id, title, total
        )
        return row["id"]


async def get_user_quizzes(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM quizzes WHERE user_id=$1 ORDER BY created_at DESC",
            user_id
        )
        return [dict(r) for r in rows]


async def get_quiz(quiz_id: int) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM quizzes WHERE id=$1", quiz_id)
        return dict(row) if row else None


# ── Questions ────────────────────────────────────────────────

async def save_questions(quiz_id: int, questions: list[dict]):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO questions (quiz_id, question_text, options, correct_option) VALUES ($1, $2, $3, $4)",
            [(quiz_id, q["text"], "|".join(q["options"]), q["correct"]) for q in questions]
        )


async def get_question(quiz_id: int, index: int) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM questions WHERE quiz_id=$1 ORDER BY id LIMIT 1 OFFSET $2",
            quiz_id, index
        )
        if not row:
            return None
        d = dict(row)
        d["options"] = d["options"].split("|")
        return d


async def get_all_questions(quiz_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM questions WHERE quiz_id=$1 ORDER BY id", quiz_id
        )
        result = []
        for r in rows:
            d = dict(r)
            d["options"] = d["options"].split("|")
            result.append(d)
        return result


# ── Sessions ─────────────────────────────────────────────────

async def create_session(user_id: int, quiz_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sessions SET is_finished=TRUE WHERE user_id=$1 AND is_finished=FALSE",
            user_id
        )
        row = await conn.fetchrow(
            "INSERT INTO sessions (user_id, quiz_id) VALUES ($1, $2) RETURNING id",
            user_id, quiz_id
        )
        return row["id"]


async def get_active_session(user_id: int) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM sessions WHERE user_id=$1 AND is_finished=FALSE ORDER BY id DESC LIMIT 1",
            user_id
        )
        return dict(row) if row else None


async def update_session(session_id: int, current_index: int, score: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sessions SET current_index=$1, score=$2 WHERE id=$3",
            current_index, score, session_id
        )


async def finish_session(session_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sessions SET is_finished=TRUE WHERE id=$1", session_id
        )


# ── Answers ──────────────────────────────────────────────────

async def save_answer(session_id: int, question_id: int, chosen: int, is_correct: bool):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO user_answers (session_id, question_id, chosen_option, is_correct) VALUES ($1, $2, $3, $4)",
            session_id, question_id, chosen, is_correct
        )


async def get_session_answers(session_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_answers WHERE session_id=$1 ORDER BY id", session_id
        )
        return [dict(r) for r in rows]