from dataclasses import dataclass
from typing import Optional


@dataclass
class Author:
    primary_name: str

@dataclass
class Publication:
    info: str

@dataclass
class Faculty:
    name: str
    id: int

@dataclass
class Department:
    name: str
    id: int
    faculty: Optional[Faculty]