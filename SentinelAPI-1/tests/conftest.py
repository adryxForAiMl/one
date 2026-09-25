import pytest

@pytest.fixture(scope="session")
def test_client():
    from app.main import app
    with app.test_client() as client:
        yield client