import pytest

from datetime import datetime, timezone
from uuid import UUID

from json_serde.serde import JsonSerde, String, Float, Integer, Boolean, List, Nested, Field, \
        IsoDateTime, Uuid


def test_string():
    class Foo(JsonSerde):
        bar = String()

    out = {'bar': 'bar'}
    foo = Foo('bar')

    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    with pytest.raises(TypeError):
        Foo.from_json({'bar': 123})


def test_int():
    class Foo(JsonSerde):
        bar = Integer()

    out = {'bar': 1312}
    foo = Foo(1312)
    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    with pytest.raises(TypeError):
        Foo.from_json({'bar': '1312'})


def test_boolean():
    class Foo(JsonSerde):
        bar = Boolean()

    out = {'bar': True}
    foo = Foo(True)
    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    with pytest.raises(TypeError):
        Foo.from_json({'bar': 'true'})


def test_float():
    class Foo(JsonSerde):
        bar = Float()

    out = {'bar': 13.12}
    foo = Foo(13.12)
    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    out = {'bar': 1312}
    foo = Foo(1312)
    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    with pytest.raises(TypeError):
        Foo.from_json({'bar': '123'})


def test_uuid():
    class Foo(JsonSerde):
        bar = Uuid()

    uuid_str = 'a629f931-0463-4b66-b9f3-f66b48deebb0'
    out = {'bar': uuid_str}
    foo = Foo(UUID(uuid_str))
    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    out = {'bar': uuid_str.upper()}
    assert Foo.from_json(out) == foo


def test_datetime():
    class Foo(JsonSerde):
        bar = IsoDateTime()

    out = {'bar': '2018-01-01T00:00:00+0000'}
    foo = Foo(datetime(2018, 1, 1, 0, 0, 0, 0, timezone.utc))
    assert foo.to_json() == out
    assert Foo.from_json(out) == foo

    dates = [
        '2018-01-01T00:00:00+0000',
        '2018-01-01T00:00:00+00:00',
        '2018-01-01T00:00:00Z',
        '2018-01-01T00:00:00.000+0000',
        '2018-01-01T00:00:00.000+00:00',
        '2018-01-01T00:00:00.000Z',
    ]

    for date in dates:
        out = {'bar': date}
        assert Foo.from_json(out) == foo


def test_validator():
    MSG = 'NOT MORE THAN THREE'

    def more_than_three(self, x) -> None:
        if x <= 3:
            raise ValueError(MSG)

    class Foo(JsonSerde):
        bar = Integer(validators=[more_than_three])

    foo = Foo(4)
    assert foo.bar == 4

    with pytest.raises(ValueError) as e:
        Foo(2)
    assert str(e.value) == MSG


def test_optional():
    class Foo(JsonSerde):
        foo = String()

    with pytest.raises(ValueError):
        Foo(None)

    class Foo(JsonSerde):
        foo = String(is_optional=True)

    foo = Foo()
    assert foo.to_json() == {}
    assert foo.from_json({}) == foo
    assert Foo.from_json({'foo': 'foo'}) == Foo('foo')


def test_list():
    class Bar(JsonSerde):
        bar = String()

    class Foo(JsonSerde):
        foo = List(Bar)

    out = {
        'foo': [
            {'bar': 'wat'},
            {'bar': 'lol'},
        ]
    }

    bars = [Bar('wat'), Bar('lol')]
    foo = Foo(bars)

    assert Foo.from_json(out) == foo
    assert foo.to_json() == out

    out = {
        'foo': {'bar': 'wat'},
    }

    with pytest.raises(TypeError):
        Foo.from_json(out)


def test_nested():
    class Bar(JsonSerde):
        baz = String()

    class Foo(JsonSerde):
        bar = Nested(Bar)

    out = {
        'bar': {
            'baz': 'baz',
        },
    }

    bar = Bar('baz')
    foo = Foo(bar)

    assert foo.to_json() == out
    assert Foo.from_json(out) == foo


def test_rename():
    class Foo(JsonSerde):
        wat = String(rename='bar')

    out = {'bar': 'bar'}
    foo = Foo('bar')
    assert foo == Foo(wat='bar')
    assert Foo.from_json(out) == foo
    assert foo.to_json() == out


def test_repr():
    class Foo(JsonSerde):
        wat = String()

    foo = Foo('wat')
    repr(foo)

    class Foo(JsonSerde):
        pass

    foo = Foo()
    repr(foo)


def test_hash():
    class Foo(JsonSerde):
        wat = String()

    foo = Foo('wat')
    assert isinstance(hash(foo), int)


def test_eq():
    class Foo(JsonSerde):
        wat = String()

    f1 = Foo('123')
    f2 = Foo('123')
    f3 = Foo('345')

    assert f1 == f2
    assert f1 != f3
    assert f1 != 'bad type'


def test_field_counter():
    f1 = String()
    f2 = String()

    assert f2.counter > f1.counter

    # be damn sure that we don't have non-determinism in anything
    json = {chr(x): chr(x) for x in range(97, 105)}
    for _ in range(1000):
        class Foo(JsonSerde):
            a = String()
            b = String()
            c = String()
            d = String()
            e = String()
            f = String()
            g = String()
            h = String()

        f1 = Foo.from_json(json)
        f2 = Foo.from_json(json)

        assert f1 == f2
        assert not (f1 != f2)
        assert hash(f1) == hash(f2)
        assert repr(f1) == repr(f2)


def test_field():
    f = Field()

    with pytest.raises(NotImplementedError):
        f.to_json('wat')

    with pytest.raises(NotImplementedError):
        f.from_json('wat')

    f.validate('wat')
    repr(f)
