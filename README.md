# json_serde

JSON de/serializer for Python, inspired by `attrs` and `SQLAlchemy`.

## Example

```python
import requests
from json_serde import JsonSerde, Integer, String, IsoDateTime


class User(JsonSerde):
    username = String()
    user_id = Integer(rename='userId')
    birthday = IsoDateTime(optional=True)


resp = requests.get('https://example.com/api/user')
resp.raise_for_status()

api_response = resp.json()
# {'username': 'emmag', 'userId': 1312, 'somethingElse': ['irrelevant']}

user = User.from_json(api_response)
assert user.username = 'emmag'
assert isinstance(user.user_id, int)
assert user.birthday is None
```

## License

This work is dual licensed under the MIT and Apache-2.0 licenses. See [LICENSE-MIT](./LICENSE-MIT)
and [LICENSE-APACHE](./LICENSE-APACHE) for details.
