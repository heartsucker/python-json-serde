``json-serde``
==============

``json-serde`` is a tool to make de/serializing JSON into/from Python classes easy.

Quick Start
-----------

.. code:: python

    from json_serde import JsonSerde, String, Integer, IsoDateTime


    class User(JsonSerde):

        username = String()
        user_id = Integer(rename='userId')
        birthday = IsoDateTime(is_optional=True, default=None)

        @staticmethod
        def what_should_we_do():
            return 'Hurry up'


    some_json = {'username': 'abonanno',
                 'userId': 1312}
    user = User.from_json(some_json)

    assert user.username = 'abonanno'
    assert user.user_id == 1312
    assert user.birthday is None
    assert user.to_json() == some_json
    assert User.what_should_we_do() == 'Hurry up'


.. note::

    ``json-serde`` uses the value ``Absent`` to indicate when a value was not present in the JSON.
    Using ``None`` would be ambiguous in this case as it would not be clear if the value was not
    present or was ``null``.


Full API Docs
-------------

Full :doc:`API Docs </api/modules>` cover basic usage of this package.

.. toctree::
    :maxdepth: 2
    :caption: API Docs:

    api/modules
