from app.ai.guard import check_sensitive
from app.ai.intents import detect_intent, extract_amount, extract_category
from app.utils.formatting import inr


def test_inr_uses_indian_grouping():
    assert inr(950) == "₹950"
    assert inr(25000) == "₹25,000"
    assert inr(120000) == "₹1,20,000"
    assert inr(1234567) == "₹12,34,567"
    assert inr(-1500) == "-₹1,500"


def test_extract_amount():
    assert extract_amount("Can I afford a ₹3,000 purchase?") == 3000
    assert extract_amount("buy a laptop for 45k") == 45000
    assert extract_amount("Can I afford another EMI of 4000?") == 4000
    assert extract_amount("I can pay 2 lakh") == 200000
    assert extract_amount("How much can I spend today?") is None


def test_detect_intent():
    cases = {
        "Can I afford a ₹3,000 purchase?": "affordability",
        "How much can I spend today?": "daily_spend",
        "How much have I spent on food this month?": "category_spend",
        "Am I overspending?": "overspending",
        "Can I afford another EMI of ₹4,000?": "emi",
        "How much should I save this month?": "save",
        "How much money should I keep for emergencies?": "emergency",
        "Why did my spending increase this month?": "why_increase",
        "What are my biggest expenses?": "biggest",
        "Should I buy this stock?": "invest",
    }
    for question, expected in cases.items():
        assert detect_intent(question) == expected, question


def test_extract_category():
    assert extract_category("How much have I spent on food this month?") == "Food"
    assert extract_category("What did I spend on groceries?") == "Food"
    assert extract_category("How is my month going?") is None


def test_guard_blocks_credentials_but_not_normal_questions():
    assert check_sensitive("my otp is 123456") is not None
    assert check_sensitive("card 4111 1111 1111 1111") is not None
    assert check_sensitive("Can I afford ₹3,000?") is None