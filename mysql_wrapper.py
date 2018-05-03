#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A lightweight wrapper around MySQLdb."""
import copy
import MySQLdb.constants
import MySQLdb.converters
import MySQLdb.cursors
import itertools
import logging
import time


# TABLE_NAME = 'userinfo'
# HOST = 'localhost'
# DB_NAME = 'freeswitch'
# USER = 'root'
# PASSWORD = ''
class Conf(object):
        """docstring for Configuration"""
        # Alias some common MySQL exceptions

        T_BASEINFO = 't_baseinfo'
        l_CRM_LOGIN = 'l_crm_login'
        CFG_QUEUE = 'cfg_queue'
        IntegrityError = MySQLdb.IntegrityError
        OperationalError = MySQLdb.OperationalError

        # 表名字定义前后要留出空格，否则在sql语句中使用的时候容易出错
        B_HCODE_SHARE = 'b_hcode_share'
        R_STAFFIDEXTEN_SHARE = ' r_staffidexten_share '
        R_STAFFIDNUM_SHARE = ' r_staffidnum_share '
        K_NUMINFO_SHARE = ' k_numinfo_share '
        ASRCALL_CONFIG = ' asrcall_config '
        K_BLACKLIST_SHARE = ' k_blacklist_share '
        CRM_COMPANYINFO = ' crm_companyinfo '
        CUSTOMER_BASEINFO = ' customer_baseinfo '
        CRM_USERINFO = ' crm_userinfo '
        CRM_ROLE = ' crm_role '
        L_MISSEDCALL = ' l_missedcall'
        L_RECORD = ' l_record '
        CDR = ' cdr '
        FORECAST_DATA_TEMP = ' forecast_data_temp '
        CFG_SIP = 'cfg_sip'
        K_PROJECT_CLASSIFICATION = ' k_projectclassification '
        K_PROJECTINFO = ' k_projectinfo '
        CRM_DEPARTMENT = ' crm_department '
        FORECAST_DATA_SHARE_LOG = ' forecast_data_share_log '
        FORECAST_IVRLOGOUT = ' forecast_ivrlogout '
        FORECAST_QUEUE = ' forecast_queue '
        TEMP_NEWNUM = 'temp_newnum'
        B_ID_GENERATOR = 'b_id_generator'
        IVR_TOD = ' ivr_tod '
        IVR_MENU = ' ivr_menu '
        IVR_SOUND = ' ivr_sound '
        ASRCALL_NOANSWER = 'asrcall_noanswer'

        HOST = 'localhost'
        DB_NAME = 'u_crm_db'
        USER = 'root'
        PASSWORD = ''
        # Fix the access conversions to properly recognize unicode/binary
        FIELD_TYPE = MySQLdb.constants.FIELD_TYPE
        FLAG = MySQLdb.constants.FLAG
        CONVERSIONS = copy.copy(MySQLdb.converters.conversions)
        SOUND_PATH = '/usr/local/src/callcenter/sounds/'
        # 是否归属座席优先
        staff_first = 0
        # 本地区号
        local_areacode = '021'
        YT_CHARSET = 'utf-8'

        CONFIG_FILE = '/usr/local/freeswitch/scripts/configfile'

        def __init__(self, arg):
                super(Conf, self).__init__()
                self.arg = arg

        if __name__ == '__main__':
                pass
        else:
                field_types = [FIELD_TYPE.BLOB, FIELD_TYPE.STRING, FIELD_TYPE.VAR_STRING]
                if 'VARCHAR' in vars(FIELD_TYPE):
                        field_types.append(FIELD_TYPE.VARCHAR)

                for field_type in field_types:
                        CONVERSIONS[field_type] = [(FLAG.BINARY, str)] + CONVERSIONS[field_type]


class Connection(object):
        """A lightweight wrapper around MySQLdb DB-API connections.

        The main value we provide is wrapping rows in a dict/object so that
        columns can be accessed by name. Typical usage::

            db = database.Connection("localhost", "mydatabase")
            for article in db.query("SELECT * FROM articles"):
                print article.title

        Cursors are hidden by the implementation, but other than that, the methods
        are very similar to the DB-API.

        We explicitly set the timezone to UTC and the character encoding to
        UTF-8 on all connections to avoid time zone and encoding errors.
        """

        def __init__(self, host=Conf.HOST, database=Conf.DB_NAME, user=Conf.USER, password=Conf.PASSWORD,
                     max_idle_time=7 * 3600):
                self.host = host
                self.database = database
                self.max_idle_time = max_idle_time

                args = dict(conv=Conf.CONVERSIONS, use_unicode=True, charset="utf8",
                            db=database, init_command='SET time_zone = "+8:00"',
                            sql_mode="TRADITIONAL")
                if user is not None:
                        args["user"] = user
                if password is not None:
                        args["passwd"] = password

                # We accept a path to a MySQL socket file or a host(:port) string
                if "/" in host:
                        args["unix_socket"] = host
                else:
                        self.socket = None
                        pair = host.split(":")
                        if len(pair) == 2:
                                args["host"] = pair[0]
                                args["port"] = int(pair[1])
                        else:
                                args["host"] = host
                                args["port"] = 3306

                self._db = None
                self._db_args = args
                self._last_use_time = time.time()
                try:
                        self.reconnect()
                except Exception:
                        logging.error("Cannot connect to MySQL on %s", self.host,
                                      exc_info=True)

        def __del__(self):
                self.close()

        # lifeng add
        def insert_id(self):
                # 把linked_id加入数据库
                pass

        def close(self):
                """Closes this database connection."""
                if getattr(self, "_db", None) is not None:
                        self._db.close()
                        self._db = None

        def reconnect(self):
                """Closes the existing database connection and re-opens it."""
                self.close()
                try:
                        from DBUtils import PooledDB

                        pool_con = PooledDB.PooledDB(creator=MySQLdb, mincached=1, maxcached=10, maxshared=10,
                                                     maxconnections=20, blocking=False, maxusage=100, **self._db_args)
                        self._db = pool_con.connection()
                        self._db.cursor().connection.autocommit(True)
                except:
                        self._db = MySQLdb.connect(**self._db_args)
                        self._db.autocommit(True)

        def iter(self, query, *parameters):
                """Returns an iterator for the given query and parameters."""
                self._ensure_connected()
                cursor = MySQLdb.cursors.SSCursor(self._db)
                try:
                        self._execute(cursor, query, parameters)
                        column_names = [d[0] for d in cursor.description]
                        for row in cursor:
                                yield Row(zip(column_names, row))
                finally:
                        cursor.close()

        def query(self, query, *parameters):
                """Returns a row list for the given query and parameters."""
                cursor = self._cursor()
                try:
                        self._execute(cursor, query, parameters)
                        column_names = [d[0] for d in cursor.description]
                        return [Row(itertools.izip(column_names, row)) for row in cursor]
                finally:
                        cursor.close()

        def get(self, query, *parameters):
                """Returns the first row returned for the given query."""
                rows = self.query(query, *parameters)
                if not rows:
                        return rows
                elif len(rows) > 1:
                        raise Exception("Multiple rows returned for Database.get() query")
                else:
                        return rows[0]

        def get_one(self, query, *parameters):
                row = self.get(query, *parameters)
                if row:
                        return row[parameters]
                else:
                        return 0  #无论对于数据库的char,int,tinyint类型，都可以将其设为0

        def get_all(self, query, *parameters):
                rows = self.query(query, *parameters)
                if not rows:
                        return ()
                else:
                        return rows

        # rowcount is a more reasonable default return value than lastrowid,
        # but for historical compatibility execute() must return lastrowid.
        def execute(self, query, *parameters):
                """Executes the given query, returning the lastrowid from the query."""
                return self.execute_lastrowid(query, *parameters)

        def execute_lastrowid(self, query, *parameters):
                """Executes the given query, returning the lastrowid from the query."""
                cursor = self._cursor()

                try:
                        self._execute(cursor, query, parameters)
                        return cursor.lastrowid
                finally:
                        cursor.close()

        def execute_rowcount(self, query, *parameters):
                """Executes the given query, returning the rowcount from the query."""
                cursor = self._cursor()
                try:
                        self._execute(cursor, query, parameters)
                        return cursor.rowcount
                finally:
                        cursor.close()

        def executemany(self, query, parameters):
                """Executes the given query against all the given param sequences.

                We return the lastrowid from the query.
                """
                return self.executemany_lastrowid(query, parameters)

        def executemany_lastrowid(self, query, parameters):
                """Executes the given query against all the given param sequences.

                We return the lastrowid from the query.
                """
                cursor = self._cursor()
                try:
                        cursor.executemany(query, parameters)
                        return cursor.lastrowid
                finally:
                        cursor.close()

        def executemany_rowcount(self, query, parameters):
                """Executes the given query against all the given param sequences.

                We return the rowcount from the query.
                """
                cursor = self._cursor()
                try:
                        cursor.executemany(query, parameters)
                        return cursor.rowcount
                finally:
                        cursor.close()

        def _ensure_connected(self):
                # Mysql by default closes client connections that are idle for
                # 8 hours, but the client library does not report this fact until
                # you try to perform a query and it fails.  Protect against this
                # case by preemptively closing and reopening the connection
                # if it has been idle for too long (7 hours by default).
                if (self._db is None or
                        (time.time() - self._last_use_time > self.max_idle_time)):
                        self.reconnect()
                self._last_use_time = time.time()

        def _cursor(self):
                self._ensure_connected()
                return self._db.cursor()

        def _execute(self, cursor, query, parameters):
                try:
                        return cursor.execute(query, parameters)
                except Conf.OperationalError:
                        logging.error("Error connecting to MySQL on %s", self.host)
                        self.close()
                        raise
                finally:
                        cursor.close()


class Row(dict):
        """A dict that allows for object-like property access syntax."""

        def __getattr__(self, name):
                try:
                        return self[name]
                except KeyError:
                        raise AttributeError(name)
