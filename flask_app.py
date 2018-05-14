# TODO:
#   Important:
#   - Replace all instances of manga or release dictionary with new Object classes
#   - Remove Admin pages (useless for now) - keep admin status
#   Next update:
#   - Add statistics to index page
#   - Add This Week + Previous to dashboard for ease of use
#   - Add personal statistics to dashboard
#   - Add footer to all pages
#   - Add genre and artist/author search
#   Future Updates:
#   - Change password encoding to include salt and stronger encoding (check bookmark) + add salt column in user table
#   - Change password checking in login to reflect changes on password encoding
#

import os
import traceback
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, flash, redirect, url_for, session, request, abort, json
from flask_mobility import Mobility
from flask_mobility.decorators import mobile_template
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_sslify import SSLify
from lxml import etree
from sqlalchemy.ext.hybrid import hybrid_method

import database_helper as db_helper
from forms import RegisterForm
from release_parser import ReleaseObject
from static.types.enumtypes import Publisher, Status

app = Flask(__name__)
api = Api(app)
sslify = SSLify(app)
mobility = Mobility(app)
app.secret_key = os.getenv('SECRET_KEY')
app.config["DEBUG"] = True

credential = etree.parse("/home/Raistrike/mysite/credential.xml")

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}?charset=utf8".format(
    username=credential.xpath("//username/text()")[0],
    password=credential.xpath("//password/text()")[0],
    hostname=credential.xpath("//hostname/text()")[0],
    databasename=credential.xpath("//database/text()")[0],
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Manga(db.Model):
    __tablename__ = "manga"

    def __init__(self, data):
        self.id = data['id']
        self.title = data['title']
        self.volumes = data['volumes']
        self.released = data['released']
        self.original = data.get('original', '')
        self.publisher = data['publisher']
        self.status = data['status']
        self.authors = data['author']
        self.artists = data['artist']
        self.genre = data['genre']
        self.complete = data['complete']
        self.cover = data['cover']

    id = db.Column(db.String(16), primary_key=True, autoincrement=False)
    title = db.Column(db.String(100), nullable=False)
    original = db.Column(db.String(100))
    volumes = db.Column(db.Integer, nullable=False, default=0)
    released = db.Column(db.Integer, nullable=False, default=0)
    publisher = db.Column(db.Enum(Publisher), nullable=False)
    status = db.Column(db.Enum(Status), nullable=False)
    authors = db.Column(db.String(100), nullable=False)
    artists = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.Text())
    complete = db.Column(db.Boolean(), default=0)
    cover = db.Column(db.Text(), nullable=False)


class Alias(db.Model):
    __tablename__ = "alias"

    def __init__(self, manga_id, alias):
        self.manga_id = manga_id
        self.title = alias

    manga_id = db.Column(db.String(16), db.ForeignKey('manga.id'), primary_key=True)
    manga = db.relationship("Manga", backref=db.backref("alias", uselist=False))
    title = db.Column(db.String(100), primary_key=True)


class Releases(db.Model):
    __tablename__ = "releases"

    def __init__(self, data):
        self.manga_id = data['id']
        self.subtitle = data['subtitle']
        self.volume = data['volume']
        if type(data['release_date']) == str:
            self.release_date = datetime.strptime(data['release_date'], "%Y-%m-%d")
        else:
            self.release_date = data['release_date']
        self.price = data['price']
        self.cover = data['cover']
        self.yearweek = db_helper.to_yearweek(self.release_date)

    release_id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    manga_id = db.Column(db.String(16), db.ForeignKey('manga.id'), nullable=False, unique=True)
    manga = db.relationship("Manga", backref=db.backref("releases", uselist=False, order_by="Manga.title"))
    subtitle = db.Column(db.String(64), unique=False)
    volume = db.Column(db.Integer, nullable=False, unique=True)
    release_date = db.Column(db.DateTime, nullable=False, unique=True)
    price = db.Column(db.Float(), nullable=False, default=0)
    cover = db.Column(db.Text())
    yearweek = db.Column(db.Integer, nullable=False)

    @hybrid_method
    def bounds(self, _from=None, _to=None, _at=None):
        if _at:
            return self.yearweek == _at
        if _from and _to:
            return (self.yearweek >= _from) & (self.yearweek < _to)
        if _from:
            return self.yearweek >= _from
        if _to:
            return self.yearweek < _to
        return False


class Collection(db.Model):
    __tablename__ = "collection"

    def __init__(self, data):
        self.manga_id = data['id']
        self.subtitle = data['subtitle']
        self.volume = data['volume']
        self.cover = data['cover']

    collection_id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    manga_id = db.Column(db.String(16), db.ForeignKey('manga.id'), nullable=True, unique=True)
    manga = db.relationship("Manga", backref=db.backref("collection", uselist=False))
    subtitle = db.Column(db.String(50), unique=True)
    volume = db.Column(db.Integer, nullable=False, unique=True)
    cover = db.Column(db.Text())


class Users(db.Model):
    __tablename__ = "users"

    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = password

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(30), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    register_date = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow())
    admin = db.Column(db.Boolean(), nullable=False, default=False)


class UserManga(db.Model):
    __tablename__ = "usermanga"

    def __init__(self, user_id, manga_id):
        self.user_id = user_id
        self.manga_id = manga_id

    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), primary_key=True)
    manga = db.relationship("Manga", backref=db.backref("usermanga", uselist=False))
    visibility = db.Column(db.Boolean(), nullable=False, default=1)


class UserCollection(db.Model):
    __tablename__ = "usercollection"

    def __init__(self, user_id, collection_id):
        self.user_id = user_id
        self.collection_id = collection_id

    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.collection_id'), primary_key=True)
    collection = db.relationship("Collection", backref=db.backref("usercollection", uselist=False))


class ReleaseMap(db.Model):
    __tablename__ = "releasemap"

    def __init__(self, release_id, collection_id):
        self.release_id = release_id
        self.collection_id = collection_id

    release_id = db.Column(db.Integer, db.ForeignKey('releases.release_id'), primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.collection_id'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error_500.html'), 500


def is_logged_in(f):
    """check if user is logged in"""

    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


def is_admin(f):
    """check if user has admin privileges"""

    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and 'admin' in session:
            return f(*args, **kwargs)
        elif 'logged_in' in session:
            flash('Unauthorized, You are not an admin', 'danger')
            return redirect(url_for('dashboard'))
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


@app.route("/")
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return type(e)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        u = db_helper.register_user(db, form)
        if u:
            flash('Registration Successful.\n Welcome {}'.format(u.username), 'success')
            return redirect(url_for('index'))
        else:
            flash('Username is already taken', 'danger')
    return render_template('register.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'logged_in' in session:
            flash('You are already logged in as: {}'.format(session['username']), 'warning')
            return redirect(url_for('dashboard'))
        r = db_helper.log_in(request, session)
        flash(r['message'], r['level'])
        if r['status'] == 'OK':
            return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route("/manga")
@mobile_template("{mobile/}manga.html")
def manga(template):
    manga_list = db_helper.get_manga()
    if session.get('logged_in', False):
        user_manga = db_helper.get_user_manga(session.get('user_id'))
        return render_template(template, MANGA_LIST=manga_list, USER_LIST=user_manga)
    return render_template(template, MANGA_LIST=manga_list)


@app.route("/manga/<string:manga_id>")
def manga_item(manga_id):
    try:
        _manga = db_helper.get_manga_by_id(manga_id)
        if not _manga:
            return abort(404, massage="No Manga with id={}".format(manga_id))
        collection = db_helper.get_collection(manga_id)
        release_list = db_helper.get_releases_by_manga_id(manga_id)
        if session.get('logged_in', False):
            user_collection = db_helper.get_user_collection(session.get('user_id'))
            return render_template('item/manga.html', MANGA=_manga, COLLECTION=collection, RELEASE_LIST=release_list,
                                   USER_COLLECTION=user_collection)
        return render_template('item/manga.html', MANGA=_manga, COLLECTION=collection, RELEASE_LIST=release_list,
                               USER_COLLECTION=[])
    except Exception as e:
        return str(e)


@app.route("/user/manga/<string:manga_id>", methods=["POST", "DELETE"])
@is_logged_in
def user_action_manga(manga_id):
    m = db_helper.get_manga_by_id(manga_id)
    if m:
        # POST REQUEST: ADD MANGA TO USER WATCHLIST
        if request.method == "POST":
            try:
                if not db_helper.is_user_watching(session['user_id'], manga_id):
                    um = UserManga(session['user_id'], manga_id)
                    db.session.add(um)
                    db.session.commit()
            except Exception as e:
                return abort(500, message="an error occured:\n{}".format(traceback.format_exc(e)))
        # DELETE REQUEST: REMOVE MANGA FROM USER WATCHLIST
        elif request.method == "DELETE":
            try:
                um = db_helper.is_user_watching(session['user_id'], manga_id)
                if um:
                    db.session.delete(um)
                    db.session.commit()
            except Exception as e:
                return abort(500, message="an error occured:\n{}".format(traceback.format_exc(e)))
    else:
        return abort(404, message="cannot find manga with id={}".format(manga_id))
    return "OK", 200, {'ContentType': 'application/json'}


@app.route("/user/release/<string:release_id>", methods=["POST", "DELETE"])
@is_logged_in
def user_action_release(release_id):
    r = db_helper.get_release_by_id(release_id)
    if r:
        c = db_helper.get_volume_from(r.manga_id, r.volume, r.subtitle)
        if c:
            return user_action_collection(c.collection_id)
        else:
            return abort(404,
                         message="cannot find volume with values=[{},{},{}]".format(r.manga_id, r.volume, r.subtitle))
    else:
        return abort(404, message="cannot find release with release_id={}".format(r.release_id))


@app.route("/user/collection/<string:collection_id>", methods=["POST", "DELETE"])
@is_logged_in
def user_action_collection(collection_id):
    c = db_helper.get_volume(collection_id)
    if c:
        # POST REQUEST: ADD VOLUME TO USER LIBRARY
        if request.method == "POST":
            try:
                if not db_helper.is_volume_in_user_library(session['user_id'], collection_id):
                    uc = UserCollection(session['user_id'], collection_id)
                    db.session.add(uc)
                    db.session.commit()
            except Exception as e:
                with open('rel.log', 'w+') as f:
                    f.write("...\n" + traceback.format_exc(e))
                return abort(500, message="an error occured:\n{}".format(traceback.format_exc(e)))
        # DELETE REQUEST: REMOVE VOLUME FROM USER LIBRARY
        elif request.method == "DELETE":
            try:
                uc = db_helper.is_volume_in_user_library(session['user_id'], collection_id)
                if uc:
                    db.session.delete(uc)
                    db.session.commit()
            except Exception as e:
                return abort(500, message="an error occured:\n{}".format(traceback.format_exc(e)))
    else:
        return abort(404, message="cannot find volume with collection_id={}".format(collection_id))
    return "OK", 200, {'ContentType': 'application/json'}


header = {'prev': 'Previous Weeks', 'this': 'This Week', 'next': 'Next Week', 'future': 'Future Releases'}


@app.route("/releases")
@mobile_template('{mobile/}releases.html')
def releases(template):
    yearweek_now = db_helper.to_yearweek(datetime.now())
    yearweek_prev = db_helper.to_yearweek(datetime.now() - timedelta(weeks=8))
    yearweek_next = db_helper.to_yearweek(datetime.now() + timedelta(weeks=1))
    yearweek_future = db_helper.to_yearweek(datetime.now() + timedelta(weeks=2))

    if session.get('logged_in', False):
        releases_prev = db_helper.get_user_releases(session.get('user_id'), _from=yearweek_prev, _to=yearweek_now)
        releases_this = db_helper.get_user_releases(session.get('user_id'), _at=yearweek_now)
        releases_next = db_helper.get_user_releases(session.get('user_id'), _at=yearweek_next)
        releases_future = db_helper.get_user_releases(session.get('user_id'), _from=yearweek_future)
    else:
        releases_prev = db_helper.get_releases_by_week(_from=yearweek_prev, _to=yearweek_now)
        releases_this = db_helper.get_releases_by_week(_at=yearweek_now)
        releases_next = db_helper.get_releases_by_week(_at=yearweek_next)
        releases_future = db_helper.get_releases_by_week(_from=yearweek_future)

    release_dict = {'prev': releases_prev,
                    'this': releases_this,
                    'next': releases_next,
                    'future': releases_future}

    return render_template(template, RELEASE_DICT=release_dict, HEADER=header)


@app.route("/test")
def test_route():
    return render_template('test.html')


@app.route("/admin")
@is_admin
def admin_login():
    return render_template('admin/admin.html')


# region API

class ApiIds(Resource):
    def get(self):
        data = db_helper.get_ids()
        if not data:
            return abort(505, 'unexpected error')
        return json.dumps(data)


class ApiMangaId(Resource):
    def get(self, manga_id):
        data = db_helper.get_manga_by_id(manga_id)
        if not data:
            return abort(404, 'no manga with id = {}'.format(manga_id))
        return json.dumps(db_helper.manga_to_dict(data), ensure_ascii=False)


class ApiManga(Resource):
    def get(self):
        data = Manga.query.all()
        return json.dumps([db_helper.manga_to_dict(x) for x in data], ensure_ascii=False)

    def post(self):
        x = db_helper.insert_manga(db, request.get_json())
        if x['status'] == 'error':
            return abort(500, x['message'])
        return {'message': x['message']}


class ApiMangaUpdate(Resource):
    def post(self):
        x = db_helper.update_manga(db, request.get_json())
        if x['status'] == 'error':
            return abort(500, x['message'])
        return {'message': x['message']}


class ApiMangaUpdateFrom(Resource):
    def get(self, yearweek):
        if not yearweek:
            return abort(500, message='bad input')
        for r in Releases.query.filter(Releases.yearweek >= yearweek).all():
            x = db_helper.update_manga_from_db(db, r)
            if x['status'] == 'error':
                return abort(500, x['message'])
        return {'message': 'updated all manga'}


class ApiAlias(Resource):
    def post(self):
        x = db_helper.insert_alias(db, request.get_json()['id'], request.get_json()['alias'])
        if x['status'] == 'error':
            return abort(500, x['message'])
        return {'message': x['message']}


class ApiParseRelease(Resource):
    def post(self):
        release_obj = ReleaseObject(request.get_json())
        release_obj.parse()
        return release_obj.as_dict()


class ApiReleases(Resource):
    def post(self):
        x = db_helper.insert_release(db, request.get_json())
        if x['status'] == 'error':
            return abort(500, x['message'])
        return {'message': x['message']}


api.add_resource(ApiIds, '/api/ids')
api.add_resource(ApiMangaId, '/api/manga/<string:manga_id>')
api.add_resource(ApiManga, '/api/manga')
api.add_resource(ApiMangaUpdate, '/api/manga/update')
api.add_resource(ApiMangaUpdateFrom, '/api/manga/update/from/<string:yearweek>')
api.add_resource(ApiAlias, '/api/alias')
api.add_resource(ApiReleases, '/api/releases')
api.add_resource(ApiParseRelease, '/api/releases/parse')

# endregion


# region Jinja2 Filters
def filter_format_datetime(value: datetime):
    return value.strftime("%d/%m/%Y")


def filter_format_commas(value: str):
    return value.replace(",", ", ")


def filter_format_price(value):
    return "{:10.2f}".format(value)


app.jinja_env.filters['format_date'] = filter_format_datetime
app.jinja_env.filters['format_commas'] = filter_format_commas
app.jinja_env.filters['format_price'] = filter_format_price
# endregion
