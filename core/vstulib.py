import logging
import re

from bs4.element import NavigableString

from core.common import UniversityLibrary
from core.dto import Author, Department, Faculty, Publication
from core.request import get, get_json, innerHTML, post, soupify

logger = logging.getLogger("core")

ORDER_NUMBER_REGEX = re.compile(r"^(\d+).\s{0,}")
EMPTY_VALUES = re.compile(r"^\s{0,}\(\s{0,}-?\s{0,}\)(\s{0,}-?)+$")


class VSTULibrary(UniversityLibrary):
    def _extract_index_information(self):
        logger.debug("Extracting information from main library search page")
        status, text = get(
            "http://library.vstu.ru/publ_2/index.php", {"command": "search2"}
        )
        universities = []
        faculties = []
        if status == 200:
            soup = soupify(text)
            uni = soup.select_one("select#universitet")
            fac = soup.select_one("select#faculty")
            for univ_record in (uni.children if uni else []):
                if isinstance(univ_record, NavigableString):
                    continue
                id = int(univ_record["value"]) # type: ignore
                if id == 0:
                    continue
                name = univ_record.text
                universities.append((id, name))
            for fac_record in fac.children: # type: ignore
                if isinstance(fac_record, NavigableString):
                    continue
                id = int(fac_record["value"]) # type: ignore
                if id == 0 or id == 11 or EMPTY_VALUES.match(fac_record.text):
                    continue
                name = fac_record.text
                faculties.append(Faculty(name, id))
        else:
            logger.error(
                f"Запрос в библиотеку (получение общей информации) не удался, код {status}, содержимое: {text}"
            )
        return universities, faculties

    def get_all_faculties(self) -> list[Faculty]:
        return self._extract_index_information()[1]

    def get_all_departments(self, faculty: Faculty) -> list[Department]:
        fac_id = faculty.id
        result = []
        status, json_text = get_json(
            "http://library.vstu.ru/publ_2/search_kaf.php", {"faculty_id": fac_id}
        )
        if status == 200:
            for entry in json_text:
                if int(entry["id"]) != 0 and not EMPTY_VALUES.match(entry["title"]):
                    result.append(Department(entry["title"], entry["id"], faculty))
        else:
            logger.error(
                f"Запрос в библиотеку (получение кафедр {faculty.name}) не удался, код {status}, содержимое: {json_text}"
            )
        return result

    def search_by_author(
        self,
        author: Author,
        department: Department | None = None,
        publ_year_from: int | None = None,
        publ_year_to: int | None = None,
    ) -> tuple[int, list[Publication]]:
        data = {
            "universitet": "1",
            "fio": author.primary_name,
            "year_rel": "",
            "year_rel1": publ_year_from or "",
            "year_rel2": publ_year_to or "",
            "year_reg": "",
            "year_reg1": "",
            "year_reg2": "",
            "faculty": department.faculty.id if department else 0, # type: ignore
            "kafedra": department.id if department else 0,
            "v_publ": "0",
        }
        logger.debug(f"Поиск по запросу в библиотеке: {author.primary_name}")
        status, text = post("http://library.vstu.ru/publ_2/publ_result.php", data, {})
        publications = []
        if status == 200:
            soup = soupify(text)
            resultlist = soup.select_one(".resultlist#LIST").children # type: ignore
            for publication in resultlist:
                if isinstance(publication, NavigableString):
                    continue
                text = innerHTML(publication)
                text = re.sub(ORDER_NUMBER_REGEX, "", text)
                publications.append(Publication(text))
        else:
            logger.error(
                f"Запрос в библиотеку (поиск публикаций {author.primary_name}) не удался, код {status}, содержимое: {text}"
            )
        return status, publications

    def get_author_suggestions(self, query: str) -> list[str]:
        if query is None:
            query = ""
        status, json_text = get_json(
            "http://library.vstu.ru/publ_2/search_fio.php", {"term": query}
        )
        if status == 200:
            return list(json_text)
        else:
            logger.warning(
                f"Запрос подсказок к имени не удался, код {status}, запрос: {query}"
            )
            return []
