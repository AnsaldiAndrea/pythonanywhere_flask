import re
from regex.main import ReleaseObject
from regex.main import Parser


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
