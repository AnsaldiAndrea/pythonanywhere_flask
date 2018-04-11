from regex import getParser
from regex import identify

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
        self.value["subtitle"].append(subtitle)

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

    def clear(self):
        self.value.clear()

    def load(self, dictonary: dict):
        self.title = dictonary.get("title_volume", "")
        self.subtitle = dictonary.get("subtitle", "")
        self.publisher = dictonary.get("publisher", "planet")
        self.release_date = dictonary.get("release_date", "1900-01-01")
        self.price = dictonary.get("price", 0)
        self.cover = dictonary.get("cover", None)

    def parse(self):
        parser = getParser(self.publisher, self)
        parser.regex()
        _id = identify(self)
        if id:
            self.clear()
            self.id = "unknown"
            return
        self.id = _id
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
