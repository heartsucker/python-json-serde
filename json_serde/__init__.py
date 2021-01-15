"""
JSON de/serialization library.
"""

from .serde import (
    Anything,
    Dict,
    JsonSerde,
    String,
    Integer,
    Float,
    Boolean,
    Nested,
    List,
    IsoDateTime,
    Uuid,
    IsoDate,
    SerdeError,
)
from ._utils import Absent

__version__ = "0.0.11"
__author__ = "heartsucker"


__all__ = [
    "Anything",
    "Dict",
    "JsonSerde",
    "String",
    "Integer",
    "Float",
    "Boolean",
    "Nested",
    "List",
    "IsoDateTime",
    "Uuid",
    "IsoDate",
    "SerdeError",
    "Absent",
]
