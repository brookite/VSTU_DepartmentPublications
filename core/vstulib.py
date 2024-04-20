from typing import List, Union

from bs4 import NavigableString

from core.common import UniversityLibrary
from core.dto import Publication, Department, Faculty, Author
from core.request import *


class VSTULibrary(UniversityLibrary):
    def _extract_index_information(self):
        status, text = get("http://library.vstu.ru/publ_2/index.php", {"command": "search2"})
        universities = []
        faculties = []
        if status == 200:
            soup = soupify(text)
            uni = soup.select_one("select#universitet")
            fac = soup.select_one("select#faculty")
            for univ_record in uni.children:
                if isinstance(univ_record, NavigableString):
                    continue
                id = int(univ_record["value"])
                if id == 0:
                    continue
                name = univ_record.text
                universities.append((id, name))
            for fac_record in fac.children:
                if isinstance(fac_record, NavigableString):
                    continue
                id = int(fac_record["value"])
                if id == 0 or id == 11:
                    continue
                name = fac_record.text
                faculties.append(Faculty(name, id))
        return universities, faculties

    def get_all_faculties(self) -> List[Faculty]:
        return self._extract_index_information()[1]

    def get_all_departments(self, faculty: Faculty) -> List[Department]:
        fac_id = faculty.id
        result = []
        status, json_text = get_json("http://library.vstu.ru/publ_2/search_kaf.php", {"faculty_id": fac_id})
        if status == 200:
            for entry in json_text:
                result.append(Department(entry["title"], entry["id"], faculty))
        return result

    def search_by_author(self, author: Author, department: Department=None, publ_year_from: int = None, publ_year_to: int = None) -> Union[int, List[Publication]]:
        data = {
            "universitet": "1",
            "fio": author.primary_name,
            "year_rel": "",
            "year_rel1": publ_year_from if publ_year_from else "",
            "year_rel2": publ_year_to if publ_year_to else "",
            "year_reg": "",
            "year_reg1": "",
            "year_reg2": "",
            "faculty": department.faculty.id if department else 0,
            "kafedra": department.id if department else 0,
            "v_publ": "0"
        }
        status, text = post("http://library.vstu.ru/publ_2/publ_result.php", data, {})
        publications = []
        if status == 200:
            soup = soupify(text)
            resultlist = soup.select_one(".resultlist#LIST").children
            for publication in resultlist:
                if isinstance(publication, NavigableString):
                    continue
                publications.append(Publication(innerHTML(publication)))
        return status, publications

    def get_author_suggestions(self, query: str) -> List[str]:
        if query is None:
            query = ""
        status, json_text = get_json("http://library.vstu.ru/publ_2/search_fio.php", {"term": query})
        if status == 200:
            return list(map(Author, json_text))
        else:
            return []


lib = VSTULibrary()
print(lib.search_by_author(Author("Шашков Д.А.")))