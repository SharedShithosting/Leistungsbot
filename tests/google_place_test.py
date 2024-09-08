from __future__ import annotations

from leistungsbot import google_place as gp


def test_find_place():
    p = gp.Places()
    result = p.findPlace("Glockenspiel")
    assert p.lat == 48.306284
    assert p.lng == 14.286215
    assert p.radius == 2000
    data = result[0]
    assert data["place_id"] == "ChIJ064h-oOXc0cRpjC5YuYBKvc"
    assert data["name"] == "Kaffee Glockenspiel"


if __name__ == "__main__":
    test_find_place()
