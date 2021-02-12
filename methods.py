from collections import ChainMap
from copy import deepcopy


REQUIRED = False
OPTIONAL = True
HOLDER_NAME = 'params'


class ReqiredParamError(Exception):
    pass  # TODO: MAKE THE EXCEPTION MORE SPECIFIC


class Parameter(property):
    def __init__(self, holder, name, valtype):
        fget = self._make_getter(holder, name)
        fset = self._make_setter(holder, name, valtype)
        fdel = self._make_deleter(holder, name)
        doc = f'Parameter {name} of type {valtype}'
        property.__init__(self, fget, fset, fdel, doc)

    @staticmethod
    def _make_getter(holder, name):
        return lambda obj: getattr(obj, holder)[name]

    @staticmethod
    def _make_setter(holder, name, valtype):
        def fset(obj, val):
            if type(val) == valtype:
                getattr(obj, holder)[name] = val
            else:
                err = f'attribute {name} is {valtype} not {type(val)}'
                raise AttributeError(err)
        return fset

    @staticmethod
    def _make_deleter(holder, name):
        def fdel(obj):
            obj_holder = getattr(obj, holder)
            del obj_holder[name]
        return fdel


class ParamHolder(ChainMap):
    def __init__(self, req, opt):
        self.required = req
        self.optional = opt
        ChainMap.__init__(self, req, opt)

    def fill_from_dict(self, obj, kwargs):
        for key in list(self.required):
            val = kwargs.get(key)
            if val is None:
                raise ReqiredParamError('Parameter', key, 'is missing')
            setattr(obj, key, val)
        for key in list(self.optional):
            val = kwargs.get(key)
            if val is not None:
                setattr(obj, key, val)
            else:
                delattr(obj, key)

    def __setitem__(self, key, val):
        if key in self.required:
            self.required[key] = val
        else:
            self.optional[key] = val

    def __delitem__(self, key):
        try:
            del self.required[key]
        except KeyError:
            del self.optional[key]

    @classmethod
    def fromholder(cls, holder):
        return deepcopy(holder)

    @classmethod
    def insert_into_classdict(cls, classdict, holder_name):
        groups = {}, {}
        for name, req, vtype in cls._collect_from_classdict(classdict):
            group = groups[req]
            group[name] = None  # May change later to provide defaults
            classdict[name] = Parameter(holder_name, name, vtype)
        classdict[holder_name] = cls(*groups)

    @staticmethod
    def _collect_from_classdict(classdict):
        for name, val in classdict.items():
            if not name.startswith('__'):
                yield name, val[0], val[1]


class Method(type):
    def __new__(meta, classname, supers, classdict):
        ParamHolder.insert_into_classdict(classdict, HOLDER_NAME)
        classdict['__init__'] = Method._func_init
        classdict['__str__'] = Method._func_str
        return type.__new__(meta, classname, supers, classdict)

    @staticmethod
    def _func_init(self, **kwargs):
        params = ParamHolder.fromholder(getattr(type(self), HOLDER_NAME))
        setattr(self, HOLDER_NAME, params)
        params.fill_from_dict(self, kwargs)

    @staticmethod
    def _func_str(self):
        res = type(self).__qualname__
        if self.__dict__:
            res += '?'
        data = []
        for key, val in self.params.items():
            data.append(f'{key}={str(val)}')
        return res + '&'.join(data)


class getUpdates(metaclass=Method):
    offset = OPTIONAL, int
    limit = OPTIONAL, int
    timeout = OPTIONAL, int
    allowed_updates = OPTIONAL, list


if __name__ == '__main__':
    request = getUpdates(offset=100, limit=3, value=100)
    print(request)
