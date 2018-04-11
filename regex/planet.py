from regex.main import ReleaseObject, Parser
import re


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
