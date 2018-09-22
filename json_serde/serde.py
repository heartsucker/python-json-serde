# -*- coding: utf-8 -*-

"""
De/Serialization classes.
"""

import hashlib
import linecache

from collections import OrderedDict
from datetime import datetime, timezone, date
from uuid import UUID


class Field:
    '''Base class for a field that should be de/serialized in a class.
    '''

    __COUNTER = 0

    def __init__(self, is_optional: bool=False, validators: list=None, rename=None,
                 write_optional: bool=False):
        ''':param is_optional: If the field is allowed to be missing/``null``/``None``.
           :param validators: List of functions taking ``(self, value)`` as args. **MUST** raise
               an ``Exception`` if they fail.
           :param rename: A different name for the JSON field.
           :param write_optional: Whether optional values should be written to the JSON object.
        '''
        self.counter = Field.__COUNTER
        Field.__COUNTER += 1

        if not is_optional and write_optional:
            raise ValueError("Cannot set 'write_optional' on a field with 'is_optional=False'")

        self.is_optional = is_optional
        self.validators = validators or []
        self.rename = rename
        self.write_optional = write_optional

    def from_json(self, value):
        '''Create an instance of this class from a JSON value.
        '''
        raise NotImplementedError

    def to_json(self, value):
        '''Convert this class to JSON compatible value.
        '''
        raise NotImplementedError

    def validate(self, value) -> None:
        '''Run a validation against the parsed value.
        '''
        pass

    def __repr__(self) -> str:
        return ('<Field counter={} is_optional={} validators={} rename={!r}>'
                .format(self.counter, self.is_optional, len(self.validators), self.rename))


class String(Field):
    '''De/serialize a JSON string.
    '''

    def from_json(self, value) -> str:
        return value

    def to_json(self, value: str) -> str:
        return value

    def validate(self, value) -> None:
        if not isinstance(value, str):
            raise TypeError("Expected 'str' but got {!r}".format(value.__class__.__name__))


class Integer(Field):
    '''De/serialize a JSON number (integers only).
    '''

    def from_json(self, value) -> int:
        return value

    def to_json(self, value: int) -> int:
        return value

    def validate(self, value) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected 'int' but got {!r}".format(value.__class__.__name__))


class Boolean(Field):
    '''De/serialize a JSON boolean.
    '''

    def from_json(self, value) -> bool:
        return value

    def to_json(self, value: bool) -> bool:
        return value

    def validate(self, value) -> None:
        if not isinstance(value, bool):
            raise TypeError("Expected 'bool' but got {!r}".format(value.__class__.__name__))


class Float(Field):
    '''De/serialize a JSON number (floats or ints).
    '''

    def from_json(self, value) -> float:
        if isinstance(value, int):
            value = float(value)
        return value

    def to_json(self, value: float) -> float:
        return value

    def validate(self, value) -> None:
        if not isinstance(value, float) and not isinstance(value, int):
            raise TypeError("Expected 'float' but got {!r}".format(value.__class__.__name__))


class IsoDateTime(Field):
    '''De/serialize a ISO8601 formated timestamp with timezone from/to a JSON string.
       Will correctly deserialize strings matching:
         - ``YYYY-MM-DD'T'hh:mm:ss.sss'Z'``
         - ``YYYY-MM-DD'T'hh:mm:ss'Z'``
         - ``YYYY-MM-DD'T'hh:mm:ss.sss±hhmm``
         - ``YYYY-MM-DD'T'hh:mm:ss±hhmm``
         - ``YYYY-MM-DD'T'hh:mm:ss.sss±hh:mm``
         - ``YYYY-MM-DD'T'hh:mm:ss±hh:mm``
    '''

    __FMT_STR_Z = '%Y-%m-%dT%H:%M:%SZ'
    __FMT_STRS = ['%Y-%m-%dT%H:%M:%S%z',
                  '%Y-%m-%dT%H:%M:%S.%f%z']

    def to_json(self, value) -> str:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if value.tzinfo == timezone.utc:
            return datetime.strftime(value, self.__FMT_STR_Z)
        return datetime.strftime(value, self.__FMT_STRS[0])

    def from_json(self, value: str) -> datetime:
        if not isinstance(value, str):
            raise ValueError('Cannot parse {!r} as a date'.format(value))
        if value.endswith('Z'):
            value = value[0:-1] + '+0000'
        else:
            if len(value) > 3 and value[-3] == ':':
                value = value[0:-3] + value[-2:]

        for fmt_str in self.__FMT_STRS:
            try:
                dt = datetime.strptime(value, fmt_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                pass
        raise ValueError('Date had bad format: {}'.format(value))

    def validate(self, value) -> None:
        if not isinstance(value, datetime):
            raise TypeError("Expected 'datetime' but got {!r}".format(value.__class__.__name__))


class IsoDate(Field):
    '''De/serialize a ISO8601 formated date (`YYYY-MM-DD`) from/to a JSON string.
    '''

    __FMT_STR = '%Y-%m-%d'

    def to_json(self, value) -> str:
        if value is None:
            return None
        return datetime.strftime(value, self.__FMT_STR)

    def from_json(self, value: str) -> datetime:
        if not isinstance(value, str):
            raise ValueError('Cannot parse {!r} as a date'.format(value))
        split = value.split('-')
        if len(split) != 3:
            raise ValueError('Date had bad format: {}'.format(value))
        return date(*[int(x) for x in split])

    def validate(self, value) -> None:
        if not isinstance(value, date):
            raise TypeError("Expected 'date' but got {!r}".format(value.__class__.__name__))


class Uuid(Field):
    '''De/serialize a JSON string to/from a UUID.
    '''

    def to_json(self, value: UUID) -> str:
        return str(value)

    def from_json(self, value: str) -> UUID:
        return UUID(value)

    def validate(self, value) -> None:
        if not isinstance(value, UUID):
            raise TypeError("Expected 'UUID' but got {!r}".format(value.__class__.__name__))


class List(Field):
    '''De/serialize a JSON array into a list of objects.
    '''

    def __init__(self, typ: type, *nargs, **kwargs) -> None:
        ''':param typ: The ``type`` to deserialize the list to.
           :param nargs: Passed to ``super()``.
           :param kwargs: Passed to ``super()``.
        '''

        super().__init__(*nargs, **kwargs)
        self.typ = typ

    def to_json(self, value: list) -> list:
        return [v.to_json() for v in value]

    def from_json(self, value: list) -> list:
        return [self.typ.from_json(v) for v in value]

    def validate(self, value) -> None:
        if not isinstance(value, list):
            raise TypeError("Expected 'list' but got {!r}".format(value.__class__))


class Nested(Field):
    '''De/serialize a nested JSON object.
    '''

    def __init__(self, typ: type, *nargs, **kwargs) -> None:
        ''':param typ: The ``type`` to deserialize the nested object to.
           :param nargs: Passed to ``super()``.
           :param kwargs: Passed to ``super()``.
        '''
        super().__init__(*nargs, **kwargs)
        self.typ = typ

    def to_json(self, value):
        return value.to_json()

    def from_json(self, value):
        return self.typ.from_json(value)

    def validate(self, value) -> None:
        if not isinstance(value, self.typ):
            raise TypeError("Expected {!r} but got {!r}".format(self.typ.__name__, value.__class__))


class JsonSerdeMeta(type):

    def __new__(mcs, name, bases, attrs):
        fields = []
        out = OrderedDict()

        for attr, value in attrs.items():
            if isinstance(value, Field):
                fields.append((attr, value))
            else:
                out[attr] = value

        fields = OrderedDict(sorted(fields, key=lambda kv: kv[1].counter))

        out['__init__'] = JsonSerdeMeta.mk_init(fields)
        out['to_json'] = JsonSerdeMeta.mk_to_json(fields)
        out['from_json'] = JsonSerdeMeta.mk_from_json(fields)
        out['__eq__'] = JsonSerdeMeta.mk_eq(fields)
        out['__ne__'] = lambda s, o: not s.__eq__(o)
        out['__hash__'] = JsonSerdeMeta.mk_hash(fields)
        out['__repr__'] = JsonSerdeMeta.mk_repr(name, fields)
        if fields:
            out['__validate'] = JsonSerdeMeta.mk_validate(fields)
        return type.__new__(mcs, name, bases, out)

    @staticmethod
    def mk_init(fields: OrderedDict) -> callable:
        slf = 'self'
        if fields:
            slf += ', '
        args = []
        init_lines = []

        for name, field in fields.items():
            keyword = name
            if field.is_optional:
                keyword += '=None'
            args.append(keyword)
            init_lines.append('    self.{name} = {name}'.format(name=name))

        args = ', '.join(args)
        init_lines.insert(0, 'def __init__({}{}) -> None:'.format(slf, args))
        if not fields:
            init_lines.append('    pass')
        else:
            init_lines.append('    self.__validate()')

        init = '\n'.join(init_lines)
        sha = hashlib.sha1()
        sha.update(init_lines[0].encode('utf-8'))
        filename = "<json_serde init {}>".format(sha.hexdigest())

        locs = {}
        bytecode = compile('\n'.join(init_lines), filename, 'exec')
        eval(bytecode, {}, locs)  # nosec

        linecache.cache[filename] = (
            len(init),
            None,
            init_lines,
            filename,
        )

        return locs['__init__']

    @staticmethod
    def mk_to_json(fields: OrderedDict) -> callable:
        def to_json(self) -> OrderedDict:
            out = {}
            for name, field in fields.items():
                val = field.to_json(getattr(self, name))
                rename = field.rename or name
                if val is None and field.is_optional and not field.write_optional:
                    continue
                out[rename] = val
            return out
        return to_json

    @staticmethod
    def mk_from_json(fields: OrderedDict) -> callable:
        def from_json(cls, value):
            nargs = []
            kwargs = {}

            for name, field in fields.items():
                rename = field.rename or name
                if rename in value:
                    val = value[rename]
                    if field.is_optional:
                        kwargs[name] = field.from_json(val)
                    else:
                        if isinstance(field, Nested):
                            val = field.typ.from_json(val)
                        elif isinstance(field, List):
                            if not isinstance(val, list):
                                raise TypeError(
                                    "Expected 'list' but got {!r}".format(val.__class__.__name__))
                            val = [field.typ.from_json(v) for v in val]
                        else:
                            val = field.from_json(val)
                        nargs.append(val)

            return cls(*nargs, **kwargs)
        return classmethod(from_json)

    @staticmethod
    def mk_eq(fields: OrderedDict) -> callable:
        def __eq__(self, other) -> bool:
            if not isinstance(other, self.__class__):
                return False
            for name in fields.keys():
                if getattr(self, name) != getattr(other, name):
                    return False
            return True
        return __eq__

    @staticmethod
    def mk_hash(fields: OrderedDict) -> callable:
        getters = ['frozenset(self.{k}) if isinstance(self.{k}, list) else self.{k}'.format(k=k)
                   for k in fields.keys()]
        hash_lines = ['def __hash__(self) -> int:',
                      '    return hash(({}))'.format(', '.join(getters))]

        sha = hashlib.sha1()
        sha.update((','.join([k for k in fields.keys()]).encode('utf-8')))
        filename = "<json_serde hash {}>".format(sha.hexdigest())

        hash_ = '\n'.join(hash_lines)
        locs = {}
        bytecode = compile(hash_, filename, 'exec')
        eval(bytecode, {}, locs)  # nosec

        linecache.cache[filename] = (
            len(hash_),
            None,
            hash_lines,
            filename,
        )

        return locs['__hash__']

    @staticmethod
    def mk_validate(fields: OrderedDict) -> callable:
        def __validate(self) -> None:
            for name, field in fields.items():
                value = getattr(self, name)
                if value is None:
                    if not field.is_optional:
                        raise ValueError('{} was None'.format(value))
                else:
                    field.validate(value)
                for validator in field.validators:
                    validator(self, value)
        return __validate

    @staticmethod
    def mk_repr(name: str, fields: OrderedDict) -> callable:
        def __repr__(self) -> str:
            if not fields:
                return '<{}>'.format(name)
            out = ['<{}'.format(name)]
            for f_name, field in fields.items():
                f_name = field.rename or f_name
                out.append(' {}={!r}'.format(f_name, getattr(self, f_name)))
            out.append('>')
            return ''.join(out)

        return __repr__


class JsonSerde(metaclass=JsonSerdeMeta):

    '''Base class for all classes that implement auto JSON de/serialization.
    '''

    pass
