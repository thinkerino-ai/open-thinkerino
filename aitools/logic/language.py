import uuid


class Language:
    def __init__(self, *, language_id: uuid.UUID = None, next_id: int = None):
        if (language_id is None) ^ (next_id is None):
            raise ValueError("language_id and next_id must be both None or both not None")
        self._id: uuid.UUID = language_id or uuid.uuid4()
        self._next_id = next_id or 0

    def get_next(self) -> int:
        # TODO can I haz thread safety?
        if self._next_id is not None:
            res = self._next_id
            self._next_id += 1
            return res
        else:
            raise RuntimeError("This Language cannot be used to generate ids anymore")

    def __repr__(self):
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
        self._next_id = None
