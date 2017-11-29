import re
import database_helper as db_helper


class ReleaseParser:
    def __init__(self, db):
        self.db = db

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
                return x
        for x in correct_jpop(to_correct):
            db_helper.insert_release(self.db, x)


def regex_planet(db, values, titles):
    match = re.fullmatch('((.*)\\s(\\d+))', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, volume, values))
        else:
            db_helper.insert_unknown(db, values)
    else:
        manga_id = check_title(values['title_volume'], titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, 1, values))
        else:
            db_helper.insert_unknown(db, values)


def regex_star(db, values, titles):
    match = re.fullmatch('((.*)\\sn\\.\\s(\\d+))|((.*)\\svolume\\sunico)', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, volume, values))
        else:
            db_helper.insert_unknown(db, values)
    elif match and match.group(4):
        title = match.group(5)
        manga_id = check_title(title, titles)
        if manga_id:
            db_helper.insert_release(db, fix(manga_id, 1, values))
        else:
            db_helper.insert_unknown(db, values)
    else:
        db_helper.insert_unknown(db, values)


def regex_jpop(db, values, titles, to_correct):
    match = re.fullmatch('((.*)\\s(\\d+))', values['title_volume'])
    if match and match.group(1):
        title = match.group(2)
        volume = int(match.group(3))
        manga_id = check_title(title, titles)
        if manga_id:
            to_correct.append(fix(manga_id, volume, values))
        else:
            db_helper.insert_unknown(db, values)
    else:
        manga_id = check_title(values['title_volume'], titles)
        if manga_id:
            to_correct.append(fix(manga_id, 1, values))
        else:
            db_helper.insert_unknown(db, values)


def correct_jpop(values):
    news_list = [x for x in values if not x['cover']]
    other = [x for x in values if x not in news_list]
    for n in news_list:
        o = [x for x in other if x['manga_id'] == n['manga_id'] and x['volume'] == n['volume']]
        if o:
            n['cover'] = o[0]['cover']
    return news_list


def check_title(title, titles):
    title_low = re.sub('[^\w]', '', title).lower()
    if title_low in titles:
        return titles[title_low]
    return ''


def fix(manga_id, volume, values):
    values['manga_id'] = manga_id
    values['volume'] = volume
    values['price'] = values['price'] if values['price'] else "0"
    values.pop('title_volume', None)
