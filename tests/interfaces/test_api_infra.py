import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
URL = "/v1/infra/rowkeys"


def test_encode_decode_roundtrip():
    data = client.post(f"{URL}/encode", json={"ids": [1000000001, 1000000123]}).json()
    assert data["scheme"] == {"storage": "int64", "width": 18, "reverse": True, "safe": True}
    assert data["keys"] == ["100000000100000000", "321000000100000000"] and data["errors"] == []
    ids = client.post(f"{URL}/decode", json={"keys": data["keys"]}).json()["ids"]
    assert ids == ["1000000001", "1000000123"]


def test_encode_overflow_reported_per_id():
    body = {"ids": [1000000009, 1000000099, -1], "scheme": {"storage": "int64", "width": 19}}
    data = client.post(f"{URL}/encode", json=body).json()
    assert data["scheme"]["safe"] is False
    assert data["keys"] == ["9000000001000000000", None, None]
    assert [e["id"] for e in data["errors"]] == ["1000000099", "-1"]


def test_string_keys_no_collisions():
    body = {"ids": [12, 120, 1200], "scheme": {"storage": "string", "width": 4}}
    keys = client.post(f"{URL}/encode", json=body).json()["keys"]
    assert keys == ["2100", "0210", "0021"]
    body = {"keys": keys + ["12", "abcd"], "scheme": {"storage": "string", "width": 4}}
    assert client.post(f"{URL}/decode", json=body).json()["ids"] == ["12", "120", "1200", None, None]


def test_decode_rejects_non_ascii_numbers():
    ids = client.post(f"{URL}/decode", json={"keys": [" 12", "١٢", "-5", "12"]}).json()["ids"]
    assert ids == [None, None, None, "21" + "0" * 16]


def test_hotspot():
    data = client.post(f"{URL}/hotspot", json={"start": 1000000000, "count": 20000, "regions": 8}).json()
    assert data["direct"]["regions_touched"] == 1 and data["direct"]["hottest_share"] == 1.0
    assert data["reversed"]["regions_touched"] == 8 and data["reversed"]["skew"] < 1.01


def test_hotspot_bad_range_is_400():
    body = {"start": 10**9, "count": 10, "scheme": {"storage": "int32", "width": 10}}
    r = client.post(f"{URL}/hotspot", json=body)
    assert r.status_code == 400 and "int32" in r.json()["detail"]
    r = client.post(f"{URL}/hotspot", json={"start": 99_990, "count": 100, "scheme": {"width": 5}})
    assert r.status_code == 400


def test_validation_422():
    assert client.post(f"{URL}/encode", json={"ids": []}).status_code == 422
    assert client.post(f"{URL}/encode", json={"ids": [1], "scheme": {"storage": "int128"}}).status_code == 422
    assert client.post(f"{URL}/hotspot", json={"start": 0, "count": 0}).status_code == 422
