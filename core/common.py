from abc import abstractmethod

from core.dto import Author, Department, Faculty, Publication


class UniversityLibrary:
    @abstractmethod
    def get_all_faculties(self) -> list[Faculty]:
        pass

    @abstractmethod
    def get_all_departments(self, faculty: Faculty) -> list[Department]:
        pass

    @abstractmethod
    def search_by_author(self, author: Author,
                         department: Department | None=None,
                         publ_year_from: int | None =None,
                         publ_year_to: int | None =None) -> tuple[int, list[Publication]]:
        pass

    @abstractmethod
    def get_author_suggestions(self, query: str) -> list[str]:
        pass
