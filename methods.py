from collections import ChainMap


REQUIRED = False
OPTIONAL = True
STORAGE_NAME = 'params'


class ReqiredParamMissing(Exception):
    pass  # TODO: MAKE THE EXCEPTION MORE SPECIFIC


class TooManyParams(Exception):
    pass


class Parameter(property):
    def __init__(self, storage, name, valtype):
        fget = self._make_getter(storage, name)
        fset = self._make_setter(storage, name, valtype)
        fdel = self._make_deleter(storage, name)
        doc = f'Parameter {name} of type {valtype}'
        property.__init__(self, fget, fset, fdel, doc)

    @staticmethod
    def _make_getter(storage, name):
        return lambda obj: getattr(type(obj), storage)[obj][name]

    @staticmethod
    def _make_setter(storage, name, valtype):
        def fset(obj, val):
            if type(val) == valtype:
                getattr(type(obj), storage)[obj][name] = val
            else:
                err = f'attribute {name} is {valtype} not {type(val)}'
                raise AttributeError(err)
        return fset

    @staticmethod
    def _make_deleter(storage, name):
        def fdel(obj):
            obj_storage = getattr(type(obj), storage)[obj]
            del obj_storage[name]
        return fdel


# class ParamIter:
#     def __init__(self, groups):
#         self.groups = groups
#
#     def __next__(self):
#         for group in self.groups:
#             for param in group:
#                 yield param
#         raise StopIteration


class ParamSignature(ChainMap):
    def __init__(self, groups):
        self.required = groups[0]
        self.optional = groups[1]
        super().__init__(groups)


class ParamStorage(dict):
    def __init__(self, groups):
        self.signature = ParamSignature(groups)
        super().__init__()

    def set_obj_storage(self, obj):
        self[obj] = {}

    def get_params_view(self, obj):
        return self[obj].items()

    def fill_from_dict(self, obj, kwargs):
        for key in self.signature.required:
            try:
                val = kwargs.pop(key)
            except KeyError:
                raise ReqiredParamMissing(f'Parameter {key} is missing')
            self[obj][key] = val
        for key in self.signature.optional:
            val = kwargs.pop(key, None)
            if val is not None:
                self[obj][key] = val
        extra = list(kwargs.keys())
        if extra:
            raise TooManyParams(f'Parameters {extra} are not supported')

    def __getitem__(self, key):
        if not type(key) == int:
            key = id(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if not type(key) == int:
            key = id(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if not type(key) == int:
            key = id(key)
        super().__delitem__(key)

    @classmethod
    def insert_into_classdict(cls, classdict, storage_name):
        groups = {}, {}
        for name, req, vtype in cls._collect_from_classdict(classdict):
            group = groups[req]
            group[name] = vtype  # May change later to provide defaults
            classdict[name] = Parameter(storage_name, name, vtype)
        classdict[storage_name] = cls(groups)

    @staticmethod
    def _collect_from_classdict(classdict):
        for name, val in classdict.items():
            if not name.startswith('__'):
                yield name, val[0], val[1]


class Method(type):
    def __new__(meta, classname, supers, classdict):
        ParamStorage.insert_into_classdict(classdict, STORAGE_NAME)
        classdict['__init__'] = Method._func_init
        classdict['__del__'] = Method._func_del
        classdict['__str__'] = Method._func_str
        return type.__new__(meta, classname, supers, classdict)

    @staticmethod
    def _func_init(self, **kwargs):
        storage = getattr(self, STORAGE_NAME)
        storage.set_obj_storage(self)
        setattr(self, STORAGE_NAME, storage.get_params_view(self))
        storage.fill_from_dict(self, kwargs)
        object.__init__(self)

    @staticmethod
    def _func_del(self):
        storage = getattr(type(self), STORAGE_NAME)
        del storage[self]
        del self

    @staticmethod
    def _func_str(self):
        res = type(self).__name__
        params = getattr(self, STORAGE_NAME)
        if params:
            res += '?'
            data = []
            for key, val in params:
                data.append(f'{key}={str(val)}')
            res += '&'.join(data)
        return res


class getUpdates(metaclass=Method):
    offset = OPTIONAL, int
    limit = OPTIONAL, int
    timeout = OPTIONAL, int
    allowed_updates = OPTIONAL, list


if __name__ == '__main__':
    request = getUpdates(offset=100,
                         limit=3,
                         allowed_updates=['a', 'b'])
    print(request)
    print(getUpdates.params)
    del request
    print(getUpdates.params)
