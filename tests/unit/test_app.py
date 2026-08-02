from app.main import app


def test_app_importable():
    assert app is not None
