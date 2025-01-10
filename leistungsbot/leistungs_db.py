# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
from __future__ import annotations

import logging
import re
from datetime import date
from datetime import datetime
from enum import Enum

import mysql.connector

from leistungsbot import leistungs_config as lc
from leistungsbot.google_place import Places
from leistungsbot.leistungs_returns import LeistungsReturnCodes


class LeistungsTagState(Enum):
    NONE = 0
    OPEN = 1
    CLOSED = 2


class LeistungsDB:
    def __init__(self):
        self.google = Places()
        self.connect()

    def connect(self):
        try:
            self.mydb = mysql.connector.connect(
                host=lc.config["mysql"]["host"],
                database=lc.config["mysql"]["db"],
                user=lc.config["mysql"]["user"],
                password=lc.config["mysql"]["password"],
                ssl_disabled=True,
                collation="utf8mb4_general_ci",
            )
            return True
        except Exception as e:
            self.mydb = mysql.connector.MySQLConnection()
            logging.error("Error while connecting to MySQL", e)
            return False

    def convert(self, mysql_res, skinny_bitch=False):
        if not mysql_res:
            return None

        elif isinstance(mysql_res, dict):
            for k in mysql_res:
                mysql_res[k] = self.convert(mysql_res[k], skinny_bitch)

        elif type(mysql_res) in [tuple, list]:
            mysql_res = [self.convert(i, skinny_bitch) for i in mysql_res]

            if skinny_bitch and len(mysql_res) == 1:
                return mysql_res[0]

        elif isinstance(mysql_res, bytearray):
            pass

        elif isinstance(mysql_res, str):
            if "POINT" in mysql_res:
                return re.findall(r"[\d\.]+", mysql_res)

        return mysql_res

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
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        try:
            sql = """INSERT INTO `members` (`user_id`, `chat_id`, `score`, `joined`)
                VALUES (%s, %s, %s, %s);"""
            values = (
                user_id,
                chat_id,
                0,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            logging.debug(sql % values)
            cursor.execute(sql, values)
        except mysql.connector.IntegrityError:
            cursor.execute(
                "UPDATE `members` SET `left` = %s, `chat_id` = %s WHERE `user_id` = %s;",
                (None, chat_id, user_id),
            )
        self.mydb.commit()

    def getUsers(self):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT * FROM `members`;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getUserKey(self, user_id):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `members` WHERE `user_id` = %s;"
        values = (user_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getUserScore(self, user_id: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `score` FROM `members` WHERE `user_id` = %s;"
        values = (user_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def setUserScore(self, user_id: int, score: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "UPDATE `members` SET `score` = 'NULL', chat_id = %s WHERE `user_id` = %s;"
        values = (score, user_id)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def increaseUserScore(self, user_id: int, value: int):
        self.setUserScore(user_id, self.getUserScore(user_id) + value)

    def removeUser(self, user_id: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "UPDATE `members` SET `left` = %s WHERE `user_id` = %s;"
        # .strftime('%Y-%m-%d %H:%M:%S')
        values = (datetime.now(), user_id)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def addLocation(self, place_id: str, name: str) -> LeistungsReturnCodes:
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        info = self.google.getPlaceInfo(place_id)
        cursor = self.mydb.cursor()
        retry = True
        orig_name = name
        cnt = 1
        res = LeistungsReturnCodes.OK
        while retry:
            try:
                sql = "INSERT INTO `locations` (`name`, `google-place-id`, `lat`, `lng`, `address`, `phone`, `url`) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                values = (
                    name,
                    place_id,
                    info.get("geometry", {})
                    .get("location", {})
                    .get("lat", None),
                    info.get("geometry", {})
                    .get(
                        "location",
                        {},
                    )
                    .get("lng", None),
                    info.get("formatted_address", None),
                    info.get("international_phone_number", None),
                    info.get("url", None),
                )
                logging.debug(sql % values)
                cursor.execute(sql, values)
                retry = False
            except mysql.connector.IntegrityError:
                location = self.getLocationInfo(name)
                if location.get("google-place-id") == place_id:
                    retry = False
                    res = LeistungsReturnCodes.DB_DUPLICATE
                else:
                    cnt += 1
                    name = orig_name + str(cnt)
        self.mydb.commit()
        return res

    def removeLocation(self, key):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "DELETE FROM `locations` WHERE `key` = %s;"
        values = (key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getAllLocations(self):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `name` FROM `locations`;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLocationKey(self, location_name):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `locations` WHERE `name` = %s;"
        values = (location_name,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getLocationName(self, location_key):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `name` FROM `locations` WHERE `key` = %s;"
        values = (location_key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getVisitedLocations(self):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `name`, `key` FROM `locations` WHERE `visited` = TRUE;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getVirgineLocations(self):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `name`, `key` FROM `locations` WHERE `visited` = FALSE ORDER BY `name` DESC;"
        values = ()
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLocationInfo(self, location_name):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT * FROM `locations` WHERE `name` = %s;"
        values = (location_name,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getLocationInfoByKey(self, key: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT * FROM `locations` WHERE `key` = %s;"
        values = (key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def setLocationVisitedState(self, location_name, visited=True):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "UPDATE `locations` SET `visited` = %s WHERE `name` = %s;"
        values = (visited, location_name)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def setLocationVisitedStateKey(self, location_key, visited=True):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "UPDATE `locations` SET `visited` = %s WHERE `key` = %s;"
        values = (visited, location_key)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def rateLocation(self, location_name, user_id, rating):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        uKey = self.getUserKey(user_id)
        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `location_rating` (`location`, `member`, `rating`) VALUES (%s, %s, %s);"
        values = (lKey, uKey, rating)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def rateLocationKey(self, location_key, user_id, rating):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        uKey = self.getUserKey(user_id)
        lKey = location_key
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `location_rating` (`location`, `member`, `rating`) VALUES (%s, %s, %s);"
        values = (lKey, uKey, rating)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getAvgLocationRating(self, location_name):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor()
        sql = "SELECT AVG(`rating`) FROM `location_rating` WHERE `location` = %s;"
        values = (lKey,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        res = self.convert(cursor.fetchall(), skinny_bitch=True)
        return res if res else 0

    def getUserLocationRating(self, location_name, user_id):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        uKey = self.getUserKey(user_id)
        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT `rating` FROM `location_rating` WHERE `location` = %s AND `member` = %s;"
        values = (lKey, uKey)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getAvgUserLocationRating(self, user_id):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        uKey = self.getUserKey(user_id)
        cursor = self.mydb.cursor()
        sql = (
            "SELECT AVG(`rating`) FROM `location_rating` WHERE `member` = %s;"
        )
        values = (uKey,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def addLeistungsTag(
        self,
        date: datetime,
        location_name: str,
        poll_id: int,
        venue_id: int,
        type: int,
    ):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        lKey = self.getLocationKey(location_name)
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `leistungstag` (`location`, `date`, `poll_id`, `venue_id`, `type`) VALUES (%s, %s, %s, %s, %s);"
        # .strftime('%Y-%m-%d')
        values = (lKey, date, poll_id, venue_id, type)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getLeistungstag(self, key: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT * FROM `leistungstag` WHERE `key` = %s;"
        values = (key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getLeistungstageByDate(self, date: date):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT * FROM `leistungstag` WHERE DATE(`date`) = %s;"
        values = (date,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLeistungsTagKeyPollId(self, poll_id: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `key` FROM `leistungstag` WHERE `poll_id` = %s;"
        values = (poll_id,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchone(), True)

    def getOpenLeistungsTag(self, type: int = None):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        if type:
            sql = "SELECT * FROM `leistungstag` WHERE `type` = %s AND `closed` = %s ORDER BY `date`;"
            values = (int(type), False)
        else:
            sql = "SELECT * FROM `leistungstag` WHERE `closed` = %s ORDER BY `date`;"
            values = (False,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getClosedLeistungsTag(self, type: int = None):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        if type:
            sql = "SELECT * FROM `leistungstag` WHERE `type` = %s AND `closed` = %s ORDER BY `date`;"
            values = (int(type), True)
        else:
            sql = "SELECT * FROM `leistungstag` WHERE `closed` = %s ORDER BY `date`;"
            values = (True,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def closeLeistungstag(self, leistungstag_key: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "UPDATE `leistungstag` SET `closed` = %s WHERE `key` = %s;"
        values = (True, leistungstag_key)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def removeLeistungstag(self, key: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "DELETE FROM `leistungstag` WHERE `key` = %s;"
        values = (key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getHistory(self, type: int = None, limit: int = 100):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = f"SELECT * FROM (SELECT * FROM `leistungstag` {'WHERE `type` = %s' if type else ''} ORDER BY `date` DESC LIMIT %s) SQ ORDER BY `date`;"
        if type:
            values = (int(type), int(limit))
        else:
            values = (int(limit),)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getHistoryCount(self, type: int = None):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

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

    def getLatest(self, type: int = None, state=LeistungsTagState.NONE):
        return self.getPrevious(type, state, 1)

    def getLeistungsTags(
        self,
        type: int = None,
        state=LeistungsTagState.NONE,
        max_results: int = 0,
        before: datetime = None,
    ):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        select = "SELECT * FROM `leistungstag`"
        where = ""
        values = ()
        order = "ORDER BY `date` DESC"

        if before:
            if len(where) > 0:
                where += " AND "
            else:
                where = "WHERE "
            where += "`date` <= %s"
            values += (before,)

        if type:
            if len(where) > 0:
                where += " AND "
            else:
                where = "WHERE "
            where += "`type` = %s"
            values += (int(type),)

        if state != LeistungsTagState.NONE:
            if len(where) > 0:
                where += " AND "
            else:
                where = "WHERE "
            where += "`closed` = %s"
            values += (state == LeistungsTagState.CLOSED,)

        limit = ""
        if max_results > 0:
            limit = "LIMIT %s"
            values += (max_results,)

        sql = f"{select} {where} {order} {limit};"
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getParticipants(self, leistungstag_key: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        sql = "SELECT `member` FROM `participants` WHERE `event` = %s;"
        values = (leistungstag_key,)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        return self.convert(cursor.fetchall())

    def getLatestParticipants(self, type=None):
        key = self.getLatest(type).get("key")
        return self.getParticipants(key)

    def addParticipant(self, user_id: int, poll_id: int):
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        user_key = self.getUserKey(user_id)
        leistungstag_key = self.getLeistungsTagKeyPollId(poll_id)
        cursor = self.mydb.cursor()
        sql = "INSERT INTO `participants` (`member`, `event`) VALUES (%s, %s);"
        values = (user_key, leistungstag_key)
        logging.debug(sql % values)
        cursor.execute(sql, values)
        self.mydb.commit()

    def getMostRecentLeistungstag(self) -> dict:
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT * FROM `leistungstag` ORDER BY `date` DESC LIMIT 1"
        cursor.execute(sql)
        return self.convert(cursor.fetchone(), True)

    def getLeistungstagByNumber(self, number: int) -> dict | None:
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor(dictionary=True)
        sql = "SELECT * FROM `leistungs_view` WHERE number = %s"
        cursor.execute(sql, (number,))
        return self.convert(cursor.fetchone(), True)

    def switchLeistungstagLocation(
        self,
        lt_id: int,
        old_location_id: int,
        new_location_id: int,
    ) -> None:
        if not self.mydb.is_connected():
            if not self.connect():
                logging.error("No connection to DataBase possible")
                raise Exception("No connection to DataBase available")

        cursor = self.mydb.cursor()
        update_lt_sql = (
            "UPDATE `leistungstag` SET `location` = '%s' WHERE `key` = '%s'"
        )
        update_old_location = "UPDATE `locations` as l SET `visited` = (SELECT count(*) FROM leistungstag WHERE location = l.`key` LIMIT 1) WHERE `key` = '%s'"
        update_new_location = (
            "UPDATE `locations` as l SET `visited` = 1 WHERE `key` = '%s'"
        )

        cursor.execute(update_lt_sql, (new_location_id, lt_id))
        cursor.execute(update_old_location, (old_location_id,))
        cursor.execute(update_new_location, (new_location_id,))
        self.mydb.commit()


if __name__ == "__main__":
    logging.basicConfig(filename="myapp.log", level=logging.DEBUG)
    db = LeistungsDB()
    db.checkConnection()
    # db.addUser(4711)
    # db.addLocation('ChIJ5UvV55IHbUcRMq6el31MzZI', 'Cafe Phönixhof')
    # db.addLeistungsTag(datetime.now(), 'Cafe Phönixhof', 42069)
    # db.addParticipant(4711, 42069)
    a = db.getOpenLeistungsTag()
    print(a)
