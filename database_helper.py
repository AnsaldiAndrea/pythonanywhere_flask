import re
import traceback
from datetime import datetime
import time

from passlib.handlers.sha2_crypt import sha256_crypt
from sqlalchemy.exc import IntegrityError

from static.types.enumtypes import Publisher, Status

empty_cover = [
    "no-photo",
    "no_cover",
]


def to_yearweek(date):
    return int(str(date.isocalendar()[0]) + "{:02}".format(date.isocalendar()[1]))


def manga_to_dict(manga):
    return {'id': manga.id,
            'title': manga.title,
            'original': manga.original,
            'volumes': manga.volumes,
            'released': manga.released,
            'publisher': manga.publisher.value,
            'status': manga.status.value,
            'author': manga.authors,
            'artist': manga.artists,
            'genre': manga.genre,
            'complete': manga.complete,
            'cover': manga.cover}


def register_user(db, form):
    from flask_app import Users
    name = form.name.data
    email = form.email.data
    username = form.username.data
    password = str(sha256_crypt.encrypt(form.password.data))

    new_user = Users(name, email, username, password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except IntegrityError:
        return False


def log_in(request, session):
    from flask_app import Users
    username = request.form['username']
    password_p = request.form['password']

    q = Users.query.filter(Users.username == username).first()
    if not q:
        return {'status': 'error', 'message': 'User not found', 'level': 'danger'}
    else:
        if sha256_crypt.verify(password_p, q.password):
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = q.id
            if q.admin:
                session['admin'] = 1
            return {'status': 'OK', 'message': 'Logged in', 'level': 'success'}
        else:
            return {'status': 'error', 'message': 'Invalid Passord', 'level': 'danger'}


def get_ids():
    from flask_app import Manga
    data = Manga.query.with_entities(Manga.id).all()
    return data


def get_manga():
    from flask_app import Manga
    return Manga.query.order_by(Manga.title).all()


def get_manga_by_id(manga_id):
    from flask_app import Manga
    return Manga.query.filter(Manga.id == manga_id).first()


def get_titles_with_alias():
    from flask_app import Manga, Alias
    t = Manga.query.all()
    titles = {(re.sub('[^\w]', '', x.title).lower(), x.publisher): x.id for x in t}
    a = Alias.query.all()
    alias = {(x.title, x.manga.publisher): x.manga_id for x in a}
    return {**titles, **alias}


def get_user_manga(user_id):
    from flask_app import UserManga
    manga_ids = UserManga.query.filter(UserManga.user_id == user_id).distinct()
    return [x.manga_id for x in manga_ids]


def is_user_watching(user_id, manga_id):
    from flask_app import UserManga
    m = UserManga.query.filter(UserManga.user_id == user_id, UserManga.manga_id == manga_id).first()
    return m


def get_user_collection(user_id):
    from flask_app import UserCollection
    collection = UserCollection.query.filter(UserCollection.user_id == user_id).all()
    return [c.collection_id for c in collection]


def is_volume_in_user_library(user_id, collection_id):
    from flask_app import UserCollection
    return UserCollection.query.filter(UserCollection.user_id == user_id,
                                       UserCollection.collection_id == collection_id).first()


def get_release_by_id(release_id):
    from flask_app import Releases
    return Releases.query.filter(Releases.release_id == release_id).first()


def get_releases_by_week(_from=None, _to=None, _at=None):
    from flask_app import Releases
    return Releases.query.filter(Releases.bounds(_from=_from, _to=_to, _at=_at)).order_by(Releases.release_date).all()


def get_releases_by_manga_id(manga_id):
    from flask_app import Releases
    return Releases.query.filter(Releases.manga_id == manga_id).order_by(Releases.release_date).all()


def get_user_releases(user_id, _from=None, _to=None, _at=None):
    from flask_app import Releases, UserCollection, ReleaseMap

    print(time.process_time())
    user_m = get_user_manga(user_id)
    print(time.process_time())
    release_list = Releases.query.filter(Releases.bounds(_from=_from, _to=_to, _at=_at)).order_by(
        Releases.release_date).all()
    print(time.process_time())
    release_list = [r for r in release_list if r.manga_id in user_m]
    print(time.process_time())
    # user_col = UserCollection.query.filter(UserCollection.user_id == user_id).all()

    user_rel = UserCollection.query.join(ReleaseMap, ReleaseMap.collection_id == UserCollection.collection_id) \
        .filter(UserCollection.user_id == user_id).add_columns(ReleaseMap.release_id).all()

    return [r for r in release_list if not any(ur for ur in user_rel if r.release_id == ur.release_id)]

    # print(time.process_time())
    # user_col = [(c.collection.manga_id, c.collection.volume, c.collection.subtitle) for c in user_col]
    # print(time.process_time())
    # result = [r for r in release_list if (r.manga_id, r.volume, r.subtitle) not in user_col]
    # print(time.process_time())
    # return result


def filter_releases_by_user(release_list, user_manga, user_collection):
    return [x for x in release_list if
            (x.manga_id in user_manga) and ((x.manga_id, x.volume, x.subtitle) not in user_collection)]


def get_collection(manga_id):
    from flask_app import Collection
    return Collection.query.filter(Collection.manga_id == manga_id).order_by(Collection.volume,
                                                                             Collection.subtitle).all()


def get_volume(collection_id):
    from flask_app import Collection
    return Collection.query.filter(Collection.collection_id == collection_id).first()


def get_volume_from(manga_id, volume, subtitle):
    from flask_app import Collection
    return Collection.query.filter(Collection.manga_id == manga_id,
                                   Collection.volume == volume,
                                   Collection.subtitle == subtitle).first()


def insert_manga(db, _manga):
    try:
        _manga['volumes'] = int(_manga['volumes'])
        _manga['released'] = int(_manga['released'])
        _manga['publisher'] = Publisher.get_Publisher(_manga['publisher'])
        _manga['status'] = Status.get_Status(_manga['status'])
        _manga['author'] = ','.join(_manga['author'])
        _manga['artist'] = ','.join(_manga['artist'])
        _manga['genre'] = ','.join(_manga['genre'])

        from flask_app import Manga
        m = Manga.query.filter(Manga.id == _manga['id']).first()
        if not m:
            m = Manga(_manga)
            db.session.add(m)
            db.session.commit()
        return {'status': 'OK', 'message': '{} added'.format(_manga['title'])}
    except Exception:
        return {'status': 'error',
                'message': traceback.format_exc()}


def insert_alias(db, manga_id, alias):
    from flask_app import Alias
    a = Alias.query.filter(Alias.manga_id == manga_id, Alias.title == alias).first()
    if not a:
        try:
            a = Alias(manga_id, alias)
            db.session.add(a)
            db.session.commit()
            return {'status': 'OK', 'message': 'alias added'}
        except Exception:
            return {'status': 'error', 'message': traceback.format_exc()}
    return {'status': 'OK', 'message': 'alias already present'}


def insert_release(db, obj):
    from flask_app import Releases
    from release_parser import ReleaseObject

    release = ReleaseObject(obj)
    r = Releases.query.filter(Releases.manga_id == release.id,
                              Releases.volume == release.volume,
                              Releases.release_date == release.release_date_as_datetime()).first()
    if not r:
        r = Releases(release.as_dict())
        db.session.add(r)
        db.session.commit()
    else:
        r.cover = release.cover
    u = update_collection(db, release)
    if not u['status'] == 'OK':
        return u
    u = update_manga_from_release(db, release)
    return u


def insert_collection(db, release):
    from flask_app import Collection
    try:
        c = Collection(release.as_dict())
        db.session.add(c)
        db.session.commit()
        return {'status': 'OK',
                'message': '{id}-{volume} added'.format_map(release.as_dict())}
    except Exception:
        return {'status': 'error',
                'source': '{id}-{volume} added'.format_map(release.as_dict()),
                'message': traceback.format_exc()}


def update_collection(db, release):
    from flask_app import Collection
    try:
        c = Collection.query.filter(Collection.manga_id == release.id, Collection.volume == release.volume,
                                    Collection.subtitle == release.subtitle).first()
        if c:
            if is_cover_null(c.cover):
                c.cover = release.cover
        else:
            insert_collection(db, release)
        db.session.commit()
        return {'status': 'OK',
                'message': '{id}-{volume} added'.format_map(release.as_dict())}
    except Exception:
        return {'status': 'error',
                'source': '{id}-{volume}'.format_map(release.as_dict()),
                'message': traceback.format_exc()}


def update_manga_from_release(db, release):
    from flask_app import Manga
    try:
        t = release.release_date_as_datetime().isocalendar()[:2]
        now = datetime.now().isocalendar()[:2]
        if t <= now:
            m = Manga.query.filter(Manga.id == release.id).first()
            if m:
                if release.volume >= m.released:
                    m.released = release.volume
                    if release.cover:
                        m.cover = release.cover
                if release.volume == 1 and m.status == Status.TBA:
                    m.status = Status.Ongoing
                if release.volume == m.volumes and m.complete:
                    m.status = Status.Complete
                db.session.commit()
        return {'status': 'OK',
                'message': '{id}-{volume}-{release_date} added'.format_map(release.as_dict())}
    except Exception:
        return {'status': 'error',
                'source': '{id}-{volume}-{release_date}'.format_map(release.as_dict()),
                'message': traceback.format_exc()}


def update_manga_from_db(db, release):
    try:
        m = release.manga
        t = release.yearweek
        now = int(str(datetime.now().isocalendar()[0]) + "{:02}".format(datetime.now().isocalendar()[1]))
        if t <= now:
            if release.volume >= m.released:
                m.released = release.volume
                if release.volume:
                    m.cover = release.cover
            if release.volume == 1 and m.status == Status.TBA:
                m.status = Status.Ongoing
            if release.volume == m.volumes and m.complete:
                m.status = Status.Complete
            db.session.commit()
        return {'status': 'OK',
                'message': 'manga {} updated'.format(m.title)}
    except Exception:
        return {'status': 'error',
                'source': '{}-{}-{}'.format(release.manga.title, release.volume, release.release_date),
                'message': traceback.format_exc()}


def update_manga(db, value):
    from flask_app import Manga
    from static.types.manga_object import MangaObject
    obj = MangaObject(value)
    m = Manga.query.filter(Manga.id == obj.manga_id).first()
    try:
        if m:
            if obj.original:
                m.original = obj.original
            if obj.genre:
                m.genre = obj.genre
            if obj.author:
                m.authors = obj.author
            if obj.artist:
                m.artists = obj.artist
            if obj.volumes > m.volumes:
                m.volumes = obj.volumes
            m.complete = obj.complete
            db.session.commit()
        return {'status': 'OK',
                'message': '{} updated'.format(m.title)}
    except Exception:
        return {'status': 'error',
                'source': m.title,
                'message': traceback.format_exc()}


def is_cover_null(cover):
    if not cover: return True
    for e in empty_cover:
        if e in cover:
            return True
    return False
