def test_fastapi_app_importable():
    from api.main import app

    assert app.title.startswith("Project")
