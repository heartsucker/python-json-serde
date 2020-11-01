# Changelog

## 0.0.10 - 2020-11-01

- Renamed `_Absent` to `AbsentType`
- Made `Absent` falsey
- Removed support for deprecated Python versions (3.4, 3.5)
- Added support for new Python versions (3.8, 3.9)

## 0.0.9 - 2018-10-23

- Added field names to errors to help devs / consumers

## 0.0.8 - 2018-10-21

- Added support for defaults and differentiating between `null` and not-present values

## 0.0.7 - 2018-10-15

- Fix bug with nesting and `null`/missing fields

## 0.0.6 - 2018-09-22
- IsoDate type

## 0.0.5 - 2018-09-19
- Better parsing of timestamps

## 0.0.4 - 2018-09-19
- Correctly parse optional args

## 0.0.3 - 2018-09-19
- Added UUIDs
- Allow writing of optional fields to JSON

## 0.0.2 - 2018-09-19
- Fixed failures on optional ISO8601 timestamps

## 0.0.1 - 2018-07-07
- Fixed failures on valid ISO8601 timestamps

## 0.0.0 - 2018-07-07
- Initial release
- Basic JSON de/serialization utilities
