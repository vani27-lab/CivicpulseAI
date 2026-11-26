from app.modules.ai_engine.language import (detect_language, normalize_language_code, reconcile_language)


def test_hindi_script():
    assert detect_language("यहाँ सड़क पर बहुत बड़ा गड्ढा है।") == "hi"


def test_english():
    assert detect_language("There is a big pothole") == "en"


def test_tamil():
    assert detect_language("சாலையில் பள்ளம்") == "ta"


def test_empty_is_undetermined():
    assert detect_language("   ") == "und"


def test_hint_wins():
    assert detect_language("There is a pothole", hint="Hindi") == "hi"
    assert normalize_language_code("hi-IN") == "hi"
    assert normalize_language_code("!!") is None


def test_reconcile_romanised_hindi():
    assert reconcile_language("en", "hi", "sadak par gadda hai") == "hi"
    assert reconcile_language("en", "hi", "sadak par gadda hai", hint="en") == "en"
    assert reconcile_language("hi", "en", "सड़क") == "hi"
