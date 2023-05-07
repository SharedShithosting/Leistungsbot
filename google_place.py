import googlemaps
import yaml
import os


class Places:
    def __init__(self) -> None:
        self.config = yaml.safe_load(
            open(os.environ.get("LEISTUNGSBOT_CONFIG_FILE", "BotConfig.yml")))
        self.gmaps = googlemaps.Client(
            key=self.config['google'])
        self.lat = 48.306284
        self.lng = 14.286215
        self.radius = 2000
        self.language = 'de'

    def getPlaceInfo(self, place_id):
        return self.gmaps.place(
            place_id,
            fields=['geometry/location', 'formatted_address',
                    'international_phone_number', 'url', 'name'],
            language=self.language,
        ).get('result', {})

    def findPlace(self, query):
        res = self.gmaps.find_place(
            query,
            input_type='textquery',
            fields=['name', 'place_id'],
            location_bias=f'circle:{self.radius}@{self.lat},{self.lng}',
            language=self.language)
        if res.get('status', None) == 'OK':
            return res.get('candidates', [])
        return []

    def checkOpenHours(self, place_id):
        place_detail = self.gmaps.place(place_id, fields=['opening_hours'])
        opening_hours = place_detail['result']['opening_hours']['periods']     # Returns something like this: [{'close': {'day': 1, 'time': '1500'}, 'open': {'day': 1, 'time': '1200'}}, {'close': {'day': 1, 'time': '2230'}, 'open': {'day': 1, 'time': '1700'}}, {'close': {'day': 2, 'time': '1500'}, 'open': {'day': 2, 'time': '1200'}}, {'close': {'day': 2, 'time': '2230'}, 'open': {'day': 2, 'time': '1800'}}, {'close': {'day': 3, 'time': '1500'}, 'open': {'day': 3, 'time': '1200'}}, {'close': {'day': 3, 'time': '2230'}, 'open': {'day': 3, 'time': '1700'}}, {'close': {'day': 4, 'time': '1500'}, 'open': {'day': 4, 'time': '1200'}}, {'close': {'day': 4, 'time': '2230'}, 'open': {'day': 4, 'time': '1700'}}, {'close': {'day': 5, 'time': '1500'}, 'open': {'day': 5, 'time': '1200'}}, {'close': {'day': 5, 'time': '2230'}, 'open': {'day': 5, 'time': '1700'}}, {'close': {'day': 6, 'time': '2230'}, 'open': {'day': 6, 'time': '1600'}}]

        # Get opening hour for tuesday == 2
        tuesday_opening_hours = filter(lambda entry: entry['open']['day'] == 2, opening_hours)

        if (len(tuesday_opening_hours) < 1):
            return False

        # ...



if __name__ == '__main__':
    place = Places()
    while True:
        q = input('Search for location: ')
        r = place.findPlace(q)
        print(r)
        i = place.getPlaceInfo(r[0]['place_id'])
        print(i)
