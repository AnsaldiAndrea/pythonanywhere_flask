import re
from static.types.enumtypes import Publisher
from database_helper import get_titles_with_alias, get_manga_by_id
import logging
from datetime import datetime


logging.basicConfig(filename='parser_test.log', level=logging.INFO)

class ReleaseObject:
    def __init__(self, obj=None):
        self.value = {"id": "",
                      "title": None,
                      "volume": 0,
                      "extra": [],
                      "subtitle": "",
                      "publisher": "",
                      "release_date": None,
                      "price": 0, "cover": None}
        if obj:
            self.load(obj)

    def get_id(self):
        return self.value['id']

    def set_id(self, id: str):
        self.value['id'] = id

    def get_title(self):
        return self.value["title"]

    def set_title(self, title):
        self.value["title"] = title

    def get_volume(self):
        return self.value["volume"]

    def set_volume(self, volume):
        self.value["volume"] = volume

    def get_extra(self):
        return self.value["extra"]

    def get_subtitle(self):
        return self.value['subtitle']

    def set_subtitle(self, subtitle):
        self.value["subtitle"] = subtitle

    def set_extra(self, extra):
        self.value["extra"].append(extra)

    def get_publisher(self):
        return self.value['publisher']

    def set_publisher(self, publisher):
        self.value['publisher'] = publisher

    def get_release_date(self):
        return self.value['release_date']

    def set_release_date(self, release_date):
        self.value['release_date'] = release_date

    def release_date_as_datetime(self):
        return datetime.strptime(self.value["release_date"],"%Y-%m-%d")

    def get_price(self):
        return self.value['price']

    def set_price(self, price):
        self.value['price'] = price

    def get_cover(self):
        return self.value['cover']

    def set_cover(self, cover):
        self.value['cover'] = cover

    def __str__(self):
        return str(self.value)

    def as_dict(self):
        return self.value

    def clear(self):
        self.value.clear()

    def load(self, dictonary: dict):
        logging.info(dictonary)
        self.title = dictonary.get("title_volume", "")
        self.subtitle = dictonary.get("subtitle", "")
        self.publisher = dictonary.get("publisher", "planet")
        self.release_date = dictonary.get("release_date", "1900-01-01")
        self.price = dictonary.get("price", 0)
        self.cover = dictonary.get("cover", None)

    def parse(self):
        # logging.info(self)
        parser = get_parser(self.publisher, self)
        parser.regex()
        # logging.info(self)
        _id = identify(self)
        if not _id:
            self.clear()
            self.id = "unknown"
            return
        self.id = _id
        self.title = get_manga_by_id(_id).title
        if "BOX" in self.extra:
            if self.subtitle:
                self.subtitle += " - BOX"
            else:
                self.subtitle = "BOX"
        self.value.pop("extra")

    id = property(get_id, set_id)
    title = property(get_title, set_title)
    volume = property(get_volume, set_volume)
    extra = property(get_extra, set_extra)
    subtitle = property(get_subtitle, set_subtitle)
    publisher = property(get_publisher, set_publisher)
    release_date = property(get_release_date, set_release_date)
    price = property(get_price, set_price)
    cover = property(get_cover, set_cover)


class Parser:
    def __init__(self, obj: ReleaseObject):
        self.obj = obj

    def regex(self):
        pass

    @staticmethod
    def filter_none(tuples):
        return tuple(x for x in tuples if x is not None)


class ParserJpop(Parser):
    re_box = "(.*)\\sbox\\s[(]\\d+-\\d+[)]|(.*)\\s[(]box\\s\\d+-\\d+[)]|(.*)\\sbox"
    re_manga = "(.*)\\s-\\sil manga(\\s.*)?|(.*)\\sil manga(\\s.*)?"
    re_volume = "(.*)\\s(\\d+)(?:\\s[(]di\\s\\d+[)])?|" \
                "(.*)\\s(\\d+)\\s(?:[(]([A-Za-z\\s]*)[)])?|" \
                "(.*)\\s(\\d+)\\s-\\s([A-Za-z\\s]*)\\s(?:[(][A-Za-z\\s]*[)])|" \
                "(.*)\\s(?:[(]([A-Za-z\\s]*)[)])?|" \
                "(.*)"

    def __init__(self, obj):
        super().__init__(obj)

    def regex(self):
        print(self.obj.title)
        title = self.obj.title
        title = self.regex_box(title)
        title = self.regex_manga(title)
        if 'BOX' not in self.obj.extra:
            self.regex_volume(title)
        print(self.obj.title)

    def regex_box(self, title):
        title = title.strip()
        r = re.fullmatch(self.re_box, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            self.obj.title = groups[0].strip()
            self.obj.extra = "BOX"
            return self.obj.title
        return title.strip()

    def regex_volume(self, title):
        title = title.strip()
        r = re.fullmatch(self.re_volume, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            if len(groups) == 2:
                self.obj.title = groups[0]
                if groups[1].isdigit():
                    self.obj.volume = int(groups[1])
                elif 'light novel' in groups[1].lower():
                    self.obj.volume = 1
                    self.obj.extra = 'LIGHT NOVEL'
            elif len(groups) == 3:
                self.obj.title = groups[0]
                self.obj.volume = int(groups[1])
                if 'light novel' in groups[2].lower():
                    self.obj.extra = 'LIGHT NOVEL'
                elif 'ultimo' not in groups[2].lower():
                    self.obj.title = "{} - {}".format(groups[0], groups[2])
            else:
                self.obj.title = groups[0]
                self.obj.volume = 1

    def regex_manga(self, title):
        r = re.fullmatch(self.re_manga, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            if len(groups) > 1:
                g = re.sub("\\s+", " ", groups[0] + groups[1])
            else:
                g = groups[0]
            self.obj.title = g.strip()
            self.obj.extra = "MANGA"
            return self.obj.title
        return title.strip()


class ParserPlanet(Parser):
    re_volume = "(.*)\\s([^0]\\d*)|(.*)"
    re_box = "(.*)\\s-\\spack|cofanetto\\s(.*)"

    def __init__(self, obj):
        super().__init__(obj)
        self.fix_title()

    def fix_title(self):
        self.obj.title = self.obj.title.replace('–', '-')

    def regex(self):
        title = self.obj.title
        print(title)
        self.regex_box(title)
        if 'BOX' not in self.obj.extra:
            self.regex_volume(title)
        print(self.obj)
        return self.obj

    def regex_box(self, title):
        r = re.fullmatch(self.re_box, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            self.obj.title = groups[0]
            self.obj.volume = 0
            self.obj.extra = 'BOX'

    def regex_volume(self, title):
        r = re.fullmatch(self.re_volume, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            self.obj.title = groups[0]
            if len(groups) > 1:
                self.obj.volume = int(groups[1])
            else:
                self.obj.volume = 1


class ParserStar(Parser):
    re_volume = "(.*)\\sn\\.\\s([^0]\\d*)"
    re_unique = "(.*)\\svolume\\sunico"

    def __init__(self, obj):
        super().__init__(obj)

    def regex(self):
        title = self.obj.title
        print(title)
        if not self.regex_unique(title):
            self.regex_volume(title)
        print(self.obj)
        return self.obj

    def regex_unique(self, title):
        r = re.fullmatch(self.re_unique, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            self.obj.title = groups[0]
            self.obj.volume = 1
            return True
        return False

    def regex_volume(self, title):
        r = re.fullmatch(self.re_volume, title, re.IGNORECASE)
        if r:
            groups = self.filter_none(r.groups())
            self.obj.title = groups[0]
            self.obj.volume = int(groups[1])


def get_parser(publisher, obj: ReleaseObject) -> Parser:
    if publisher == 'planet':
        return ParserPlanet(obj)
    if publisher == 'star':
        return ParserStar(obj)
    if publisher == 'jpop':
        return ParserJpop(obj)
    return ParserPlanet(obj)


publisher_map = {"planet": Publisher.PlanetManga, "star": Publisher.StarComics, "jpop": Publisher.JPOP}


def identify(obj: ReleaseObject):
    titles = get_titles_with_alias()
    title = obj.title
    if "MANGA" in obj.extra:
        title += " MANGA"
    elif "LIGHT NOVEL" in obj.extra:
        title += " LIGHT NOVEL"
    return titles.get((normal(obj.title), publisher_map[obj.publisher]), None)


def normal(title: str):
    return re.sub("[^\\w]", "", title).lower()
