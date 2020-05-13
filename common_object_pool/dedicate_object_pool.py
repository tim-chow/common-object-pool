from .abstract_object_pool import AbstractObjectPool


class DedicateObjectPool(AbstractObjectPool):
    def __init__(self, max_count, factory=None):
        AbstractObjectPool.__init__(self, max_count, factory)
        self._idle_object_ids = []
        self._idle_objects = {}
        self._using_objects = {}

    def has_free_object(self):
        return len(self._idle_object_ids) > 0

    def get_free_object(self):
        object_id = self._idle_object_ids.pop(0)
        obj = self._idle_objects.pop(object_id)
        self._using_objects[object_id] = obj
        return object_id, obj

    def store_newly_created_object(self, object_id, obj):
        self._using_objects[object_id] = obj

    def is_using(self, object_id):
        return object_id in self._using_objects

    def is_idle(self, object_id):
        return object_id in self._idle_objects

    def restore_object(self, object_id):
        obj = self._using_objects.pop(object_id)
        self._idle_object_ids.append(object_id)
        self._idle_objects[object_id] = obj

    def remove_idle_object_from_pool(self, object_id):
        self._idle_objects.pop(object_id)
        self._idle_object_ids.remove(object_id)

    def remove_using_object_from_pool(self, object_id):
        self._using_objects.pop(object_id)

    def iter_created_objects(self):
        for obj in self._idle_objects.values():
            yield obj

        for obj in self._using_objects.values():
            yield obj
