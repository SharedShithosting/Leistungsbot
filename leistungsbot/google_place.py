# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
from __future__ import annotations

import datetime
from enum import auto
from enum import Enum

import googlemaps

from leistungsbot import leistungs_config as lc


class Openness(Enum):
    UNKNOWN = auto()
    CLOSED = auto()
    SHORT = auto()
    OPEN = auto()


class Weekday(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THIRSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def toIsoWeekday(self):
        return self.value + 1

    def toPythonWeekday(self):
        return self.value

    def toGooglePlacesWeekday(self):
        return (self.value + 1) % 7

    @staticmethod
    def fromIsoWeekday(weekday):
        return Weekday(weekday - 1)

    @staticmethod
    def fromPythonWeekday(weekday):
        return Weekday(weekday)

    @staticmethod
    def fromGooglePlacesWeekday(weekday):
        result = weekday - 1
        return Weekday(result) if result >= 0 else Weekday(6)


class Hours:
    def __init__(self, open, close):
        self.open = open
        self.close = close


class Places:
    def __init__(self) -> None:
        self.gmaps = googlemaps.Client(
            key=lc.config["google"],
        )
        self.lat = 48.306284
        self.lng = 14.286215
        self.radius = 2000
        self.language = "de"

    def getPlaceInfo(self, place_id):
        return self.gmaps.place(
            place_id,
            fields=[
                "geometry/location",
                "formatted_address",
                "international_phone_number",
                "url",
                "name",
            ],
            language=self.language,
        ).get("result", {})

    def findPlace(self, query):
        res = self.gmaps.find_place(
            query,
            input_type="textquery",
            fields=["name", "place_id", "formatted_address"],
            location_bias=f"circle:{self.radius}@{self.lat},{self.lng}",
            language=self.language,
        )
        if res.get("status", None) == "OK":
            return res.get("candidates", [])
        return []

    def checkOpenHours(
        self,
        place_id,
        target_day: datetime.date,
        target_time=datetime.time(19, 0),
        duration=datetime.timedelta(hours=3),
    ):
        target_date = datetime.datetime.combine(target_day, target_time)

        place_detail = self.gmaps.place(place_id, fields=["opening_hours"])
        if place_detail["status"] != "OK" or len(place_detail["result"]) == 0:
            return (Openness.UNKNOWN, "")

        opening_hours = place_detail["result"]["opening_hours"]["periods"]
        # Returns something like this:
        # [
        #     {
        #         "close": {
        #             "day": 1,
        #             "time": "1500"
        #         },
        #         "open": {
        #             "day": 1,
        #             "time": "1200"
        #         }
        #     },
        #     {
        #         "close": {
        #             "day": 1,
        #             "time": "2230"
        #         },
        #         "open": {
        #             "day": 1,
        #             "time": "1700"
        #         }
        #     },
        #     {
        #         "close": {
        #             "day": 2,
        #             "time": "1500"
        #         },
        #         "open": {
        #             "day": 2,
        #             "time": "1200"
        #         }
        #     }
        # ...
        # ]

        wd = Weekday.fromPythonWeekday(
            target_day.weekday(),
        ).toGooglePlacesWeekday()

        # Get opening hour for tuesday == 2
        target_day_opening_hours = filter(
            lambda entry: entry["open"]["day"] == wd,
            opening_hours,
        )

        hours = []

        # TODO: Transform weekday and time to actual datetimes,
        #  for easier handling
        for oh in target_day_opening_hours:
            open = datetime.datetime.combine(
                target_day + datetime.timedelta(days=oh["open"]["day"] - wd),
                datetime.time(
                    int(oh["open"]["time"][0:2]),
                    int(oh["open"]["time"][2:4]),
                ),
            )
            close = datetime.datetime.combine(
                target_day + datetime.timedelta(days=oh["close"]["day"] - wd),
                datetime.time(
                    int(oh["close"]["time"][0:2]),
                    int(oh["close"]["time"][2:4]),
                ),
            )

            if open.date() < target_day:
                open += datetime.timedelta(7)

            if close.date() < target_day:
                close += datetime.timedelta(7)

            hours.append(Hours(open, close))

        weekday_text = "\n".join(
            place_detail["result"]["opening_hours"]["weekday_text"],
        )

        if len(hours) < 1:
            return (Openness.CLOSED, weekday_text)

        for h in hours:
            if h.open <= target_date and h.close > target_date:
                if h.close - target_date < duration:
                    return (Openness.SHORT, weekday_text)
                else:
                    return (Openness.OPEN, weekday_text)

        return (Openness.CLOSED, weekday_text)


if __name__ == "__main__":
    place = Places()
    while True:
        q = input("Search for location: ")
        r = place.findPlace(q)
        print(r)
        i = place.getPlaceInfo(r[0]["place_id"])
        print(i)
        print(
            place.checkOpenHours(
                r[0]["place_id"],
                datetime.date.fromisoformat("2023-05-16"),
            ),
        )
