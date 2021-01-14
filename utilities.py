# OrderedSet taken from: https://stackoverflow.com/a/1653978/7022904 (license: https://creativecommons.org/licenses/by-sa/4.0/)

import collections

class OrderedSet(collections.OrderedDict, collections.MutableSet):

    def update(self, *args, **kwargs):
        if kwargs:
            raise TypeError("update() takes no keyword arguments")

        for s in args:
            for e in s:
                 self.add(e)

    def add(self, elem):
        self[elem] = None

    def discard(self, elem):
        self.pop(elem, None)

    def __eq__(self, other):
        for i in self:
            if i not in other:
                return False

        for i in other:
            if i not in self:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return all(e in other for e in self)

    def __lt__(self, other):
        return self <= other and self != other

    def __ge__(self, other):
        return all(e in self for e in other)

    def __gt__(self, other):
        return self >= other and self != other

    def __repr__(self):
        return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))

    def __str__(self):
        return '{%s}' % (', '.join(map(repr, self.keys())))

    def __init__(self, collection=set()):
        super().__init__()
        for i in collection:
            self.add(i)
    
    difference = collections.MutableSet.__sub__ 
    difference_update = collections.MutableSet.__isub__
    intersection = collections.MutableSet.__and__
    intersection_update = collections.MutableSet.__iand__
    issubset = collections.MutableSet.__le__
    issuperset = collections.MutableSet.__ge__
    symmetric_difference = collections.MutableSet.__xor__
    symmetric_difference_update = collections.MutableSet.__ixor__
    union = collections.MutableSet.__or__

class CaseInsensitiveDict():
    
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)
        self._convert_keys()
    
    def __getitem__(self, key):
        return self._dict.__getitem__(self.__class__._k(key))
    
    def __setitem__(self, key, value):
        self._dict.__setitem__(self.__class__._k(key), value)
        
    def __delitem__(self, key):
        return self._dict.__delitem__(self.__class__._k(key))
    
    def __contains__(self, key):
        return self._dict.__contains__(self.__class__._k(key))

    def pop(self, key, *args, **kwargs):
        return self._dict.pop(self.__class__._k(key), *args, **kwargs)
    
    def get(self, key, *args, **kwargs):
        return self._dict.get(self.__class__._k(key), *args, **kwargs)
    
    def setdefault(self, key, *args, **kwargs):
        return self._dict.setdefault(self.__class__._k(key), *args, **kwargs)
    
    def update(self, E={}, **F):
        self._dict.update(self.__class__(E))
        self._dict.update(self.__class__(**F))

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def __iter__(self):
        for k in self._dict:
            yield k
    
    def _convert_keys(self):
        self._dict = {k.lower(): v for k, v in self._dict.items()}
