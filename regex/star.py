from regex.main import ReleaseObject, Parser
import re


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
