from datetime import datetime
from static.types.enumtypes import Publisher, Status
import traceback
import re


def get_titles_with_alias():
    from flask_app import Manga, Alias
    t = Manga.query.all()
    titles = {re.sub('[^\w]', '', x.title).lower(): x.id for x in t}
    a = Alias.query.all()
    alias = {x.title: x.manga_id for x in a}
    return {**titles, **alias}


def insert(db, values):
    try:
        n_r = 0
        n_c = 0
        if 'info' in values:
            title = values['info']['title']
            insert_manga(db, values['info'])
            if 'release' in values:
                n_r = len(values['releases'])
                for r in values['releases']:
                    insert_release(db, r)
            if 'collection' in values:
                n_c = len(values['collection'])
                for c in values['collection']:
                    insert_collection_item(db, c)
            return {'status': 'OK',
                    'message': '{} added succeffully with {} releases and {} collection item'.format(title, n_r, n_c)}
        else:
            return {'status': 'error',
                    'message': 'data must contain item info'}
    except Exception:
        return {'status': 'error',
                'message': traceback.format_exc()}


def insert_manga(db, _manga):
    _manga['volumes'] = int(_manga['volumes'])
    _manga['released'] = int(_manga['released'])
    _manga['publisher'] = Publisher(_manga['publisher'])
    _manga['status'] = Status(_manga['status'])
    _manga['author'] = ','.join(_manga['author'])
    _manga['artist'] = ','.join(_manga['artist'])
    _manga['genre'] = ','.join(_manga['genre'])

    from flask_app import Manga
    m = Manga.query.filter(Manga.id == _manga['id']).first()
    if not m:
        m = Manga(_manga)
        db.session.add(m)
        db.session.commit()


def insert_alias(db, manga_id, alias):
    from flask_app import Alias
    a = Alias.query.filter(Alias.manga_id == manga_id, Alias.title == alias).first()
    if not a:
        a = Alias(manga_id, alias)
        db.session.add(a)
        db.session.commit()


def insert_release(db, release):
    from flask_app import Releases
    with open("api.log", "w") as p:
        if release:
            p.write(release['id'])
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
    update_collection(db, release)
    update_manga(db, release)


def insert_collection_item(db, item):
    from flask_app import Collection
    item['volume'] = int(item['volume'])
    c = Collection(item)
    db.session.add(c)
    db.session.commit()


def insert_unknown(db, values):
    from flask_app import Unknown
    values['title'] = values.pop('title_volume', None)
    values['release_date'] = datetime.strptime(values['release_date'], '%Y-%m-%d')
    u = Unknown.query.filter(Unknown.title == values['title'],
                             Unknown.subtitle == values['subtitle'],
                             Unknown.release_date == values['release_date']).first()
    if not u:
        u = Unknown(values)
        db.session.add(u)
        db.session.commit()


def update_collection(db, values):
    from flask_app import Collection
    c = Collection.query.filter(Collection.manga_id == values['id'], Collection.volume == values['volume']).first()
    if c:
        c.cover = values['cover']
    else:
        insert_collection_item(db, values)
    db.session.commit()


def update_manga(db, values):
    from flask_app import Manga
    t = values['release_date'].isocalendar()[:2]
    now = datetime.now().isocalendar()[:2]
    if t <= now:
        m = Manga.query.filter(Manga.id == values['id']).first()
        if m:
            if values['volume'] > m.released:
                m.released = values['volume']
                if values['cover']:
                    m.cover = values['cover']
            if values['volume'] == 1 and m.status == Status.TBA:
                m.status = Status.Ongoing
            if values['volume'] == m.volumes and m.complete:
                m.status = Status.Complete
            db.session.commit()
