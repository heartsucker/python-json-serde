"""
JSON de/serialization library.
"""

from .serde import JsonSerde, String, Integer, Float, Boolean, Nested, List, IsoDateTime, Uuid, \
    IsoDate, SerdeError
from ._utils import Absent

__version__ = '0.0.8'
__author__ = 'heartsucker'


__all__ = ['JsonSerde', 'String', 'Integer', 'Float', 'Boolean', 'Nested', 'List', 'IsoDateTime',
           'Uuid', 'IsoDate', 'SerdeError', 'Absent']
