"""Validated local demo information. No booking or availability decisions happen here."""

import argparse
import json
import logging
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from backend.app.settings import ROOT

ID = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")]
Text = Annotated[str, Field(min_length=1, max_length=12000)]
Version = Annotated[int, Field(ge=1)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Room(Record):
    id: ID
    name: Text
    description: Text
    capacity: Annotated[int, Field(ge=1, le=20)]
    bedrooms: Annotated[int, Field(ge=1, le=10)]
    beds: Annotated[list[Text], Field(min_length=1, max_length=20)]
    amenity_ids: list[ID]


class Amenity(Record):
    id: ID
    name: Text
    description: Text


class Policy(Record):
    id: ID
    title: Text
    status: Literal["known", "unknown"]
    body: Text


class Night(Record):
    room_id: ID
    night: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    open: bool

    @field_validator("night")
    @classmethod
    def valid_date(cls, value):
        from datetime import date

        date.fromisoformat(value)
        return value


class HotelData(Record):
    schema_version: Literal[1]
    source_id: ID
    version: Version
    demo: Literal[True]
    name: Text
    language: Annotated[str, Field(pattern=r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")]
    timezone: Text
    rooms: Annotated[list[Room], Field(min_length=1, max_length=50)]
    amenities: Annotated[list[Amenity], Field(min_length=1, max_length=100)]
    policies: Annotated[list[Policy], Field(min_length=1, max_length=100)]
    inventory: Annotated[list[Night], Field(max_length=40000)]

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Use an IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def valid_links(self):
        for rows in (self.rooms, self.amenities, self.policies):
            ids = [row.id for row in rows]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate record ID")
        amenities = {item.id for item in self.amenities}
        rooms = {room.id for room in self.rooms}
        for room in self.rooms:
            if len(room.amenity_ids) != len(set(room.amenity_ids)):
                raise ValueError("Duplicate room amenity")
            if not set(room.amenity_ids) <= amenities:
                raise ValueError("Room references an unknown amenity")
        nights = [(item.room_id, item.night) for item in self.inventory]
        if len(nights) != len(set(nights)):
            raise ValueError("Duplicate inventory night")
        if any(item.room_id not in rooms for item in self.inventory):
            raise ValueError("Inventory references an unknown room")
        return self


class Source(Record):
    source_id: ID
    version: Version
    file: Text


class Catalogue(Record):
    schema_version: Literal[1]
    sources: Annotated[list[Source], Field(min_length=1, max_length=100)]
    active_source_id: ID
    active_version: Version


class HotelDataError(ValueError):
    """An invalid candidate was not published."""


def load_data(directory: Path):
    """Validate every listed revision before returning a candidate snapshot."""
    directory = directory.resolve()

    def read_file(path):
        path = path.resolve()
        if not path.is_relative_to(directory) or path.suffix != ".json":
            raise HotelDataError("Source must be a JSON file inside hotel/")
        if path.stat().st_size > 4_000_000:
            raise HotelDataError("Hotel file is too large")
        return path.read_text(encoding="utf-8")

    try:
        catalogue = Catalogue.model_validate_json(read_file(directory / "catalogue.json"))
        snapshot = {}
        for source in catalogue.sources:
            key = (source.source_id, source.version)
            if key in snapshot:
                raise HotelDataError("Duplicate source ID/version")
            data = HotelData.model_validate_json(read_file(directory / source.file))
            if key != (data.source_id, data.version):
                raise HotelDataError("Catalogue and source ID/version do not match")
            snapshot[key] = data.model_dump(mode="json")
        active = (catalogue.active_source_id, catalogue.active_version)
        if active not in snapshot:
            raise HotelDataError("Active source is missing from the catalogue")
        return snapshot, active
    except (OSError, UnicodeError, ValidationError) as exc:
        raise HotelDataError(
            "Missing or invalid hotel data; run the hotel validation command"
        ) from exc


class HotelStore:
    """Publish complete snapshots. Readers receive copies, never mutable stored data."""

    def __init__(self, directory: Path = ROOT / "hotel", *, expected_hotel=None):
        self.directory = directory
        self.expected_hotel = expected_hotel
        self._snapshot = {}
        self._active = None
        self._lock = RLock()

    def reload(self):
        with self._lock:
            candidate, active = load_data(self.directory)
            if self.expected_hotel is not None:
                identity = tuple(candidate[active][key] for key in ("name", "language", "timezone"))
                if identity != self.expected_hotel:
                    raise HotelDataError(
                        "Active hotel identity does not match application settings"
                    )
            for key, old in self._snapshot.items():
                if key not in candidate or old != candidate[key]:
                    raise HotelDataError(
                        "Keep published revisions unchanged and listed; add a version"
                    )
            # No state changes occur until all files and revision checks pass.
            self._snapshot, self._active = candidate, active
        return {"status": "ok", "source_id": active[0], "version": active[1], "demo": True}

    def catalogue(self):
        with self._lock:
            if self._active is None:
                return {"status": "unavailable", "message": "Hotel data is not loaded"}
            return {
                "status": "ok",
                "demo": True,
                "active": {"source_id": self._active[0], "version": self._active[1]},
                "sources": [{"source_id": key[0], "version": key[1]} for key in self._snapshot],
            }

    def read(self, section: str, item_id: str | None = None, *, source_id=None, version=None):
        with self._lock:
            if self._active is None:
                return {"status": "unavailable", "message": "Hotel data is not loaded"}
            if not isinstance(section, str) or section not in {
                "rooms",
                "amenities",
                "policies",
                "inventory",
            }:
                return {"status": "invalid_input", "message": "Unknown hotel section"}
            if (source_id is None) != (version is None):
                return {"status": "invalid_input", "message": "Supply both source_id and version"}
            if (
                (item_id is not None and not isinstance(item_id, str))
                or (source_id is not None and not isinstance(source_id, str))
                or (version is not None and (type(version) is not int or version < 1))
            ):
                return {"status": "invalid_input", "message": "Invalid ID or source version"}
            key = self._active if source_id is None else (source_id, version)
            data = self._snapshot.get(key)
            if data is None:
                return {"status": "not_found", "message": "Source revision is not listed"}
            rows = data[section]
            if item_id is not None:
                if section == "inventory":
                    return {
                        "status": "invalid_input",
                        "message": "Read inventory as a complete list",
                    }
                rows = [row for row in rows if row["id"] == item_id]
            result = {
                "status": "ok" if rows else "not_found",
                "source": {"source_id": key[0], "version": key[1], "demo": True},
                "hotel": {name: data[name] for name in ("name", "language", "timezone")},
                "section": section,
                "data": rows,
            }
            if len(rows) == 1 and section == "policies" and rows[0]["status"] == "unknown":
                result["status"] = "unknown"
            # JSON copying also prevents callers changing nested stored records.
            return json.loads(json.dumps(result))

    def get_rooms(self, room_id=None):
        return self.read("rooms", room_id)

    def get_amenities(self, amenity_id=None):
        return self.read("amenities", amenity_id)

    def get_policy(self, policy_id):
        return self.read("policies", policy_id)


def main():
    parser = argparse.ArgumentParser(
        description="Validate local demo hotel files without publishing"
    )
    parser.add_argument("--directory", type=Path, default=ROOT / "hotel")
    args = parser.parse_args()
    try:
        result = HotelStore(args.directory).reload()
    except HotelDataError as exc:
        logging.error("%s", exc)
        if isinstance(exc.__cause__, ValidationError):
            for error in exc.__cause__.errors(include_input=False, include_url=False):
                logging.error("%s: %s", ".".join(map(str, error["loc"])), error["msg"])
        elif isinstance(exc.__cause__, OSError):
            logging.error("%s", exc.__cause__)
        raise SystemExit(1) from exc
    print(json.dumps(result))


if __name__ == "__main__":
    main()
