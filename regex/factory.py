from regex.main import Parser, ReleaseObject
from regex.planet import ParserPlanet
from regex.star import ParserStar
from regex.jpop import ParserJpop


def getParser(publisher, obj:ReleaseObject) -> Parser:
    if publisher == 'planet':
        return ParserPlanet(obj)
    if publisher == 'star':
        return ParserStar(obj)
    if publisher == 'jpop':
        return ParserJpop(obj)
    return ParserPlanet(obj)