import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
URL = "/v1/biotech/cloning"


def test_enzymes_catalog():
    data = client.get(f"{URL}/enzymes").json()
    eco = next(e for e in data if e["name"] == "EcoRI")
    assert eco == {"name": "EcoRI", "pattern": "G^AATTC", "ends": "5'", "overhang": "AATT"}


def test_restriction_map_circular():
    body = {"sequence": "ATTCaaaaGGATCCaaaaGA", "circular": True, "enzymes": ["EcoRI", "BamHI", "NotI"]}
    data = client.post(f"{URL}/restriction-map", json=body).json()
    sites = {e["name"]: e["sites"] for e in data["enzymes"]}
    assert sites == {"EcoRI": [{"position": 18, "cut": 19}], "BamHI": [{"position": 8, "cut": 9}], "NotI": []}
    assert data["unique_cutters"] == ["EcoRI", "BamHI"] and data["non_cutters"] == ["NotI"]
    assert (data["length"], data["cuts"], data["fragments"]) == (20, [9, 19], [10, 10])


def test_custom_enzyme():
    body = {"sequence": "ttGAGCTCaa", "enzymes": ["SacI"], "custom_enzymes": [{"name": "Eco53kI", "pattern": "GAG^CTC"}]}
    data = client.post(f"{URL}/restriction-map", json=body).json()
    assert [(e["name"], e["ends"], e["sites"][0]["cut"]) for e in data["enzymes"]] == [("SacI", "3'", 7),
                                                                                       ("Eco53kI", "blunt", 5)]


def test_candidates():
    body = {"vector": "ATATATATAT" "GAATTCGGATCCAAGCTT" "ATATATATAT", "insert": "ATGGCCGGATCCTTTAAA",
            "mcs_start": 10, "mcs_end": 28, "enzymes": ["EcoRI", "BamHI", "HindIII"]}
    data = client.post(f"{URL}/candidates", json=body).json()
    assert [(c["name"], c["cut"]) for c in data["candidates"]] == [("EcoRI", 11), ("HindIII", 23)]


def test_primer_check():
    body = {"primers": ["ATGACCATGATTACGCCAAG", "gtaaaacgacggccagtGAATTC", "ACGTN"]}
    reports = client.post(f"{URL}/primer-check", json=body).json()["reports"]
    assert [r["verdict"] for r in reports] == ["ok", "self_dimer", "has_n"]
    assert (reports[1]["stem"], reports[1]["stem_3prime"]) == ("GAATTC", 6)


@pytest.mark.parametrize("path, body", [
    ("restriction-map", {"sequence": "GAATTX"}),                                        # не ДНК
    ("restriction-map", {"sequence": "GAATTC", "enzymes": ["EcoRJ"]}),                  # нет в каталоге
    ("restriction-map", {"sequence": "GAATTC", "custom_enzymes": [{"name": "BsaI", "pattern": "GGTCTC^"}]}),
    ("restriction-map", {"sequence": "GAATTC", "enzymes": ["EcoRI"],
                         "custom_enzymes": [{"name": "EcoRI", "pattern": "G^AATTC"}]}),  # повтор имени
    ("candidates", {"vector": "GAATTC", "insert": "", "mcs_start": 3, "mcs_end": 10}),   # MCS вне вектора
    ("primer-check", {"primers": [""]}),
])
def test_validation(path, body):
    assert client.post(f"{URL}/{path}", json=body).status_code == 422


def test_bad_backend():
    r = client.post(f"{URL}/primer-check", json={"primers": ["ACGT"], "backend": "quantum"})
    assert r.status_code == 400
