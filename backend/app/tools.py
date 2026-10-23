"""Read-only hotel tools with invocation-local snapshots and evidence budgets."""

import json
from urllib.parse import urlencode


class HotelTools:
    def __init__(self, hotel):
        active = hotel.catalogue().get("active")
        self.sections = (
            {key: hotel.read(key, **active) for key in ("rooms", "amenities", "policies")}
            if active
            else {}
        )
        self.calls = 0
        self.characters = 0
        self.sources = {}

    def admit(self):
        self.calls += 1
        return self.calls <= 8

    def list_information(self) -> dict:
        """List hotel record IDs. Read a record before using its facts."""
        if not self.admit():
            return {"status": "limit_reached"}
        if not self.sections:
            return {"status": "unavailable"}
        return {
            "status": "ok",
            "sections": {
                key: [
                    {"id": row["id"], "title": row.get("title", row.get("name"))}
                    for row in result["data"]
                ]
                for key, result in self.sections.items()
            },
        }

    def read_information(self, section: str, item_id: str) -> dict:
        """Read one complete hotel record using IDs from list_information.

        Args:
            section: rooms, amenities or policies. Inventory is not exposed.
            item_id: Exact record ID from the catalogue.
        """
        if not self.admit():
            return {"status": "limit_reached"}
        if not self.sections:
            return {"status": "unavailable"}
        if not isinstance(section, str) or section not in self.sections:
            return {"status": "invalid_input"}
        result = self.sections[section]
        rows = [row for row in result["data"] if row["id"] == item_id]
        if not rows:
            return {"status": "not_found"}
        row = rows[0]
        size = len(json.dumps(row, ensure_ascii=False))
        if self.characters + size > 24000:
            return {"status": "limit_reached"}
        self.characters += size
        source = result["source"]
        self.sources[(section, item_id)] = {
            **source,
            "title": row.get("title", row.get("name")),
            "url": f"/api/hotel/{section}/{item_id}?"
            + urlencode({"source_id": source["source_id"], "version": source["version"]}),
        }
        return json.loads(
            json.dumps(
                {
                    "status": "unknown" if row.get("status") == "unknown" else "ok",
                    "source": source,
                    "record": row,
                }
            )
        )
