import re

_WHY = [r"why .*(spend|spent|expens)", r"\bincreas", r"gone up", r"higher than"]
_SPENT_ON = [r"(spent|spend|spending) on"]
_INVEST = [r"\bstocks?\b", r"\bshares?\b", r"mutual fund", r"crypto", r"bitcoin",
           r"\binvest", r"\bnifty\b", r"\bsensex\b", r"\bipo\b", r"\btrading\b"]
_EMI = [r"\bemis?\b", r"\bloan", r"\binstal+ments?\b"]
_OVERSPEND = [r"overspend", r"spending too much", r"too much", r"am i spending"]
_BIGGEST = [r"biggest", r"largest", r"highest", r"top (expense|categor)", r"most (money|expensive)"]
_EMERGENCY = [r"emergenc"]
_SAVE = [r"\bsave\b", r"\bsaving"]
_DAILY = [r"spend today", r"spend (per|each) day", r"per day", r"daily", r"safe to spend"]
_AFFORD = [r"afford", r"\bbuy\b", r"purchase", r"worth (buying|it)"]

CATEGORY_WORDS = {
    "Food": ["food", "grocery", "groceries", "restaurant", "eating", "lunch", "dinner", "snack"],
    "Transport": ["transport", "commute", "metro", "bus", "fuel", "petrol", "cab"],
    "Shopping": ["shopping", "clothes"],
    "Entertainment": ["entertainment", "movie", "game", "gaming", "subscription"],
    "Bills": ["bill", "electricity", "recharge"],
    "Education": ["education", "tuition", "book", "course", "fee"],
    "Healthcare": ["healthcare", "medical", "medicine", "doctor", "health"],
    "Rent": ["rent"],
    "EMI": ["emi"],
    "Travel": ["travel", "trip", "vacation", "flight"],
    "Investments": ["investment"],
}

_AMOUNT = re.compile(
    r"(₹|rs\.?|inr)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|lakhs?|lacs?)?(?![a-z0-9])", re.I
)
_MULTIPLIER = {"k": 1_000, "thousand": 1_000, "lakh": 100_000, "lakhs": 100_000,
               "lac": 100_000, "lacs": 100_000}


def _has(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def detect_intent(message: str) -> str:
    t = message.lower()
    if _has(t, _WHY):
        return "why_increase"
    if _has(t, _SPENT_ON):
        return "category_spend"
    if _has(t, _INVEST):
        return "invest"
    if _has(t, _EMI):
        return "emi"
    if _has(t, _OVERSPEND):
        return "overspending"
    if _has(t, _BIGGEST):
        return "biggest"
    if _has(t, _EMERGENCY):
        return "emergency"
    if _has(t, _SAVE):
        return "save"
    if _has(t, _DAILY):
        return "daily_spend"
    if _has(t, _AFFORD) or (re.search(r"can i spend", t) and re.search(r"\d", t)):
        return "affordability"
    if re.search(r"can i spend", t):
        return "daily_spend"
    return "general"


def extract_amount(message: str) -> float | None:
    """Pull a rupee amount out of a question. Prefers amounts marked with ₹/Rs/INR."""
    fallback = None
    for m in _AMOUNT.finditer(message):
        value = float(m.group(2).replace(",", "")) * _MULTIPLIER.get((m.group(3) or "").lower(), 1)
        if value <= 0:
            continue
        if m.group(1):
            return value
        if fallback is None:
            fallback = value
    return fallback


def extract_category(message: str) -> str | None:
    t = message.lower()
    for category, words in CATEGORY_WORDS.items():
        for w in words:
            if re.search(rf"\b{re.escape(w)}(?:s|es)?\b", t):
                return category
    return None