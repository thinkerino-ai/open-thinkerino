import threading
import uuid


class Language:
    def __init__(self, *, _language_id: uuid.UUID = None, _next_id: int = None):
        self._id: uuid.UUID = _language_id or uuid.uuid4()
        self._next_id = _next_id or 0
        self.__lock = threading.Lock()

    def get_next(self) -> int:
        with self.__lock:
            if self._next_id is not None:
                res = self._next_id
                self._next_id += 1
                return res
            else:
                raise RuntimeError("This Language cannot be used to generate ids anymore")

    def __repr__(self):
        with self.__lock:
            return f"Language(language_id={repr(self._id)}, next_id={self._next_id})"

    def __str__(self):
        return f"Language({self._id})"

    def __eq__(self, other):
        if not isinstance(other, Language):
            return NotImplemented
        return other._id == self._id

    def __hash__(self):
        return hash(self._id)

    def __getstate__(self):
        return self._id

    def __setstate__(self, state):
        self._id = state
        self._next_id = None  # an unpickled language is "just for reference", it cannot generate any more ids
        self.__lock = threading.Lock()
