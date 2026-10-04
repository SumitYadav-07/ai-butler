import re

_CARD_LIKE = re.compile(r"\b(?:\d[ -]?){12,19}\b")
_CREDENTIAL_WITH_DIGITS = re.compile(
    r"\b(otp|cvv|upi pin|atm pin|card pin|password)\b[^0-9]{0,15}\d{3,}", re.I
)

WARNING = (
    "Please don't share card numbers, PINs, OTPs or passwords here. I never need them: "
    "everything I do comes from the amounts you type into this app. "
    "I haven't saved that message."
)


def check_sensitive(message: str) -> str | None:
    """Return a warning if the message looks like it contains banking credentials."""
    if _CARD_LIKE.search(message) or _CREDENTIAL_WITH_DIGITS.search(message):
        return WARNING
    return None