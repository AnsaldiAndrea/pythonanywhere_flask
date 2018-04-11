from regex import release_object
from regex import parser
from regex import star
from regex import planet
from regex import jpop


def get_parser(publisher, obj:release_object.ReleaseObject) -> parser.Parser:
    if publisher == 'planet':
        return planet.ParserPlanet(obj)
    if publisher == 'star':
        return star.ParserStar(obj)
    if publisher == 'jpop':
        return jpop.ParserJpop(obj)
    return planet.ParserPlanet(obj)