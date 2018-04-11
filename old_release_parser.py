import re
import traceback

import database_helper as db_helper
from static.types.enumtypes import Publisher


class ReleaseParser:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def parse_single(data):
        titles = db_helper.get_titles_with_alias()
        try:
            pub = data['publisher']
            if pub == 'planet':
                return _regex_planet(data, titles)
            if pub == 'star':
                return _regex_star(data, titles)
            if pub == 'jpop':
                return _regex_jpop(data, titles)
            return {}
        except Exception:
            return {"status": "error", "message": traceback.format_exc()}

    def _parse(self, data):
        titles = db_helper.get_titles_with_alias()
        to_correct = []
        for x in data:
            try:
                pub = x['publisher']
                if pub == 'planet':
                    r = _regex_planet(x, titles)
                elif pub == 'star':
                    r = _regex_star(x, titles)
                elif pub == 'jpop':
                    r = _regex_jpop(x, titles)
                    if not r.id == "unknown":
                        to_correct.append(r)
                        continue
                if r.id == "unknown":
                    db_helper.insert_unknown(self.db, x)
                else:
                    db_helper.insert_release(self.db, r)
                continue
            except Exception:
                return {"status": "Error", "sorce": x, "message": traceback.format_exc()}
        self.insert_jpop(to_correct)
        return {"status": "OK", "message": "parsing successful"}

    def parse(self, data):
        titles = db_helper.get_titles_with_alias()
        to_correct = []
        for x in data:
            try:
                pub = x['publisher']
                if pub == 'planet':
                    regex_planet(self.db, x, titles)
                    continue
                if pub == 'star':
                    regex_star(self.db, x, titles)
                    continue
                if pub == 'jpop':
                    regex_jpop(self.db, x, titles, to_correct)
                    continue
            except Exception:
                return {"status": "Error", "sorce": x, "message": traceback.format_exc()}
        self.insert_jpop(to_correct)
        return {"status": "OK", "message": "parsing successful"}

    def insert_jpop(self, to_correct):
        for x in correct_jpop(to_correct):
            db_helper.insert_release(self.db, x)


def _regex_planet(values, titles):
    match = re.fullmatch('((.*)\\s(\\d+))', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, Publisher.PlanetManga, titles)
        if manga_id:
            return fix(manga_id, volume, values)
        else:
            return {"id": "unknown"}
    else:
        manga_id = check_title(values['title_volume'], Publisher.PlanetManga, titles)
        if manga_id:
            return fix(manga_id, 1, values)
        else:
            return {"id": "unknown"}


@DeprecationWarning
def regex_planet(db, values, titles):
    match = re.fullmatch('((.*)\\s(\\d+))', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, Publisher.PlanetManga, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, volume, values))
        else:
            db_helper.insert_unknown(db, values)
    else:
        manga_id = check_title(values['title_volume'], Publisher.PlanetManga, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, 1, values))
        else:
            db_helper.insert_unknown(db, values)


def _regex_star(values, titles):
    match = re.fullmatch('((.*)\\sn\\.\\s(\\d+))|((.*)\\svolume\\sunico)', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, Publisher.StarComics, titles)
        if manga_id:
            return fix(manga_id, volume, values)
        else:
            return {"id": "unknown"}
    elif match and match.group(4):
        title = match.group(5)
        manga_id = check_title(title, Publisher.StarComics, titles)
        if manga_id:
            return fix(manga_id, 1, values)
        else:
            return {"id": "unknown"}
    else:
        return {"id": "unknown"}


@DeprecationWarning
def regex_star(db, values, titles):
    match = re.fullmatch('((.*)\\sn\\.\\s(\\d+))|((.*)\\svolume\\sunico)', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, Publisher.StarComics, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, volume, values))
        else:
            db_helper.insert_unknown(db, values)
    elif match and match.group(4):
        title = match.group(5)
        manga_id = check_title(title, Publisher.StarComics, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, 1, values))
        else:
            db_helper.insert_unknown(db, values)
    else:
        db_helper.insert_unknown(db, values)


def _regex_jpop(values, titles):
    match = re.fullmatch('((.*)\\s(\\d+))', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, Publisher.JPOP, titles)
        if manga_id:
            return fix(manga_id, volume, values)
        else:
            return {"id": "unknown"}
    else:
        manga_id = check_title(values['title_volume'], Publisher.JPOP, titles)
        if manga_id:
            return fix(manga_id, 1, values)
        else:
            return {"id": "unknown"}


@DeprecationWarning
def regex_jpop(db, values, titles, to_correct):
    match = re.fullmatch('((.*)\\s(\\d+))', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, Publisher.JPOP, titles)
        if manga_id:
            to_correct.append(fix(manga_id, volume, values))
        else:
            db_helper.insert_unknown(db, values)
    else:
        manga_id = check_title(values['title_volume'], Publisher.JPOP, titles)
        if manga_id:
            to_correct.append(fix(manga_id, 1, values))
        else:
            db_helper.insert_unknown(db, values)


def correct_jpop(values):
    news_list = [x for x in values if not x['cover']]
    other = [x for x in values if x not in news_list]
    for n in news_list:
        o = [x for x in other if x['id'] == n['id'] and x['volume'] == n['volume']]
        if o:
            n['cover'] = o[0]['cover']
    return news_list


def check_title(title, publisher, titles):
    title_low = re.sub('[^\w]', '', title).lower()
    if (title_low, publisher) in titles:
        return titles[(title_low, publisher)]
    return ''


def fix(manga_id, volume, values):
    values['id'] = manga_id
    values['volume'] = volume
    values['price'] = values['price'] if values['price'] else "0"
    values.pop('title_volume', None)
    return values
