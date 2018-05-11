class MangaObject:
    def __init__(self, obj=None):
        self.info = {"id": "", "title":"", "original": "", "publisher": "planet", "status": "tba", "volumes": 0,
                     "released": 0, "author": [], "artist": [],
                     "cover": "", "genre": [], "complete": False}
        if obj:
            self.manga_id = obj['id']
            self.title = obj.get('title', '')
            self.original = obj.get('original', '')
            self.publisher = obj.get('publisher', 'planet')
            self.status = obj.get("status", "tba")
            self.volumes = obj['volumes']
            self.released = obj.get('released', 0)
            self.author = ','.join(obj.get('author', ''))
            self.artist = ','.join(obj.get('artist', ''))
            self.genre = ','.join(obj.get('genre', ''))
            self.cover = obj.get('cover', '')
            self.complete = obj['complete']

    def get_id(self):
        return self.info['id']

    def set_id(self, id):
        self.info['id'] = id

    def get_title(self):
        return self.info['title']

    def set_title(self, title):
        self.info['title'] = title

    def get_original(self):
        return self.info['original']

    def set_original(self, original):
        self.info['original'] = original

    def get_publisher(self):
        return self.info['publisher']

    def set_publisher(self, publisher):
        self.info['publisher'] = publisher

    def get_status(self):
        return self.info['status']

    def set_status(self, status):
        self.info['status'] = status

    def get_volumes(self):
        return self.info['volumes']

    def set_volumes(self, volumes):
        self.info['volumes'] = volumes

    def get_released(self):
        return self.info['released']

    def set_released(self, released):
        self.info['released'] = released

    def get_author(self):
        return self.info['author']

    def set_author(self, author):
        self.info['author'] = author

    def get_artist(self):
        return self.info['artist']

    def set_artist(self, artist):
        self.info['artist'] = artist

    def get_cover(self):
        return self.info['cover']

    def set_cover(self, cover):
        self.info['cover'] = cover

    def get_genre(self):
        return self.info['genre']

    def set_genre(self, genre):
        self.info['genre'] = genre

    def get_complete(self):
        return self.info['complete']

    def set_complete(self, complete):
        self.info['complete'] = complete

    def as_dict(self):
        return self.info

    manga_id = property(get_id, set_id)
    title = property(get_title, set_title)
    original = property(get_original, set_original)
    status = property(get_status, set_status)
    publisher = property(get_publisher, set_publisher)
    volumes = property(get_volumes, set_volumes)
    released = property(get_released, set_released)
    author = property(get_author, set_author)
    artist = property(get_artist, set_artist)
    cover = property(get_cover, set_cover)
    genre = property(get_genre, set_genre)
    complete = property(get_complete, set_complete)
