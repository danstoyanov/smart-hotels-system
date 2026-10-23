import json
import shutil

import pytest
from fastapi.testclient import TestClient

from backend.app.hotel import HotelDataError, HotelStore
from backend.app.main import create_app
from backend.app.runtime import new_loop
from backend.app.settings import ROOT, Settings


@pytest.fixture
def hotel_dir(tmp_path):
    target = tmp_path / "hotel"
    shutil.copytree(ROOT / "hotel", target)
    return target


def update_source(directory, change):
    path = directory / "revisions/royal-crest-demo.v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_complete_reads_and_unknowns(hotel_dir):
    store = HotelStore(hotel_dir)
    assert store.get_rooms()["status"] == "unavailable"
    store.reload()
    rooms = store.get_rooms()
    assert rooms["source"] == {"source_id": "royal-crest-demo", "version": 1, "demo": True}
    assert rooms["hotel"] == {
        "name": "Royal Crest Manor",
        "language": "en",
        "timezone": "Europe/Kyiv",
    }
    assert len(rooms["data"]) == 2
    assert rooms["data"][0]["capacity"] == 2
    assert store.get_amenities("wifi")["data"][0]["description"]
    arrival = store.get_policy("arrival")
    assert "15:00" in arrival["data"][0]["body"]
    assert "11:00" in arrival["data"][0]["body"]
    assert store.get_policy("prices")["status"] == "unknown"
    assert store.get_policy("absent")["status"] == "not_found"
    assert store.get_rooms("absent")["data"] == []
    assert len(store.read("inventory")["data"]) == 14
    assert not any(row["night"] == "2026-11-08" for row in store.read("inventory")["data"])
    # A caller cannot mutate the shared snapshot.
    rooms["data"][0]["beds"].append("invented")
    assert store.get_rooms()["data"][0]["beds"] == ["1 king bed"]


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(demo=False),
        lambda d: d.update(timezone="Invalid/Place"),
        lambda d: d["rooms"][0].update(capacity=0),
        lambda d: d["rooms"][0].update(capacity="2"),
        lambda d: d["rooms"][0].update(amenity_ids=["missing"]),
        lambda d: d["rooms"].append(d["rooms"][0]),
        lambda d: d["inventory"][0].update(room_id="missing"),
        lambda d: d["inventory"][0].update(night="2026-02-30"),
        lambda d: d["inventory"].append(d["inventory"][0]),
        lambda d: d["policies"][0].update(body=""),
        lambda d: d["policies"][0].update(body=" \n\t "),
        lambda d: d["rooms"][0].update(name="   "),
        lambda d: d.update(version=2),
        lambda d: d.update(unexpected="field"),
    ],
)
def test_invalid_candidate_keeps_last_valid_snapshot(hotel_dir, change):
    store = HotelStore(hotel_dir)
    store.reload()
    before = store.get_rooms()
    update_source(hotel_dir, change)
    with pytest.raises(HotelDataError):
        store.reload()
    assert store.get_rooms() == before


def test_safe_version_reload_preserves_old_sources(hotel_dir):
    store = HotelStore(hotel_dir)
    store.reload()
    assert store.reload()["version"] == 1
    original = store.get_policy("arrival")
    old_path = hotel_dir / "revisions/royal-crest-demo.v1.json"
    data = json.loads(old_path.read_text(encoding="utf-8"))
    data["version"] = 2
    data["policies"][0]["body"] = "Revised fictional demo policy. Check-in starts at 16:00."
    new_path = hotel_dir / "revisions/royal-crest-demo.v2.json"
    new_path.write_text(json.dumps(data), encoding="utf-8")
    catalogue_path = hotel_dir / "catalogue.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    catalogue["active_version"] = 2
    catalogue["sources"].append(
        {
            "source_id": "royal-crest-demo",
            "version": 2,
            "file": "revisions/royal-crest-demo.v2.json",
        }
    )
    catalogue_path.write_text(json.dumps(catalogue), encoding="utf-8")
    assert store.reload()["version"] == 2
    assert "16:00" in store.get_policy("arrival")["data"][0]["body"]
    assert store.read("policies", "arrival", source_id="royal-crest-demo", version=1) == original
    # Earlier citations also work after a new process starts.
    restarted = HotelStore(hotel_dir)
    restarted.reload()
    assert (
        restarted.read("policies", "arrival", source_id="royal-crest-demo", version=1) == original
    )
    update_source(hotel_dir, lambda d: d["rooms"][0].update(name="Changed without version"))
    with pytest.raises(HotelDataError, match="unchanged"):
        store.reload()
    assert store.catalogue()["active"]["version"] == 2


@pytest.mark.parametrize("file_value", ["../outside.json", "revisions/missing.json"])
def test_missing_and_escaping_files_are_rejected(hotel_dir, file_value):
    path = hotel_dir / "catalogue.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["sources"][0]["file"] = file_value
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(HotelDataError):
        HotelStore(hotel_dir).reload()


def test_invalid_json_and_missing_catalogue(hotel_dir):
    path = hotel_dir / "catalogue.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(HotelDataError):
        HotelStore(hotel_dir).reload()
    path.unlink()
    with pytest.raises(HotelDataError):
        HotelStore(hotel_dir).reload()


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("bad-section",), {}),
        (("rooms",), {"source_id": "royal-crest-demo"}),
        (("rooms",), {"source_id": [], "version": 1}),
        (("rooms",), {"source_id": "royal-crest-demo", "version": True}),
        (("rooms", []), {}),
        (("inventory", "some-id"), {}),
    ],
)
def test_invalid_tool_input_is_clear(hotel_dir, args, kwargs):
    store = HotelStore(hotel_dir)
    store.reload()
    assert store.read(*args, **kwargs)["status"] == "invalid_input"


def test_http_reads_revisions_and_no_reload_endpoint(hotel_dir):
    app = create_app(Settings(_env_file=None), hotel_directory=hotel_dir)
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        assert client.get("/api/hotel/catalogue").json()["active"]["version"] == 1
        assert client.get("/api/hotel/rooms/manor-suite").json()["data"][0]["capacity"] == 2
        assert client.get("/api/hotel/amenities").status_code == 200
        assert client.get("/api/hotel/policies/prices").json()["status"] == "unknown"
        assert client.get("/api/hotel/policies/missing").status_code == 404
        assert (
            client.get("/api/hotel/rooms?source_id=royal-crest-demo&version=9").status_code == 404
        )
        assert client.get("/api/hotel/rooms?source_id=royal-crest-demo").status_code == 422
        assert client.get("/api/hotel/rooms?version=0").status_code == 422
        assert client.post("/api/hotel/reload").status_code in (404, 405)
        assert client.get("/hotel/catalogue.json").status_code == 404


def test_invalid_startup_returns_safe_unavailable(tmp_path):
    app = create_app(Settings(_env_file=None), hotel_directory=tmp_path)
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        response = client.get("/api/hotel/rooms")
        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"
        assert str(tmp_path) not in response.text
        assert client.get("/").status_code == 200


def test_wrong_hotel_is_not_served(hotel_dir):
    app = create_app(
        Settings(_env_file=None, hotel_name="Another Hotel"), hotel_directory=hotel_dir
    )
    with TestClient(app, backend_options={"loop_factory": new_loop}) as client:
        assert client.get("/api/hotel/rooms").status_code == 503


def test_failed_new_revision_does_not_publish_or_drop_old_citations(hotel_dir):
    store = HotelStore(hotel_dir)
    store.reload()
    before = store.get_policy("arrival")
    path = hotel_dir / "catalogue.json"
    catalogue = json.loads(path.read_text(encoding="utf-8"))
    catalogue["active_version"] = 2
    catalogue["sources"].append(
        {"source_id": "royal-crest-demo", "version": 2, "file": "missing-v2.json"}
    )
    path.write_text(json.dumps(catalogue), encoding="utf-8")
    with pytest.raises(HotelDataError):
        store.reload()
    assert store.get_policy("arrival") == before
    assert store.catalogue()["active"]["version"] == 1
    # Fixing the failed candidate allows a safe retry.
    catalogue["active_version"] = 1
    catalogue["sources"] = catalogue["sources"][:1]
    path.write_text(json.dumps(catalogue), encoding="utf-8")
    assert store.reload()["status"] == "ok"
