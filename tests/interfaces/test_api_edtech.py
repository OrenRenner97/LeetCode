import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
URL = "/v1/edtech/railfence"


def test_encrypt_with_grid():
    data = client.post(f"{URL}/encrypt", json={"text": "WEAREDISCOVERED", "key": {"rails": 3}, "with_grid": True}).json()
    assert data == {"ciphertext": "WECRERDSOEEAIVD",
                    "grid": ["W...E...C...R..", ".E.R.D.S.O.E.E.", "..A...I...V...D"]}


def test_encrypt_letters_and_groups_then_decrypt():
    body = {"text": "Meet me at nine!", "key": {"rails": 4, "offset": 5}, "letters_only": True, "group_by": 5}
    cipher = client.post(f"{URL}/encrypt", json=body).json()["ciphertext"]
    assert all(len(block) <= 5 for block in cipher.split())
    plain = client.post(f"{URL}/decrypt", json={"ciphertext": cipher.replace(" ", ""),
                                                 "key": {"rails": 4, "offset": 5}}).json()["plaintext"]
    assert plain == "MEETMEATNINE"


def test_crack():
    text = "Meet me at the north gate of the park at nine and bring the map and a flashlight"
    cipher = client.post(f"{URL}/encrypt", json={"text": text, "key": {"rails": 6, "offset": 2}}).json()["ciphertext"]
    data = client.post(f"{URL}/crack", json={"ciphertext": cipher, "top": 3}).json()
    assert data["language"] == "en" and len(data["candidates"]) <= 3
    found = [c["plaintext"] for c in data["candidates"][:1] + data["rotations"]]
    assert text in found


def test_bad_key_is_422():
    for key in ({"rails": 3, "offset": 4}, {"rails": 0}):
        assert client.post(f"{URL}/decrypt", json={"ciphertext": "abc", "key": key}).status_code == 422


def test_bad_backend_is_400():
    r = client.post(f"{URL}/decrypt", json={"ciphertext": "abc", "key": {"rails": 2}, "backend": "quantum"})
    assert r.status_code == 400
