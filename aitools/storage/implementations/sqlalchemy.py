from sqlalchemy import Column, Integer, String, BLOB, func
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from aitools.storage.base import NodeStorage


Base = declarative_base()


class AbstruseToObject(Base):
    __tablename__ = "abstruse_to_object"
    abstruse_id = Column(Integer, primary_key=True)
    object_id = Column(Integer, primary_key=True)


class AbstruseToSubtrie(Base):
    __tablename__ = "abstruse_to_subtrie"
    abstruse_id = Column(Integer, primary_key=True)
    subtrie_id = Column(Integer)


class TrieToAbstruse(Base):
    __tablename__ = "trie_to_abstruse"
    trie_id = Column(Integer, primary_key=True)
    abstruse_id = Column(Integer, unique=True)


class TrieToKeyAndSubtrie(Base):
    __tablename__ = "trie_to_key_and_subtrie"
    trie_id = Column(Integer, primary_key=True)
    key_element = Column(String, primary_key=True)
    subtrie_id = Column(Integer)


class ObjectToData(Base):
    __tablename__ = "object_to_data"
    object_id = Column(Integer, primary_key=True)
    data = Column(BLOB, unique=True)


# TODO: handle the session creation in a sensible way :P like.. not here
class SQLAlchemyNodeStorage(NodeStorage):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.Session: sessionmaker = sessionmaker(bind=engine)
        Base.metadata.create_all(self.engine)

        self.last_id = self.__fetch_last_id()

    def __fetch_last_id(self):
        session: Session = self.Session()
        max_results = session.query(
                func.max(AbstruseToSubtrie.abstruse_id),
                func.max(AbstruseToSubtrie.subtrie_id),
                func.max(ObjectToData.object_id)
            ).one()
        session.commit()
        return max(
            x if x is not None else 0
            for x in max_results
        )

    def next_id(self):
        self.last_id += 1
        return self.last_id

    def store_abstruse_node_for_trie_index_id(self, trie_id, abstruse_id):
        try:
            session: Session = self.Session()
            session.add(TrieToAbstruse(trie_id=trie_id, abstruse_id=abstruse_id))
            session.commit()
        except IntegrityError:
            pass

    def get_all_object_ids_in_trie_node(self, trie_id):
        session: Session = self.Session()
        results = session.query(TrieToAbstruse).filter(TrieToAbstruse.trie_id == trie_id).all()
        session.commit()
        for obj in results:
            yield obj.abstruse_id

    def get_object(self, object_id):
        session: Session = self.Session()
        obj = session.query(ObjectToData).filter(ObjectToData.object_id == object_id).one()
        session.commit()
        return obj.data

    def get_all_object_ids_in_abstruse_node(self, abstruse_id):
        session: Session = self.Session()
        results = session.query(AbstruseToObject).filter(AbstruseToObject.abstruse_id == abstruse_id).all()
        session.commit()
        for obj in results:
            yield obj.object_id

    def get_subindex_id_for_abstruse_node(self, abstruse_id):
        session: Session = self.Session()
        obj = session.query(AbstruseToSubtrie).filter(AbstruseToSubtrie.abstruse_id == abstruse_id).one_or_none()
        if obj is None:
            subtrie_id = self.next_id()
            session.add(AbstruseToSubtrie(abstruse_id=abstruse_id, subtrie_id=subtrie_id))
        else:
            subtrie_id = obj.subtrie_id
        session.commit()
        return subtrie_id

    def store_object_for_abstruse_node(self, abstruse_id, object_id):
        try:
            session: Session = self.Session()
            session.add(AbstruseToObject(abstruse_id=abstruse_id, object_id=object_id))
            session.commit()
        except IntegrityError:
            pass

    def get_all_subindices_in_trie_node(self, trie_id):
        session: Session = self.Session()
        results = session.query(TrieToKeyAndSubtrie).filter(TrieToKeyAndSubtrie.trie_id == trie_id).all()
        session.commit()
        for res in results:
            yield res.subtrie_id

    def get_all_key_value_pairs_in_trie_node(self, trie_id):
        session: Session = self.Session()
        results = session.query(TrieToKeyAndSubtrie).filter(TrieToKeyAndSubtrie.trie_id == trie_id).all()
        session.commit()
        for res in results:
            yield res.key_element, res.subtrie_id

    def get_subindex_from_trie_by_key(self, trie_id, key_element):
        session: Session = self.Session()
        res = session.query(TrieToKeyAndSubtrie).filter(TrieToKeyAndSubtrie.trie_id == trie_id,
                                                        TrieToKeyAndSubtrie.key_element == key_element).one_or_none()
        session.commit()
        return res.subtrie_id if res is not None else None

    def store_trie_subindex_for_trie_node_and_key(self, trie_id, key_element, subindex_id):
        try:
            session: Session = self.Session()
            session.add(TrieToKeyAndSubtrie(trie_id=trie_id, key_element=key_element, subtrie_id=subindex_id))
            session.commit()
        except IntegrityError:
            pass

    def store_obj(self, obj):
        try:
            session: Session = self.Session()
            object_id = self.next_id()
            session.add(ObjectToData(object_id=object_id, data=obj))
            session.commit()
            return object_id
        except IntegrityError:
            session: Session = self.Session()
            res = session.query(ObjectToData).filter(ObjectToData.data==obj).one()
            return res.object_id
