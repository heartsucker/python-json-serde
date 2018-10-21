# -*- coding: utf-8 -*-

"""
De/Serialization classes.
"""

import hashlib
import linecache

from collections import OrderedDict
from datetime import datetime, timezone, date
from uuid import UUID

from ._utils import Absent


class SerdeError(Exception):
    '''
    Generic error returned on de/serialization exceptions. The error is designed to contain
    information that is safe to return in an API response without sanitation.
    '''
    pass


class Field:
    '''
    Base class for a field that should be de/serialized in a class.
    '''

    __COUNTER = 0

    def __init__(self,
                 is_optional: bool=False,
                 validators: list=None,
                 rename=None,
                 write_null: bool=False,
                 write_absent: bool=False,
                 default=Absent,
                 default_factory=None):
        ''':param is_optional: If the field is allowed to be ``null``/``None``/``Absent``.
           :param validators: List of functions taking ``(self, value)`` as args. **MUST** raise
               a ``SerdeError`` if they fail.
           :param rename: A different name for the JSON field.
           :param write_null: Whether null values should be written to the JSON object.
           :param write_absent: Whether absent values shoudl be writtne to the JSON object as null.
           :param default: Provide a default value when the value is absent.
           :param default_factory: Generate a default value when the value is absent.
        '''
        self.counter = Field.__COUNTER
        Field.__COUNTER += 1

        if not is_optional and write_null:
            raise ValueError("Cannot have 'is_optional=False' and 'write_null=True'")

        if not is_optional and write_absent:
            raise ValueError("Cannot have 'is_optional=False' and 'write_absent=True'")

        if default is not Absent and default_factory is not None:
            raise ValueError("Cannot have a 'default' and a 'default_factory'")

        self.is_optional = is_optional
        self.validators = validators or []
        self.rename = rename
        self.write_null = write_null
        self.write_absent = write_absent
        self.default = default
        self.default_factory = default_factory

    def from_json(self, value):
        '''Create an instance of this class from a JSON value.
        '''
        raise NotImplementedError

    def to_json(self, value):
        '''Convert this class to JSON compatible value.
        '''
        raise NotImplementedError

    def __repr__(self) -> str:
        return ('<Field counter={} is_optional={} validators={} rename={!r}>'
                .format(self.counter, self.is_optional, len(self.validators), self.rename))


class String(Field):
    '''De/serialize a JSON string.
    '''

    def from_json(self, value) -> str:
        if not isinstance(value, str):
            raise SerdeError("Expected a string.")
        return value

    def to_json(self, value: str) -> str:
        return value


class Integer(Field):
    '''De/serialize a JSON number (integers only).
    '''

    def from_json(self, value) -> int:
        if not isinstance(value, int):
            raise SerdeError("Expected an integer.")
        return value

    def to_json(self, value: int) -> int:
        return value


class Boolean(Field):
    '''De/serialize a JSON boolean.
    '''

    def from_json(self, value) -> bool:
        if not isinstance(value, bool):
            raise SerdeError("Expected a boolean.")
        return value

    def to_json(self, value: bool) -> bool:
        return value


class Float(Field):
    '''De/serialize a JSON number (floats or ints).
    '''

    def from_json(self, value) -> float:
        if not isinstance(value, float) and not isinstance(value, int):
            raise SerdeError("Expected a number.")
        if isinstance(value, int):
            value = float(value)
        return value

    def to_json(self, value: float) -> float:
        return value


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
            raise SerdeError('Cannot parse as a date')
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
        raise SerdeError('Illegal date format.')


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
            raise SerdeError('Cannot parse as a date.')
        split = value.split('-')
        if len(split) != 3:
            raise SerdeError('Date had bad format.')
        return date(*[int(x) for x in split])


class Uuid(Field):
    '''De/serialize a JSON string to/from a UUID.
    '''

    def to_json(self, value: UUID) -> str:
        return str(value)

    def from_json(self, value: str) -> UUID:
        if not isinstance(value, str):
            raise SerdeError('Cannot parse as a UUID.')
        try:
            return UUID(value)
        except ValueError:
            raise SerdeError('UUID had bad format.')


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
        if not isinstance(value, list):
            raise TypeError('Expected a list.')
        return [self.typ.from_json(v) for v in value]


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
        if value is None:
            return None
        return value.to_json()

    def from_json(self, value):
        return self.typ.from_json(value)


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
        default_map = {}

        for name, field in fields.items():
            keyword = name
            if field.is_optional:
                keyword += '=None'
            args.append(keyword)
            if field.is_optional:
                if field.default is not Absent:
                    default = field.default
                    set_default = '__default_map__["{name}"]'.format(name=name)
                elif field.default_factory is not None:
                    default = field.default_factory
                    set_default = '__default_map__["{name}"]()'.format(name=name)
                else:
                    default = None
                    set_default = name

                default_map[name] = default

                lines = ('    if {name} is Absent or {name} is None:\n'
                         '        self.{name} = {set_default}\n'
                         '    else:\n'
                         '        self.{name} = {name}\n')
                init_lines.append(lines.format(name=name, set_default=set_default))
            else:
                init_lines.append('    self.{name} = {name}'.format(name=name))

        args = ', '.join(args)
        init_lines.insert(0, 'def __init__({}{}) -> None:'.format(slf, args))
        if not fields:
            init_lines.append('    pass')
        else:
            init_lines.append('    self.__validate()')

        init = '\n'.join(init_lines)
        sha = hashlib.sha1()  # nosec
        sha.update(init_lines[0].encode('utf-8'))
        filename = "<json_serde init {}>".format(sha.hexdigest())

        locs = {}
        variables = {
            'Absent': Absent,
            '__default_map__': default_map,
        }
        bytecode = compile('\n'.join(init_lines), filename, 'exec')
        eval(bytecode, variables, locs)  # nosec

        linecache.cache[filename] = (
            len(init),
            None,
            init_lines,
            filename,
        )

        return locs['__init__']

    @staticmethod
    def mk_to_json(fields: OrderedDict) -> callable:
        def to_json(self) -> dict:
            out = {}
            for name, field in fields.items():
                val = getattr(self, name)
                rename = field.rename or name
                if val is None:
                    if field.write_null:
                        out[rename] = None
                elif val is Absent:
                    if field.write_absent:
                        out[rename] = None
                else:
                    val = field.to_json(val)
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
                if rename not in value:
                    val = Absent
                else:
                    val = value[rename]

                if field.is_optional:
                    if val is not None and val is not Absent:
                        kwargs[name] = field.from_json(val)
                    else:
                        kwargs[name] = val
                else:
                    if isinstance(field, Nested):
                        if val is not None or val is not Absent:
                            val = field.typ.from_json(val)
                    elif isinstance(field, List):
                        if not isinstance(val, list):
                            raise TypeError(
                                "Expected 'list' but got {!r}".format(val.__class__.__name__))

                        def parser(v):
                            if v is not None and v is not Absent:
                                return field.typ.from_json(v)
                            else:
                                return v

                        val = [parser(v) for v in val]
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

        sha = hashlib.sha1()  # nosec
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
                rename = field.rename or name
                value = getattr(self, name)
                if value is None or value is Absent:
                    if not field.is_optional:
                        raise SerdeError('Field {!r} is required.'.format(rename))
                for validator in field.validators:
                    try:
                        validator(self, value)
                    except SerdeError as e:
                        raise SerdeError('Field {!r}: {}'.format(rename, e))
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
