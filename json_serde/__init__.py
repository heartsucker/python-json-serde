"""
JSON de/serialization library.
"""

from .serde import JsonSerde, String, Integer, Float, Boolean, Nested, List, IsoDateTime

__version__ = '0.0.1'
__author__ = 'heartsucker'


__all__ = ['JsonSerde', 'String', 'Integer', 'Float', 'Boolean', 'Nested', 'List', 'IsoDateTime']
