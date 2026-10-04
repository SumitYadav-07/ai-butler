import json
import logging
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.client import AIUnavailable, call_llm
from app.ai.context import build_context
from app.ai.guard import check_sensitive
from app.ai.prompts import SYSTEM_PROMPT
from app.models import AIConversation, User

logger = logging.getLogger("ai_butler")

INVEST_EDUCATION = (
    "I can't tell you whether to buy or sell a particular stock, but here are some general things "
    "people usually think about:\n"
    "- Do you have an emergency fund first? Investments can go down as well as up.\n"
    "- How long can you leave the money untouched? Short timelines make market swings riskier.\n"
    "- Are you spreading risk, or putting everything in one place?\n"
    "- What fees and taxes apply?\n"
    "- Only invest money you won't need soon.\n"
    "Please do your own research or speak to a registered financial advisor. This is general "
    "education, not advice."
)


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _fallback(ctx: dict) -> str:
    if ctx["intent"] == "invest":
        return INVEST_EDUCATION
    body = "\n".join(f"- {line}" for line in ctx["lines"]) or "- I don't have any calculations for that question."
    return ("My AI helper isn't available right now, but here is what I calculated from the numbers "
            f"you entered:\n{body}\n\nThese are calculations only, not financial advice.")


def _ask_amount(intent: str) -> str:
    if intent == "emi":
        return "Tell me the monthly EMI amount you're considering, for example ₹4,000, and I'll check it against what you've entered."
    return "Tell me the amount you're thinking of spending, for example ₹3,000, and I'll check it against what you've entered."


def _history(db: Session, user: User, limit: int = 6) -> list[dict]:
    rows = db.scalars(select(AIConversation).where(AIConversation.user_id == user.id)
                      .order_by(AIConversation.id.desc()).limit(limit)).all()
    return [{"role": r.role, "content": r.message} for r in reversed(rows)]


def _normalize(messages: list[dict]) -> list[dict]:
    """The API needs the first message from the user and roles that alternate."""
    out: list[dict] = []
    for m in messages:
        if not out and m["role"] != "user":
            continue
        if out and out[-1]["role"] == m["role"]:
            out[-1]["content"] += "\n" + m["content"]
        else:
            out.append(dict(m))
    return out


def _final_turn(ctx: dict, message: str) -> str:
    payload = {k: ctx[k] for k in ("intent", "today", "currency", "not_entered_yet", "lines", "data")}
    return f"<context>\n{json.dumps(payload, ensure_ascii=False)}\n</context>\n\nUser question: {message}"


def _response(reply: str, intent: str, used_ai: bool, missing=None, notice=None) -> dict:
    return {"reply": reply, "intent": intent, "used_ai": used_ai,
            "missing_info": missing or [], "notice": notice}


def answer(db: Session, user: User, message: str, today: date) -> dict:
    blocked = check_sensitive(message)
    if blocked:
        return _response(blocked, "privacy_guard", False)  # not stored, not sent to the AI

    ctx = build_context(db, user, message, today)
    notice = None
    if ctx["missing"]:
        reply = f"I don't have enough information to calculate that. Please enter your {_join(ctx['missing'])}."
        used_ai = False
    elif ctx["needs_amount"]:
        reply, used_ai = _ask_amount(ctx["intent"]), False
    else:
        messages = _normalize([*_history(db, user), {"role": "user", "content": _final_turn(ctx, message)}])
        try:
            reply, used_ai = call_llm(SYSTEM_PROMPT, messages), True
        except AIUnavailable as exc:
            logger.warning("AI unavailable: %s", exc)
            reply, used_ai = _fallback(ctx), False
            notice = "The AI helper is unavailable right now, so this answer shows calculations only."

    db.add_all([AIConversation(user_id=user.id, role="user", message=message[:4000]),
                AIConversation(user_id=user.id, role="assistant", message=reply[:4000])])
    db.commit()
    return _response(reply, ctx["intent"], used_ai, ctx["missing"], notice)


def history(db: Session, user: User, limit: int = 50) -> list[dict]:
    rows = db.scalars(select(AIConversation).where(AIConversation.user_id == user.id)
                      .order_by(AIConversation.id.desc()).limit(limit)).all()
    return [{"role": r.role, "message": r.message, "created_at": r.created_at.isoformat()}
            for r in reversed(rows)]


def clear_history(db: Session, user: User) -> None:
    db.execute(delete(AIConversation).where(AIConversation.user_id == user.id))
    db.commit()