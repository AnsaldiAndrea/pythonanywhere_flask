from database_helper import get_titles_with_alias
from static.types.enumtypes import Publisher
from regex import release_object
import re

publisher_map = {"planet": Publisher.PlanetManga, "star": Publisher.StarComics, "jpop": Publisher.JPOP}


def identify(obj: release_object.ReleaseObject):
    obj.parse()
    titles = get_titles_with_alias()
    title = obj.title
    if "MANGA" in obj.extra:
        title += " MANGA"
    elif "LIGHT NOVEL" in obj.extra:
        title += " LIGHT NOVEL"
    return titles.get((normal(obj.title), publisher_map[obj.publisher]), None)


def normal(title: str):
    return re.sub("[^\\w]", "", title).lower()