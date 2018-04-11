from regex import main
from regex import star
from regex import planet
from regex import jpop


def getParser(publisher, obj:main.ReleaseObject) -> main.Parser:
    if publisher == 'planet':
        return planet.ParserPlanet(obj)
    if publisher == 'star':
        return star.ParserStar(obj)
    if publisher == 'jpop':
        return jpop.ParserJpop(obj)
    return planet.ParserPlanet(obj)