from abc import abstractmethod
from typing import List, Dict

from core.dto import Author, Publication, Department, Faculty


class UniversityLibrary:
    @abstractmethod
    def get_all_faculties(self) -> List[Faculty]:
        pass

    @abstractmethod
    def get_all_departments(self, faculty: Faculty) -> List[Department]:
        pass

    @abstractmethod
    def search_by_author(self, author: Author, department: Department=None, publ_year_from=None, publ_year_to=None) -> List[Publication]:
        pass

    @abstractmethod
    def get_author_suggestions(self, query: str) -> List[Author]:
        pass