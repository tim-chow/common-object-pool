class ObjectPoolException(Exception):
    pass


class MaxAttemptsReached(ObjectPoolException):
    pass


class ObjectUnusable(ObjectPoolException):
    pass
