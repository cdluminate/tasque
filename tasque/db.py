'''
Copyright (C) 2016-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''

import os
import re
import sqlite3
import sys
import rich
import pathlib
from . import defs
from . import resources
from . import utils


class tqDB:
    def __init__(self, dbpath: str):
        self.dbpath = dbpath
        self.create()

    def create(self) -> None:
        '''
        Create a sqlite3 database for Tq Daemon use.
        '''
        if os.path.exists(self.dbpath):
            return None
        path = pathlib.Path(self.dbpath).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.dbpath)
        sql = f'CREATE TABLE {defs.DB_TABLE_CONFIG} ({defs.CONFIG_FIELDS})'
        conn.execute(sql)
        sql = f'CREATE TABLE {defs.DB_TABLE_TASQUE} ({defs.TASK_FIELDS})'
        conn.execute(sql)
        sql = f'CREATE TABLE {defs.DB_TABLE_NOTES} ({defs.NOTE_FIELDS})'
        conn.execute(sql)
        conn.commit()
        conn.close()
        # insert configurations
        self.exec(f'INSERT INTO {defs.DB_TABLE_CONFIG} ({defs.CONFIG_FIELDS})'
                + f' VALUES ("resource", "{resources.RESOURCE_DEFAULT}")')

    def exec(self, sql: str) -> None:
        '''
        Execute a SQL statement on a given DB file.
        '''
        conn = sqlite3.connect(self.dbpath)
        conn.execute(sql)
        conn.commit()
        conn.close()

    def __call__(self, sql: str) -> None:
        self.exec(sql)

    def __iadd__(self, item: object) -> object:
        if isinstance(item, str):
            self.exec(item)
        elif isinstance(item, defs.Task):
            values = ','.join(map(repr, utils.none2null(item)))
            self.exec(f'''INSERT INTO
                    {defs.DB_TABLE_TASQUE} ({defs.TASK_FIELDS})
                    VALUES ({values})'''.replace('\n', ' '))
        elif isinstance(item, defs.Note):
            values = ','.join(map(repr, utils.null2none(item)))
            self.exec(f'''INSERT INTO
                    {defs.DB_TABLE_NOTES} ({defs.NOTE_FIELDS})
                    VALUES ({values})'''.replace('\n', ' '))
        else:
            raise TypeError('unknown type')
        return self

    def query(self, sql: str) -> list:
        '''
        Query from DB
        '''
        if not isinstance(sql, str):
            raise TypeError('expected SQL string here')
        if sql == defs.DB_TABLE_TASQUE:
            return list(map(lambda T: defs.Task._make(utils.null2none(T)),
                self[f'select * from {defs.DB_TABLE_TASQUE}']))
        elif sql == defs.DB_TABLE_NOTES:
            return list(map(lambda T: defs.Note._make(utils.null2none(T)),
                self[f'select * from {defs.DB_TABLE_NOTES}']))
        elif sql == defs.DB_TABLE_CONFIG:
            return list(map(lambda T: defs.Config._make(utils.null2none(T)),
                self[f'select * from {defs.DB_TABLE_CONFIG}']))
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute(sql)
        values = cursor.fetchall()  # len(values) may be 0
        cursor.close()
        conn.close()
        values = list(map(utils.null2none, values))
        return values

    def __getitem__(self, sql: str) -> list:
        return self.query(sql)


    def dump(self) -> None:
        '''
        Dump database to screen. Raw version of tqLS.
        '''
        c = rich.get_console()
        c.log('dumping configurations')
        c.print(self[defs.DB_TABLE_CONFIG])
        c.log('dumping tasks')
        c.print(self[defs.DB_TABLE_TASQUE])
        c.log('dumping notes')
        c.print(self[defs.DB_TABLE_NOTES])
