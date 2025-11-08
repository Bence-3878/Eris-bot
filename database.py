# -*- coding: utf-8 -*-
# database.py
# adatásis kapcsolatok


if __name__ == '__main__':
    exit(1)


class Database:
    def __init__(self):

        try:
            import mysql.connector
            self.leveldb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="alma",
                database="Eris_bot",
                port=3306,
                auth_plugin='mysql_native_password'
            )
            self.cursor = self.leveldb.cursor()
        except Exception as e:
            self.leveldb = None
            print(f"Figyelem: az adatbázis-kapcsolat nem jött létre: {e}. A szint/xp funkciók nem lesznek elérhetőek.")
            # Figyelmeztető üzenet a konzolra

    def close(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.leveldb:
            self.leveldb.close()
            self.leveldb = None

    def __del__(self):
        self.close()

    def get_database(self):
        return self.leveldb

    def get_cursor(self):
        return self.cursor

    def execute(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def commit(self):
        self.leveldb.commit()

    def rollback(self):
        self.leveldb.rollback()

    def execute_many(self, query, values):
        self.reset()
        self.cursor.executemany(query, values)
        self.leveldb.commit()
        return

    def check(self):
        return self.leveldb.is_connected()

    def get_connection_status(self):
        return self.leveldb.get_server_info() if self.leveldb else None

    def get_connection_info(self):
        return self.leveldb.get_server_info() if self.leveldb else None

    def get_connection_host(self):
        return self.leveldb.get_server_info() if self.leveldb else None

    def get_connection_port(self):
        return self.leveldb.get_server_info() if self.leveldb else None

    def reset(self):
        if not self.check():
            return
        self.close()
        self.__init__()
        return


