# coding: utf8

import logging
import abc
import threading
import sys

from .exceptions import MaxAttemptsReached

LOGGER = logging.getLogger(__name__)


class AbstractObjectPool(object):
    __metaclass__ = abc.ABCMeta
    __LOCK = threading.Lock()
    __ID = 0

    def __init__(self, max_count, factory=None):
        if factory is not None:
            assert callable(factory), "factory must be callable"
        self._creating_count = 0
        self._created_count = 0
        self._condition = threading.Condition()
        self._closing = False
        self._closed = False

        self._factory = factory
        self._max_count = max_count

    @abc.abstractmethod
    def has_free_object(self):
        pass

    @abc.abstractmethod
    def get_free_object(self):
        pass

    @abc.abstractmethod
    def store_newly_created_object(self, object_id, obj):
        pass

    def get_object(
            self,
            timeout=None,
            max_attempts=None,
            factory=None):
        """
        获取对象

        @param timeout None、不小于0的数值
            当对象池中没有空闲对象时，线程等待的时间，
            None 表示等待到其它线程释放或销毁对象。
            线程的最大等待时间等于 timeout * (max_attempts or 1)
        @param max_attempts None、不小于0的整数
            线程尝试获取对象的最大次数
        @param factory None、可调用对象
            对象池调用该可调用对象创建对象

        @return (int, object)
            由 ID 和对象组成的元组

        @raise MaxRetriesReached
            当线程尝试获取连接的次数达到指定的最大次数时，抛出该异常
        @raise RuntimeError
            当调用方既没有通过该方法的 factory 参数， 也没有通过构造方法指定 factory 时，
            抛出该异常
        @raise BaseException
            调用 factory 时出现的异常，会被抛出
        @raise RuntimeError
            当对象池正在或已经关闭时，调用该方法将引发该异常
        """
        if factory is not None:
            assert callable(factory), "factory must be callable"

        cf = factory or self._factory
        if cf is None:
            raise RuntimeError("no factory specified")

        with self._condition:
            if self._closing or self._closed:
                raise RuntimeError("pool closed")
            loop_count = 1
            max_attempts = max_attempts or 1
            while loop_count <= max_attempts:
                if self._closing or self._closed:
                    raise RuntimeError("pool closed")
                if self.has_free_object():
                    object_id, obj = self.get_free_object()
                    LOGGER.debug("get object %d from pool", object_id)
                    return object_id, obj
                if self._creating_count + self._created_count < self._max_count:
                    LOGGER.debug("will create new object")
                    self._creating_count = self._creating_count + 1
                    break
                if loop_count < max_attempts:
                    LOGGER.debug("wait for idle objects")
                    self._condition.wait(timeout)
                loop_count = loop_count + 1
            else:
                raise MaxAttemptsReached("max attempts reached")

        obj = None
        exc_info = None
        try:
            obj = cf()
        except Exception:
            exc_info = sys.exc_info()

        with self._condition:
            if self._closing or self._closed:
                if obj is not None:
                    try_close(obj)
                raise RuntimeError("pool closed")

            self._creating_count = self._creating_count - 1

            if obj is not None:
                self._created_count = self._created_count + 1
                object_id = self.get_id()
                LOGGER.debug("store newly created object %d", object_id)
                self.store_newly_created_object(object_id, obj)
                return object_id, obj
            LOGGER.error("fail to create object")
            raise exc_info[0], exc_info[1], exc_info[2]

    @abc.abstractmethod
    def is_using(self, object_id):
        pass

    @abc.abstractmethod
    def restore_object(self, object_id):
        pass

    def release_object(self, object_id):
        """
        将对象放回对象池

        @param object_id int
            对象ID

        @return None

        @raise RuntimeError
            当对象池正在关闭时，调用该方法将引发该异常
        """
        with self._condition:
            if self._closing or self._closed:
                raise RuntimeError("pool closed")

            if not self.is_using(object_id):
                LOGGER.error("unknown object id %d", object_id)
                return
            LOGGER.debug("release using object %d to pool", object_id)
            self.restore_object(object_id)
            self._condition.notify_all()

    @abc.abstractmethod
    def remove_using_object_from_pool(self, object_id):
        pass

    @abc.abstractmethod
    def is_idle(self, object_id):
        pass

    @abc.abstractmethod
    def remove_idle_object_from_pool(self, object_id):
        pass

    def drop_object(self, object_id):
        """
        从对象池中移除对象
        比如，当对象是一个网络连接时，如果调用方发现该连接不可用，则应该调用该方法移除该连接

        @param object_id int
            对象ID

        @return None

        @raise RuntimeError
            当对象池正在关闭时，调用该方法将引发该异常
        """
        with self._condition:
            if self._closing or self._closed:
                raise RuntimeError("pool closed")

            if self.is_using(object_id):
                self._created_count = self._created_count - 1
                LOGGER.debug("drop using object %d", object_id)
                self.remove_using_object_from_pool(object_id)
            elif self.is_idle(object_id):
                self._created_count = self._created_count - 1
                LOGGER.debug("drop idle object %d", object_id)
                self.remove_idle_object_from_pool(object_id)
            else:
                LOGGER.debug("unknown object %d", object_id)

            self._condition.notify_all()

    @classmethod
    def get_id(cls):
        """
        获取唯一ID

        @return int
        """
        with cls.__LOCK:
            cls.__ID = cls.__ID + 1
            return cls.__ID

    @abc.abstractmethod
    def iter_created_objects(self):
        pass

    def close(self):
        if self._closing or self._closed:
            return
        with self._condition:
            if self._closing or self._closed:
                return
            self._closing = True
            self._condition.notify_all()

        for obj in self.iter_created_objects():
            try_close(obj)

        self._closing = False
        self._closed = True


def try_close(obj):
    attr = getattr(obj, 'close', None)
    if attr is not None and callable(attr):
        try:
            attr()
        except Exception:
            LOGGER.error("fail to call close",
                         exc_info=True)
