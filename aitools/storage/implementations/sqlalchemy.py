from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, func, MetaData, Table, select, and_
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from aitools.storage.base import NodeStorage

metadata = MetaData()
Base = declarative_base()

abstruse_to_object = Table(
    'abstruse_to_object', metadata,
    Column('abstruse_id', Integer, primary_key=True),
    Column('object_id', Integer, primary_key=True)
)


abstruse_to_subtrie = Table(
    'abstruse_to_subtrie', metadata,
    Column('abstruse_id', Integer, primary_key=True),
    Column('subtrie_id', Integer)
)


trie_to_abstruse = Table(
    'trie_to_abstruse', metadata,
    Column('trie_id', Integer, primary_key=True),
    Column('abstruse_id', Integer, unique=True, sqlite_on_conflict_unique='IGNORE')
)


trie_to_key_and_subtrie = Table(
    'trie_to_key_and_subtrie', metadata,
    Column('trie_id', Integer, primary_key=True),
    Column('key_element', String, primary_key=True),
    Column('subtrie_id', Integer)
)


object_to_data = Table(
    'object_to_data', metadata,
    Column('object_id', Integer, primary_key=True),
    Column('data', Integer, unique=True)
)


# TODO: handle the session creation in a sensible way :P like.. not here
class SQLAlchemyNodeStorage(NodeStorage):
    def __init__(self, connection: Connection):
        self.connection = connection

        metadata.create_all(self.connection.engine)

        self.last_id = self.__fetch_last_id()

    @contextmanager
    def transaction(self):
        # TODO: feeling lazy, might implement later :P
        raise NotImplementedError()

    def commit(self):
        # TODO: feeling lazy, might implement later :P
        raise NotImplementedError()

    def rollback(self):
        # TODO: feeling lazy, might implement later :P
        raise NotImplementedError()

    def close(self):
        self.connection.close()

    def __fetch_last_id(self):
        # TODO I'm sure there's a better way of doing this but SQLAlchemy eludes my feeble brain
        max_results = [
            self.connection.execute(select([
                func.max(abstruse_to_subtrie.c.abstruse_id),
            ])).scalar(),
            self.connection.execute(select([
                func.max(abstruse_to_subtrie.c.subtrie_id),
            ])).scalar(),
            self.connection.execute(select([
                func.max(object_to_data.c.object_id),
            ])).scalar(),
        ]
        return max(
            x if x is not None else 0
            for x in max_results
        )

    def next_id(self):
        self.last_id += 1
        return self.last_id

    def store_abstruse_node_for_trie_index_id(self, trie_id, abstruse_id):
        try:
            self.connection.execute(trie_to_abstruse.insert().values(trie_id=trie_id, abstruse_id=abstruse_id))
        except IntegrityError:
            pass

    def get_all_object_ids_in_trie_node(self, trie_id):
        results = self.connection.execute(trie_to_abstruse.select(trie_to_abstruse.c.trie_id == trie_id)).fetchall()
        for obj in results:
            yield obj.abstruse_id

    def get_object(self, object_id):
        obj = self.connection.execute(object_to_data.select(object_to_data.c.object_id == object_id)).fetchone()
        return obj.data

    def get_all_object_ids_in_abstruse_node(self, abstruse_id):
        results = self.connection.execute(
            abstruse_to_object.select(abstruse_to_object.c.abstruse_id == abstruse_id)
        ).fetchall()

        for obj in results:
            yield obj.object_id

    def get_subindex_id_for_abstruse_node(self, abstruse_id):
        obj = self.connection.execute(
            abstruse_to_subtrie.select(abstruse_to_subtrie.c.abstruse_id == abstruse_id)
        ).fetchone()
        if obj is None:
            subtrie_id = self.next_id()
            self.connection.execute(abstruse_to_subtrie.insert().values(abstruse_id=abstruse_id, subtrie_id=subtrie_id))
        else:
            subtrie_id = obj.subtrie_id
        return subtrie_id

    def store_object_for_abstruse_node(self, abstruse_id, object_id):
        try:
            self.connection.execute(abstruse_to_object.insert().values(abstruse_id=abstruse_id, object_id=object_id))
        except IntegrityError:
            pass

    def get_all_subindices_in_trie_node(self, trie_id):
        results = self.connection.execute(
            trie_to_key_and_subtrie.select(trie_to_key_and_subtrie.c.trie_id == trie_id)
        ).fetchall()
        for res in results:
            yield res.subtrie_id

    def get_all_key_value_pairs_in_trie_node(self, trie_id):
        results = self.connection.execute(
            trie_to_key_and_subtrie.select(trie_to_key_and_subtrie.c.trie_id == trie_id)
        ).fetchall()

        for res in results:
            key = res.key_element if res.key_element[0] in "#*" else int(res.key_element)
            yield key, res.subtrie_id

    def get_subindex_from_trie_by_key(self, trie_id, key_element):
        res = self.connection.execute(trie_to_key_and_subtrie.select(
            and_(trie_to_key_and_subtrie.c.trie_id == trie_id,
            trie_to_key_and_subtrie.c.key_element == key_element)
        )).fetchone()
        return res.subtrie_id if res is not None else None

    def store_trie_subindex_for_trie_node_and_key(self, trie_id, key_element, subindex_id):
        try:
            self.connection.execute(
                trie_to_key_and_subtrie.insert().values(
                    trie_id=trie_id, key_element=key_element, subtrie_id=subindex_id
                )
            )
        except IntegrityError:
            pass

    def store_obj(self, obj):
        try:
            object_id = self.next_id()
            self.connection.execute(object_to_data.insert().values(object_id=object_id, data=obj))
            return object_id
        except IntegrityError:
            res = self.connection.execute(object_to_data.select(object_to_data.c.data==obj)).fetchone()
            return res.object_id
