import re
import traceback
from datetime import datetime

from passlib.handlers.sha2_crypt import sha256_crypt
from sqlalchemy.exc import IntegrityError

from static.types.enumtypes import Publisher, Status


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


def release_to_dict(release):
    return {'id': release.manga_id,
            'subtitle': release.subtitle,
            'volume': release.volume,
            'release_date': release.release_date,
            'price': release.price,
            'cover': release.cover}


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
        return {'status': 'Error', 'message': 'User not found', 'level': 'danger'}
    else:
        if sha256_crypt.verify(password_p, q.password):
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = q.id
            if q.admin:
                session['admin'] = 1
            return {'status': 'OK', 'message': 'Logged in', 'level': 'success'}
        else:
            return {'status': 'Error', 'message': 'Invalid Passord', 'level': 'danger'}


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
    return [(x.manga_id, x.volume) for x in collection]


def is_volume_in_user_library(user_id, manga_id, volume):
    from flask_app import UserCollection
    return UserCollection.query.filter(UserCollection.user_id == user_id,
                                       UserCollection.manga_id == manga_id,
                                       UserCollection.volume == volume).first()


def get_releases_by_week(_from=None, _to=None, _at=None):
    from flask_app import Releases
    return Releases.query.filter(Releases.bounds(_from=_from, _to=_to, _at=_at)).order_by(Releases.release_date).all()


def get_releases_by_id(manga_id):
    from flask_app import Releases
    return Releases.query.filter(Releases.manga_id == manga_id).order_by(Releases.release_date).all()


def filter_releases_by_user(release_list, user_manga, user_collection):
    return [x for x in release_list if (x.manga_id in user_manga) and ((x.manga_id, x.volume) not in user_collection)]


def get_collection(manga_id):
    from flask_app import Collection
    return Collection.query.filter(Collection.manga_id == manga_id).order_by(Collection.volume).all()


def get_volume(manga_id, volume):
    from flask_app import Collection
    return Collection.query.filter(Collection.manga_id == manga_id, Collection.volume == volume).first()


def insert(db, values):
    try:
        n_r = 0
        n_c = 0
        if 'info' in values:
            title = values['info']['title']
            insert_manga(db, values['info'])
            if 'release' in values:
                n_r = len(values['releases'])
                for release in values['releases']:
                    r = insert_release(db, release)
                    if not r['status'] == 'OK':
                        return r
            if 'collection' in values:
                n_c = len(values['collection'])
                for c in values['collection']:
                    r = insert_collection_item(db, c)
                    if not r['status'] == 'OK':
                        return r
            return {'status': 'OK',
                    'message': '{} added succeffully with {} releases and {} collection item'.format(title, n_r, n_c)}
        else:
            return {'status': 'error',
                    'message': 'data must contain item info'}
    except Exception:
        return {'status': 'error',
                'message': traceback.format_exc()}


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


def insert_release(db, release):
    from flask_app import Releases

    release['volume'] = int(release['volume'])
    release['release_date'] = datetime.strptime(release['release_date'], '%Y-%m-%d')
    release['price'] = float(release['price'])

    r = Releases.query.filter(Releases.manga_id == release['id'],
                              Releases.volume == release['volume'],
                              Releases.release_date == release['release_date']).first()
    if not r:
        r = Releases(release)
        db.session.add(r)
        db.session.commit()
    u = update_collection(db, release)
    if not u['status'] == 'OK':
        return u
    u = update_manga_from_release(db, release)
    if not u['status'] == 'OK':
        return u


def insert_collection_item(db, item):
    from flask_app import Collection
    try:
        item['volume'] = int(item['volume'])
        c = Collection(item)
        db.session.add(c)
        db.session.commit()
        return {'status': 'OK',
                'message': '{id}-{volume} added'.format_map(item)}
    except Exception:
        return {'status': 'Error',
                'source': '{id}-{volume} added'.format_map(item),
                'message': traceback.format_exc()}


def insert_unknown(db, values):
    from flask_app import Unknown
    try:
        values['title'] = values.pop('title_volume', None)
        values['release_date'] = datetime.strptime(values['release_date'], '%Y-%m-%d')
        u = Unknown.query.filter(Unknown.title == values['title'],
                                 Unknown.subtitle == values['subtitle'],
                                 Unknown.release_date == values['release_date']).first()
        if not u:
            u = Unknown(values)
            db.session.add(u)
            db.session.commit()
        return {'status': 'OK',
                'message': '{title} added'.format_map(values)}
    except Exception:
        return {'status': 'Error',
                'source': '{title} added'.format_map(values),
                'message': traceback.format_exc()}


def update_collection(db, values):
    from flask_app import Collection
    try:
        c = Collection.query.filter(Collection.manga_id == values['id'], Collection.volume == values['volume']).first()
        if c:
            c.cover = values['cover']
        else:
            insert_collection_item(db, values)
        db.session.commit()
        return {'status': 'OK',
                'message': '{id}-{volume} added'.format_map(values)}
    except Exception:
        return {'status': 'Error',
                'source': '{id}-{volume}'.format_map(values),
                'message': traceback.format_exc()}


def update_manga_from_release(db, release):
    from flask_app import Manga
    try:
        t = release['release_date'].isocalendar()[:2]
        now = datetime.now().isocalendar()[:2]
        if t <= now:
            m = Manga.query.filter(Manga.id == release['id']).first()
            if m:
                if release['volume'] >= m.released:
                    m.released = release['volume']
                    if release['cover']:
                        m.cover = release['cover']
                if release['volume'] == 1 and m.status == Status.TBA:
                    m.status = Status.Ongoing
                if release['volume'] == m.volumes and m.complete:
                    m.status = Status.Complete
                db.session.commit()
        return {'status': 'OK',
                'message': '{id}-{volume}-{release_date} added'.format_map(release)}
    except Exception:
        return {'status': 'Error',
                'source': '{id}-{volume}-{release_date}'.format_map(release),
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
                'message': 'manga {} updated'.format_map(m.title)}
    except Exception:
        return {'status': 'Error',
                'source': '{}-{}-{}'.format(release.manga.title, release.volume, release.release_date),
                'message': traceback.format_exc()}


def update_manga(db, values):
    from flask_app import Manga
    m = Manga.query.filter(Manga.id == values['id']).first()
    try:
        if m:
            if 'original' in values:
                m.original = values['original']
            if 'genre' in values:
                m.genre = values['genre']
            if 'author' in values:
                m.authors = values['author']
            if 'artist' in values:
                m.artists = values['artist']
            m.volumes = values['volumes']
            m.complete = values['complete']
            db.session.commit()
        return {'status': 'OK',
                'message': '{} updated'.format(m.title)}
    except Exception:
        return {'status': 'Error',
                'source': m.title,
                'message': traceback.format_exc()}
