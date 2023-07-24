import MySQLdb
import logging
import datetime

#class DBHelper():
#    @staticmethod
#    def convertDatetime(datetime_str):
#        return datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

class DBException(Exception):
    pass

class DBConnection():
    def __init__(self, db, config):
        self.db = db
        self.config = config

    def __enter__(self):
        self.connection = MySQLdb.connect(host=self.config.db_host,user=self.config.db_username,passwd=self.config.db_password,db=self.config.db_name)
        self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)
        return self

    def __exit__(self ,type, value, traceback):
        self.cursor.close()
        self.connection.close()

    def hasEntry(self, timestamp):
        try:
            self.cursor.execute(u"SELECT * FROM {} WHERE `datetime`=from_unixtime({})".format(self.config.db_table,timestamp))
            self.db.state = 1
            return self.cursor.rowcount != 0
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

    def update(self, timestamp, fields):
        try:
            self.cursor.execute(u"UPDATE {} SET {} WHERE `datetime`=from_unixtime({})".format(self.config.db_table,",".join(fields),timestamp))
            self.connection.commit()
            self.db.state = 1
            return self.cursor.rowcount != 0
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

    def insertOrUpdate(self, timestamp, fields):
        try:
            insert_values = [ u"`datetime`=from_unixtime({})".format(timestamp) ]
            insert_values.extend(fields)
            self.cursor.execute(u"INSERT INTO {} SET {} ON DUPLICATE KEY UPDATE {}".format(self.config.db_table,",".join(insert_values),",".join(fields)))
            self.connection.commit()
            self.db.state = 1
            return self.cursor.rowcount != 0
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

    def getFullDay(self):
        try:
            self.cursor.execute("SELECT * FROM {} WHERE `datetime` >= NOW() AND `datetime` <= DATE_ADD(NOW(), INTERVAL 24 HOUR) ORDER BY `datetime` ASC".format(self.config.db_table))
            self.db.state = 1
            return self.cursor.fetchall()
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

    def getOffset(self, offset):
        try:
            self.cursor.execute("SELECT * FROM {} WHERE `datetime` > DATE_ADD(NOW(), INTERVAL {} HOUR) ORDER BY `datetime` ASC LIMIT 1".format(self.config.db_table,offset-1))
            self.db.state = 1
            return self.cursor.fetchone()
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

    def getRangeList(self, start, end):
        try:
            self.cursor.execute("SELECT * FROM {} WHERE `datetime` >= '{}' AND `datetime` <= '{}' ORDER BY `datetime`".format(self.config.db_table, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')))
            self.db.state = 1
            return self.cursor.fetchall()
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

    def getWeekList(self, start):
        try:
            self.cursor.execute("SELECT * FROM {} WHERE `datetime` >= '{}' AND `datetime` < DATE_ADD(CURDATE(), INTERVAL 8 DAY) ORDER BY `datetime`".format(self.config.db_table, start.strftime('%Y-%m-%d %H:%M:%S')))
            self.db.state = 1
            return self.cursor.fetchall()
        except MySQLdb._exceptions.OperationalError as e:
            logging.warn("{}: {}".format(str(e.__class__),str(e)))
            self.db.state = 0
            raise(DBException(e))

class DB():
    def __init__(self, config):
        self.config = config
        self.state = -1

    def open(self):
        return DBConnection(self, self.config)

    def getStateMetrics(self):
        return ["weather_service_state{{type=\"mysql\"}} {}".format(self.state)]

#    def connect(self):
#        return MySQLdb.connect(host=self.config.db_host,user=self.config.db_username,passwd=self.config.db_password,db=self.config.db_name)

#    def getFullDaySQL(self):
#        return "SELECT * FROM {} WHERE `datetime` >= NOW() AND `datetime` <= DATE_ADD(NOW(), INTERVAL 24 HOUR) ORDER BY `datetime` ASC".format(self.config.db_table)

#    def getOffsetSQL(self, offset):
#        return "SELECT * FROM {} WHERE `datetime` > DATE_ADD(NOW(), INTERVAL {} HOUR) ORDER BY `datetime` ASC LIMIT 1".format(self.config.db_table,offset-1)


#    def getInsertUpdateSQL(self, timestamp,fields):
#        insert_values = [ u"`datetime`=from_unixtime({})".format(timestamp) ]
#        insert_values.extend(fields)
#        return u"INSERT INTO {} SET {} ON DUPLICATE KEY UPDATE {}".format(self.config.db_table,",".join(insert_values),",".join(fields))

#    def getEntrySQL(self, timestamp):
#        return u"SELECT * FROM {} WHERE `datetime`=from_unixtime({})".format(self.config.db_table,timestamp)

#    def getUpdateSQL(self, timestamp,fields):
#        return u"UPDATE {} SET {} WHERE `datetime`=from_unixtime({})".format(self.config.db_table,",".join(fields),timestamp)



