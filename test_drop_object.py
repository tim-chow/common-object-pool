import logging

from common_object_pool.dedicate_object_pool import DedicateObjectPool
from common_object_pool import get_object
from common_object_pool.exceptions import ObjectUnusable

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
)

LOGGER = logging.getLogger(__name__)


def test(raise_=False, timeout=2, max_attempts=2):
    max_count = 2
    pool = DedicateObjectPool(max_count, object)

    try:
        with get_object(pool, timeout, max_attempts) as obj:
            if raise_:
                raise ObjectUnusable("object is unusable")
    except ObjectUnusable:
        pass

    with get_object(pool, timeout, max_attempts) as obj:
        LOGGER.info("object is %r" % obj)


if __name__ == "__main__":
    test()
    test(True)
