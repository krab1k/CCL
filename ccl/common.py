import os
from enum import Enum
from typing import Set


class NoValEnum(Enum):
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self.name}'

    def __str__(self) -> str:
        return f'{self.value}'


ELEMENT_NAMES: Set[str] = set()
with open(os.path.join('ccl', 'elements.txt')) as elements_file:
    for line in elements_file:
        ELEMENT_NAMES.add(line.strip().lower())
