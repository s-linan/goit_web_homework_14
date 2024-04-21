from unittest.mock import Mock

import pytest
from tests.conftest import TestingSessionLocal

user_data = {"username": "bober", "email": "okurvabober@gmail.com", "password": "123456789"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data

