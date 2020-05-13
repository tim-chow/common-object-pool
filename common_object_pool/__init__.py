from contextlib import contextmanager
import sys

from .exceptions import ObjectUnusable


@contextmanager
def get_object(
        object_pool,
        *args,
        **kwargs):
    object_id, obj = object_pool.get_object(*args, **kwargs)
    exc_info = None
    try:
        yield obj
    except ObjectUnusable:
        object_pool.drop_object(object_id)
        raise
    except:
        exc_info = sys.exc_info()

    object_pool.release_object(object_id)
    if exc_info:
        raise exc_info[0], exc_info[1], exc_info[2]
