from common_object_pool.dedicate_object_pool import DedicateObjectPool

from test_shared_object_pool import test, Factory


if __name__ == "__main__":
    thread_count = 20
    sleep_time = 3

    max_count = 3
    object_pool = DedicateObjectPool(
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