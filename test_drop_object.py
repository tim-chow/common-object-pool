import logging

from common_object_pool.dedicate_object_pool import DedicateObjectPool
from common_object_pool.exceptions import MaxAttemptsReached

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
)

LOGGER = logging.getLogger(__name__)


def test(timeout=1, max_attempts=2):
    max_count = 2
    pool = DedicateObjectPool(max_count, object)

    for _ in range(max_count):
        object_id, _ = pool.get_object(timeout, max_attempts)
        pool.drop_object(object_id)

    for _ in range(max_count):
        _, obj = pool.get_object(timeout, max_attempts)
        LOGGER.debug("object is %r", obj)

    try:
        _, obj = pool.get_object(timeout, max_attempts)
    except MaxAttemptsReached:
        LOGGER.debug("max attempts reached")

    pool.close()


if __name__ == "__main__":
    test()

