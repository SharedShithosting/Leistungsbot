import mysql.connector
from mysql.connector import errorcode


class LeistungsDB(object):
    def __init__(self, host, database, user, password):
        try:
            self.mydb = mysql.connector.connect(
                host=host,
                database=database,
                user=user,
                password=password
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

    def addUser(self, username):
        cursor = self.mydb.cursor()
        cursor.execute(
            "INSERT INTO `user` (`username`, `id`) VALUES ('%s', NULL);" % (username))


if __name__ == "__main__":
    db = LeistungsDB("mysqlsvr82.world4you.com",
                     "8843356db4", "sql4311137", "i@fg952y")
    db.checkConnection()
    db.addUser("IagendwosEini")
