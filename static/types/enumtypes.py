from enum import Enum


class Publisher(Enum):
    PlanetManga = 'Planet Manga'
    StarComics = 'StarComics'
    JPOP = 'J-POP'
    GOEN = 'GOEN'

    @staticmethod
    def get_Publisher(value):
        simple_publisher = {'planet': Publisher.PlanetManga,
                            'star': Publisher.StarComics,
                            'jpop': Publisher.JPOP,
                            'goen': Publisher.GOEN}
        if value in simple_publisher:
            return simple_publisher[value]
        return None


class Status(Enum):
    Ongoing = 'Ongoing'
    Complete = 'Complete'
    TBA = 'TBA'

    @staticmethod
    def get_Status(value):
        simple_status = {'ongoing': Status.Ongoing,
                         'complete': Status.Complete,
                         'tba': Status.TBA}
        if value in simple_status:
            return simple_status[value]
        return None
