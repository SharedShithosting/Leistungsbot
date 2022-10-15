import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import logging
from google_place import Places
import yaml
import re


class LeistungsDB(object):
    def __init__(self):
        self.google = Places()
        self.config = yaml.safe_load(open("BotConfig.yml"))
        self.mydb = None
        self.connect()

    def convert(self, mysql_res, skinny_bitch=False):
        if not mysql_res:
            return None

        elif type(mysql_res) == dict:
            for k in mysql_res:
                mysql_res[k] = self.convert(mysql_res[k])

        elif type(mysql_res) in [tuple, list]:
            mysql_res = [self.convert(i) for i in mysql_res]

            if skinny_bitch and len(mysql_res) == 1:
                return mysql_res[0]

        elif type(mysql_res) == bytearray:
            pass

        elif type(mysql_res) == str:
            if 'POINT' in mysql_res:
                return re.findall("[\d\.]+", mysql_res)

        return mysql_res

    def connect(self):
        try:
            self.mydb = mysql.connector.connect(
                host=self.config['mysql']['host'],
                database=self.config['mysql']['db'],
                user=self.config['mysql']['user'],
                password=self.config['mysql']['password'],
                ssl_disabled=True
            )
        except Exception as e:
            print("Error while connecting to MySQL", e)

    def checkConnection(self):
        if self.mydb.is_connected():
            db_Info = self.mydb.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            cursor = self.mydb.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("You're connected to database: ", record)
        return self.mydb.is_connected()

    def addUser(self, user_id: int, chat_id: int = None):
        cursor = self.mydb.cursor()
        try:
            sql = """INSERT INTO `members` (`user_id`, `chat_id`, `score`, `joined`)
                VALUES (%s, %s, %s, %s);"""
            values = (user_id, chat_id, 0,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            logging.debug(sql % values)
            cursor.execute(sql, values)
        except mysql.connector.IntegrityError as err:
            cursor.execute(
                "UPDATE `members` SET `left` = %s, `chat_id` = %s WHERE `user_id` = %s;",
                (None, chat_id, user_id))
        self.mydb.commit()

    def getUsers(self):
        cursor = self.mydb.cursor()
        sql = "SELECT * FROM `members`;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getUserKey(self, user_id):
        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `members` WHERE `user_id` = %s;"
        values = (user_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getUserScore(self, user_id: int):
        cursor = self.mydb.cursor()
        sql = "SELECT `score` FROM `members` WHERE `user_id` = %s;"
        values = (user_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def setUserScore(self, user_id: int, score: int):
        cursor = self.mydb.cursor()
        sql = "UPDATE `members` SET `score` = 'NULL', chat_id = %s WHERE `user_id` = %s;"
        values = (score, user_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def increaseUserScore(self, user_id: int, value: int):
        self.setUserScore(user_id, self.getUserScore(user_id) + value)

    def removeUser(self, user_id: int):
        cursor = self.mydb.cursor()
        sql = "UPDATE `members` SET `left` = %s WHERE `user_id` = %s;"
        # .strftime('%Y-%m-%d %H:%M:%S')
        values = (datetime.now(), user_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def addLocation(self, place_id: str, name: str):
        info = self.google.getPlaceInfo(place_id)
        cursor = self.mydb.cursor()
        retry = True
        orig_name = name
        cnt = 1
        while (retry):
            try:
                sql = "INSERT INTO `locations` (`name`, `google-place-id`, `location`, `address`, `phone`, `url`) VALUES (%s, %s, PointFromText('POINT(%s %s)'), %s, %s, %s);"
                values = (name, place_id, info['geometry']['location']['lat'], info['geometry']
                          ['location']['lng'], info['formatted_address'], info['international_phone_number'], info['url'])
                logging.debug(sql % values)
                cursor.execute(sql, values)
                retry = False
            except mysql.connector.IntegrityError as err:
                cnt += 1
                name = orig_name + cnt
        self.mydb.commit()

    def getAllLocations(self):
        cursor = self.mydb.cursor()
        sql = "SELECT `name` FROM `locations`;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLocationKey(self, location_name):
        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `locations` WHERE `name` = %s;"
        values = (location_name,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getLocationName(self, location_key):
        cursor = self.mydb.cursor()
        sql = "SELECT `name` FROM `locations` WHERE `key` = %s;"
        values = (location_key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getVisitedLocations(self):
        cursor = self.mydb.cursor()
        sql = "SELECT `name`, `key` FROM `locations` WHERE `visited` = TRUE;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getVirgineLocations(self):
        cursor = self.mydb.cursor()
        sql = "SELECT `name`, `key` FROM `locations` WHERE `visited` = FALSE;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLocationInfo(self, location_name):
        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT `name`, `google-place-id`, ST_asText(`location`) AS `location`, `address`, `phone`, `url`, `visited` FROM `locations` WHERE `name` = %s;"
        values = (location_name,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def setLocationVisited(self, location_name):
        cursor = self.mydb.cursor()
        sql = "UPDATE `locations` SET `visited` = TRUE WHERE `name` = %s;"
        values = (location_name,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def rateLocation(self, location_name, user_id, rating):
        uKey = self.getUserKey(user_id)
        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `location_rating` (`location`, `member`, `rating`) VALUES (%s, %s, %s);"
        values = (lKey, uKey, rating,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getAvgLocationRating(self, location_name):
        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor()
        sql = "SELECT AVG(`rating`) FROM `location_rating` WHERE `location` = %s;"
        values = (lKey,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getUserLocationRating(self, location_name, user_id):
        uKey = self.getUserKey(user_id)
        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT `rating` FROM `location_rating` WHERE `location` = %s AND `member` = %s;"
        values = (lKey, uKey,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getAvgUserLocationRating(self, user_id):
        uKey = self.getUserKey(user_id)
        cursor = self.mydb.cursor()
        sql = "SELECT AVG(`rating`) FROM `location_rating` WHERE `member` = %s;"
        values = (uKey,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def addLeistungsTag(self, date: datetime, location_name: str, poll_id: int, venue_id: int, type: int):
        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `leistungstag` (`location`, `date`, `poll_id`, `venue_id`, `type`) VALUES (%s, %s, %s, %s, %s);"
        # .strftime('%Y-%m-%d')
        values = (lKey, date, poll_id, venue_id, type,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getLeistungsTagKeyDate(self, date: datetime):
        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `leistungstag` WHERE `date` = %s;"
        # .strftime('%Y-%m-%d')
        values = (date,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getLeistungsTagKeyPollId(self, poll_id: int):
        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `leistungstag` WHERE `poll_id` = %s;"
        values = (poll_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getOpenLeistungsTag(self, type: int = None):
        cursor = self.mydb.cursor(dictionary=True)
        if type:
            sql = "SELECT * FROM `leistungstag` WHERE `type` = %s AND `closed` = %s ORDER BY `date`;"
            values = (int(type), False,)
        else:
            sql = "SELECT * FROM `leistungstag` WHERE `closed` = %s ORDER BY `date`;"
            values = (False,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getClosedLeistungsTag(self, type: int = None):
        cursor = self.mydb.cursor(dictionary=True)
        if type:
            sql = "SELECT * FROM `leistungstag` WHERE `type` = %s AND `closed` = %s ORDER BY `date`;"
            values = (int(type), True,)
        else:
            sql = "SELECT * FROM `leistungstag` WHERE `closed` = %s ORDER BY `date`;"
            values = (True,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def closeLeistungstag(self, leistungstag_key: int):
        cursor = self.mydb.cursor()
        sql = "UPDATE `leistungstag` SET `closed` = %s WHERE `key` = %s;"
        values = (True, leistungstag_key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getHistory(self, type: int = None):
        cursor = self.mydb.cursor(dictionary=True)
        if type:
            sql = "SELECT * FROM `leistungstag` WHERE `type` = %s ORDER BY `date`;"
            values = (int(type),)
        else:
            sql = "SELECT * FROM `leistungstag` ORDER BY `date`;"
            values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getHistoryCount(self, type: int = None):
        cursor = self.mydb.cursor()
        if type:
            sql = "SELECT COUNT(*) FROM `leistungstag` WHERE `type` = %s;"
            values = (int(type),)
        else:
            sql = "SELECT COUNT(*) FROM `leistungstag`;"
            values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getLatest(self, type: int = None):
        cursor = self.mydb.cursor(dictionary=True)
        if type:
            sql = "SELECT * FROM `leistungstag` WHERE `type` = %s ORDER BY `date` DESC LIMIT 1;"
            values = (int(type),)
        else:
            sql = "SELECT * FROM `leistungstag` ORDER BY `date` DESC LIMIT 1;"
            values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getParticipants(self, leistungstag_key: int):
        cursor = self.mydb.cursor()
        sql = "SELECT `member` FROM `participants` WHERE `event` = %s;"
        values = (leistungstag_key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLatestParticipants(self, type=None):
        key = self.getLatest(type).get('key')
        return self.getParticipants(key)

    def addParticipant(self, user_id: int, poll_id: int):
        user_key = self.getUserKey(user_id)
        leistungstag_key = self.getLeistungsTagKeyPollId(poll_id)
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `participants` (`member`, `event`) VALUES (%s, %s);"
        values = (user_key, leistungstag_key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()


if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.DEBUG)
    db = LeistungsDB()
    db.checkConnection()
    # db.addUser(4711)
    #db.addLocation('ChIJ5UvV55IHbUcRMq6el31MzZI', 'Cafe Phönixhof')
    #db.addLeistungsTag(datetime.now(), 'Cafe Phönixhof', 42069)
    db.addParticipant(4711, 42069)
