from enum import Enum

class Publisher(Enum):
    PlanetManga = 'Planet Manga'
    StarComics = 'StarComics'
    JPOP = 'J-POP'
    GOEN = 'GOEN'

class Status(Enum):
    Ongoing = 'Ongoing'
    Complete = 'Complete'
    TBA = 'TBA'