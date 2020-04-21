import sqlite3

from aitools.storage.base import NodeStorage


class SqliteNodeStorage(NodeStorage):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.__ensure_db_present(self.connection)
        self.last_id = self.__fetch_last_id()

    @staticmethod
    def __ensure_db_present(connection: sqlite3.Connection):
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS abstruse_to_object (
            abstruse_id INTEGER NOT NULL, 
            object_id INTEGER NOT NULL, 
            PRIMARY KEY (abstruse_id, object_id)
        );
        CREATE TABLE IF NOT EXISTS abstruse_to_subtrie (
            abstruse_id INTEGER NOT NULL, 
            subtrie_id INTEGER, 
            PRIMARY KEY (abstruse_id)
        );
        CREATE TABLE IF NOT EXISTS trie_to_abstruse (
            trie_id INTEGER NOT NULL, 
            abstruse_id INTEGER, 
            PRIMARY KEY (trie_id), 
            UNIQUE (abstruse_id) ON CONFLICT IGNORE
        );
        CREATE TABLE IF NOT EXISTS trie_to_key_and_subtrie (
            trie_id INTEGER NOT NULL, 
            key_element VARCHAR NOT NULL, 
            subtrie_id INTEGER, 
            PRIMARY KEY (trie_id, key_element)
        );
        CREATE TABLE IF NOT EXISTS object_to_data (
            object_id INTEGER NOT NULL, 
            data INTEGER, 
            PRIMARY KEY (object_id), 
            UNIQUE (data)
        );
        """)

    def __fetch_last_id(self):
        max_results = [
            self.connection.execute("SELECT max(abstruse_to_subtrie.abstruse_id) FROM abstruse_to_subtrie").fetchone(),
            self.connection.execute("SELECT max(abstruse_to_subtrie.subtrie_id) FROM abstruse_to_subtrie").fetchone(),
            self.connection.execute("SELECT max(object_to_data.object_id) FROM object_to_data").fetchone(),
        ]
        return max(
            x[0] if x[0] is not None else 0
            for x in max_results
        )

    def next_id(self):
        self.last_id += 1
        return self.last_id

    def store_abstruse_node_for_trie_index_id(self, trie_id, abstruse_id):
        try:
            self.connection.execute(
                "INSERT INTO trie_to_abstruse (trie_id, abstruse_id) VALUES (?, ?)",
                (str(trie_id), str(abstruse_id))
            )
        except sqlite3.IntegrityError:
            pass

    def get_all_object_ids_in_trie_node(self, trie_id):
        results = self.connection.execute(
            "SELECT abstruse_id FROM trie_to_abstruse WHERE trie_id = ?",
            (str(trie_id),)
        ).fetchall()
        for obj in results:
            yield obj['abstruse_id']

    def get_object(self, object_id):
        obj = self.connection.execute(
            "SELECT data FROM object_to_data WHERE object_id = ?",
            (str(object_id),)
        ).fetchone()

        return obj['data']

    def get_all_object_ids_in_abstruse_node(self, abstruse_id):
        results = self.connection.execute(
            "SELECT object_id FROM abstruse_to_object WHERE abstruse_id = ?",
            (str(abstruse_id),)
        ).fetchall()

        for obj in results:
            yield obj['object_id']

    def get_subindex_id_for_abstruse_node(self, abstruse_id):
        obj = self.connection.execute(
            "SELECT * FROM abstruse_to_subtrie WHERE abstruse_id = ?",
            (str(abstruse_id),)
        ).fetchone()
        if obj is None:
            subtrie_id = self.next_id()
            self.connection.execute(
                "INSERT INTO abstruse_to_subtrie (abstruse_id, subtrie_id) values (?,?)",
                (str(abstruse_id), str(subtrie_id))
            )
        else:
            subtrie_id = obj['subtrie_id']
        return subtrie_id

    def store_object_for_abstruse_node(self, abstruse_id, object_id):
        try:
            self.connection.execute(
                "INSERT INTO abstruse_to_object (abstruse_id, object_id) VALUES (?, ?)",
                (str(abstruse_id), str(object_id))
            )
        except sqlite3.IntegrityError:
            pass

    def get_all_subindices_in_trie_node(self, trie_id):
        results = self.connection.execute(
            "SELECT * from trie_to_key_and_subtrie WHERE trie_id = ?",
            (str(trie_id),)
        ).fetchall()

        for res in results:
            yield res['subtrie_id']

    def get_all_key_value_pairs_in_trie_node(self, trie_id):
        results = self.connection.execute(
            "SELECT key_element, subtrie_id FROM trie_to_key_and_subtrie WHERE trie_id = ?",
            (str(trie_id),)
        ).fetchall()

        for res in results:
            key_element = res['key_element']
            key = key_element if key_element[0] in "#*" else int(key_element)
            yield key, res['subtrie_id']

    def get_subindex_from_trie_by_key(self, trie_id, key_element):
        res = self.connection.execute(
            "SELECT subtrie_id FROM trie_to_key_and_subtrie WHERE trie_id = ? AND key_element = ?",
            (str(trie_id), str(key_element))
        ).fetchone()
        return res['subtrie_id'] if res is not None else None

    def store_trie_subindex_for_trie_node_and_key(self, trie_id, key_element, subindex_id):
        try:
            self.connection.execute(
                "INSERT INTO trie_to_key_and_subtrie (trie_id, key_element, subtrie_id) values (?, ?, ?)",
                (str(trie_id), str(key_element), str(subindex_id))
            )
        except sqlite3.IntegrityError:
            pass

    def store_obj(self, obj):
        try:
            object_id = self.next_id()
            self.connection.execute(
                "INSERT INTO object_to_data (object_id, data) VALUES (?, ?)",
                (str(object_id), obj)
            )
            return object_id
        except sqlite3.IntegrityError:
            res = self.connection.execute(
                "SELECT object_id FROM object_to_data WHERE data = ?",
                (obj,)
            ).fetchone()
            return res['object_id']
