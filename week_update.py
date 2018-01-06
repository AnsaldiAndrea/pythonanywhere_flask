from datetime import datetime
import database_helper as db_helper


def week_update(_db):
    from flask_app import Releases
    yw = db_helper.to_yearweek(datetime.now())
    week_releases = Releases.query.filter(Releases.yearweek == yw).all()
    for r in week_releases:
        db_helper.update_manga_from_db(_db, r)


if __name__ == '__main__':
    from flask_app import db

    week_update(db)
