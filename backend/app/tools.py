"""Read-only hotel tools with invocation-local snapshots and evidence budgets."""

import json
import re
from urllib.parse import urlencode


class HotelTools:
    def __init__(self, hotel, availability=None):
        self.availability = availability
        active = hotel.catalogue().get("active")
        self.sections = (
            {key: hotel.read(key, **active) for key in ("rooms", "amenities", "policies")}
            if active
            else {}
        )
        self.calls = 0
        self.characters = 0
        self.sources = {}

    def prepare_context(self, question: str, previous_question: str = "") -> list[dict]:
        """Read likely records locally; unmatched questions retain the normal tools.

        This small English demo lookup selects records, never generates an answer.
        Every selected record still passes the normal evidence and call budgets.
        """
        aliases = {
            "cost": "price",
            "costs": "price",
            "prices": "price",
            "fees": "fee",
            "kids": "child",
            "children": "child",
            "pets": "pet",
            "checkin": "arrival",
            "checkout": "departure",
        }
        stop = {
            "the",
            "and",
            "for",
            "can",
            "could",
            "would",
            "does",
            "what",
            "when",
            "how",
            "are",
            "about",
            "with",
            "this",
            "that",
            "hotel",
            "demo",
            "room",
            "rooms",
            "per",
            "night",
            "please",
            "tell",
            "have",
            "has",
            "you",
            "your",
        }

        def words(text):
            text = re.sub(r"check[ -]+in", "checkin", text.casefold())
            text = re.sub(r"check[ -]+out", "checkout", text)
            text = text.replace("how much", "price")
            return {
                aliases.get(word, word)
                for word in re.findall(r"[a-z]{3,}", text)
                if word not in stop
            }

        query = words(question)
        if len(query) < 2:
            query |= words(previous_question)
        ranked = []
        for section, result in self.sections.items():
            for row in result["data"]:
                title = row.get("title", row.get("name", ""))
                names = words(row["id"] + " " + title)
                body = words(row.get("body", row.get("description", "")))
                score = 3 * len(query & names) + len(query & body)
                if score:
                    ranked.append((score, section, row["id"]))
        ranked.sort(key=lambda item: -item[0])
        threshold = ranked[0][0] / 2 if ranked else 0
        return [
            self.read_information(section, item_id)
            for score, section, item_id in ranked[:4]
            if score >= threshold
        ]

    def admit(self):
        self.calls += 1
        return self.calls <= 8

    def list_information(self) -> dict:
        """List hotel record IDs. Read a record before using its facts."""
        if not self.admit():
            return {"status": "limit_reached"}
        if not self.sections:
            return {"status": "unavailable"}
        result = {
            "status": "ok",
            "sections": {
                key: [
                    {"id": row["id"], "title": row.get("title", row.get("name"))}
                    for row in result["data"]
                ]
                for key, result in self.sections.items()
            },
        }
        if len(json.dumps(result, ensure_ascii=False)) > 6000:
            return {"status": "limit_reached"}
        return result

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

    async def search_availability(self, check_in: str, check_out: str, guests: int) -> dict:
        """Search every night for one room fitting all guests. No room is held.

        Args:
            check_in: Exact arrival date, YYYY-MM-DD, in the property timezone.
            check_out: Exact checkout date, YYYY-MM-DD; this night is excluded.
            guests: Total people, including children and infants.
        """
        if not self.admit():
            return {"status": "limit_reached"}
        if self.availability is None:
            return {"status": "unavailable"}
        result = await self.availability.search(check_in, check_out, guests)
        size = len(json.dumps(result, ensure_ascii=False))
        if self.characters + size > 24000:
            return {"status": "limit_reached"}
        self.characters += size
        return result
