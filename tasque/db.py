import os
import re
import sqlite3
import sys
import rich
import pathlib
from . import defs


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
            values = ','.join(map(repr, item))
            self.exec(f'''INSERT INTO
                    {defs.DB_TABLE_TASQUE} ({defs.TASK_FIELDS})
                    VALUES ({values})'''.replace('\n', ' '))
        elif isinstance(item, defs.Note):
            values = ','.join(map(repr, item))
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
            return list(map(defs.Task._make,
                self[f'select * from {defs.DB_TABLE_TASQUE}']))
        elif sql == defs.DB_TABLE_NOTES:
            return list(map(defs.Note._make,
                self[f'select * from {defs.DB_TABLE_NOTES}']))
        elif sql == defs.DB_TABLE_CONFIG:
            return list(map(defs.Config._make,
                self[f'select * from {defs.DB_TABLE_CONFIG}']))
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute(sql)
        values = cursor.fetchall()  # len(values) may be 0
        cursor.close()
        conn.close()
        return values

    def __getitem__(self, sql: str) -> list:
        return self.query(sql)


    def dump(self) -> None:
        '''
        Dump database to screen. Raw version of tqLS.
        '''
        c = rich.get_console()
        c.print(self[defs.DB_TABLE_CONFIG])
        c.print(self[defs.DB_TABLE_TASQUE])
        c.print(self[defs.DB_TABLE_NOTES])
