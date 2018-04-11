from regex import Parser, ReleaseObject
from regex import ParserPlanet
from regex import ParserStar
from regex import ParserJpop


def getParser(publisher, obj:ReleaseObject) -> Parser:
    if publisher == 'planet':
        return ParserPlanet(obj)
    if publisher == 'star':
        return ParserStar(obj)
    if publisher == 'jpop':
        return ParserJpop(obj)
    return ParserPlanet(obj)