import logging
import threading
import time

from common_object_pool.shared_object_pool import SharedObjectPool
from common_object_pool import get_object
from common_object_pool.exceptions import MaxAttemptsReached

LOGGER = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(threadName)s %(asctime)s "
           "%(filename)s:%(lineno)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")


def target(sleep_time, object_pool, *args, **kwargs):
    try:
        with get_object(object_pool,
                            *args,
                            **kwargs) as obj:
            LOGGER.info("object is %s", obj)
            time.sleep(sleep_time)
    except MaxAttemptsReached:
        LOGGER.error("max attempts reached")


def test(
        thread_count,
        sleep_time,
        object_pool,
        timeout,
        max_attempts):
    threads = []
    for ind in range(thread_count):
        t = threading.Thread(
            target=target,
            args=(sleep_time,
                  object_pool,
                  timeout,
                  max_attempts))
        t.setName("test-thread-%d" % ind)
        t.setDaemon(True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    object_pool.close()


class Factory(object):
    def close(self):
        LOGGER.debug("object %r is closed", self)


if __name__ == "__main__":
    thread_count = 20
    sleep_time = 1

    max_shared_count = 2
    max_count = 3
    object_pool = SharedObjectPool(
        max_shared_count,
        max_count,
        Factory
    )

    timeout = 1.5
    max_attempts = 5

    test(
        thread_count,
        sleep_time,
        object_pool,
        timeout,
        max_attempts
    )
