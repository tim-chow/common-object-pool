from .abstract_object_poll import AbstractObjectPool


class SharedObjectPool(AbstractObjectPool):
    def __init__(self, max_shared_count, max_count, factory=None):
        AbstractObjectPool.__init__(self, max_count, factory)
        self._max_shared_count = max_shared_count
        self._objects = {}
        self._id_to_shared_count = {}
        self._available_object_ids = []

    def has_free_object(self):
        return len(self._available_object_ids) > 0

    def get_free_object(self):
        object_id = self._available_object_ids[0]
        self._id_to_shared_count[object_id] = \
            self._id_to_shared_count.get(object_id, 0) + 1
        if self._id_to_shared_count[object_id] == self._max_shared_count:
            self._available_object_ids.pop(0)
        return object_id, self._objects[object_id]

    def store_newly_created_object(self, object_id, obj):
        self._objects[object_id] = obj
        self._id_to_shared_count[object_id] = 1
        if self._max_shared_count > 1:
            self._available_object_ids.append(object_id)

    def is_using(self, object_id):
        if object_id not in self._objects:
            return False
        return self._id_to_shared_count[object_id] > 0

    def is_idle(self, object_id):
        if object_id not in self._objects:
            return False
        return self._id_to_shared_count[object_id] == 0

    def restore_object(self, object_id):
        self._id_to_shared_count[object_id] = \
            self._id_to_shared_count[object_id] - 1
        if self._id_to_shared_count[object_id] < self._max_shared_count:
            if object_id not in self._available_object_ids:
                self._available_object_ids.append(object_id)

    def remove_using_object_from_pool(self, object_id):
        self._objects.pop(object_id)
        self._id_to_shared_count.pop(object_id)

        try:
            self._available_object_ids.remove(object_id)
        except ValueError:
            pass

    remove_idle_object_from_pool = remove_using_object_from_pool

    def iter_created_objects(self):
        for obj in self._objects.itervalues():
            yield obj
