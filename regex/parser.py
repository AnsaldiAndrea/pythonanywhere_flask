from regex import release_object

class Parser:
    def __init__(self, obj: release_object.ReleaseObject):
        self.obj = obj

    def regex(self):
        pass

    @staticmethod
    def filter_none(tuples):
        return tuple(x for x in tuples if x is not None)