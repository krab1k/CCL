"""Common utility functions used within CCL"""

import os
from enum import Enum
from typing import Set


class NoValEnum(Enum):
    """Enum with simplified text representation"""
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self.name}'

    def __str__(self) -> str:
        return f'{self.value}'


ELEMENT_NAMES: Set[str] = set()
with open(os.path.join(os.path.dirname(__file__), 'elements.txt')) as elements_file:
    for line in elements_file:
        ELEMENT_NAMES.add(line.strip().lower())
