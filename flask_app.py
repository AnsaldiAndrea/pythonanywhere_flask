import os
from datetime import datetime, timedelta
from functools import wraps
import traceback

from flask import Flask, render_template, flash, redirect, url_for, session, request, abort, json, Markup
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_migrate import Migrate

from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.sql.expression import func, tuple_

import database_helper as db_helper
from forms import RegisterForm, NewMangaForm, NewReleaseForm
from release_parser import ReleaseParser
from static.types.enumtypes import Publisher, Status

app = Flask(__name__)
api = Api(app)
app.secret_key = os.getenv('SECRET_KEY')
app.config["DEBUG"] = True


SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}?charset=utf8".format(
    username="Raistrike",
    password="Nuvoletta2",
    hostname="Raistrike.mysql.pythonanywhere-services.com",
    databasename="Raistrike$data",
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)


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
        self.authors = data['authors']
        self.artists = data['artists']
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
        self.release_date = data['release_date']
        self.price = data['price']
        self.cover = data['cover']
        self.year = data['release_date'].isocalendar()[0]
        self.week = data['release_date'].isocalendar()[1]

    manga_id = db.Column(db.String(16), db.ForeignKey('manga.id'), primary_key=True)
    manga = db.relationship("Manga", backref=db.backref("releases", uselist=False))
    subtitle = db.Column(db.String(50))
    volume = db.Column(db.Integer, nullable=False, primary_key=True)
    release_date = db.Column(db.DateTime, nullable=False, primary_key=True)
    price = db.Column(db.Float(), nullable=False, default=0)
    cover = db.Column(db.Text())
    year = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)

    @hybrid_method
    def bounds(self, _from_year=None, _from_week=None, _to_year=None, _to_week=None, _at_year=None, _at_week=None):
        now = datetime.now()
        if _at_year and _at_week:
            return self.year == _at_year & self.week==_at_week
        if _from_year and _from_week and _to_year and _to_week:
            if self.year == _from_year and self.week >= _from_week:
                return (self.year == _to_year and self.week < _to_week) or self.year < _to_year
            return self.year > _from_year
        if _from_year and _from_week:
            return (self.year == _from_year and self.week >= _from_week) or self.year > _from_year
        if _to_year and _to_week:
            return (self.year == _to_year and self.week < _to_week) or self.year < _to_year
        return False

    @hybrid_method
    def user(self, _collection=None, _manga=None):
        if _collection and _manga:
            return (self.manga_id in _manga) &  ((self.manga_id, self.volume) not in _collection)
        else:
            return True


class Collection(db.Model):
    __tablename__ = "collection"

    def __init__(self, data):
        self.manga_id = data['id']
        self.subtitle = data['subtitle']
        self.volume = data['volume']
        self.cover = data['cover']

    manga_id = db.Column(db.String(16), db.ForeignKey('manga.id'), primary_key=True)
    manga = db.relationship("Manga", backref=db.backref("collection", uselist=False))
    subtitle = db.Column(db.String(50))
    volume = db.Column(db.Integer, nullable=False, primary_key=True)
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

    def __init__(self, user_id, manga_id, volume):
        self.user_id = user_id
        self.manga_id = manga_id
        self.volume = volume

    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), primary_key=True)
    manga = db.relationship("Manga", backref=db.backref("usercollection", uselist=False))
    volume = db.Column(db.Integer, nullable=False, primary_key=True)


class Unknown(db.Model):
    __tablename__ = "unknown"

    def __init__(self, data):
        self.title = data['title']
        self.subtitle = data['subtitle']
        self.publisher = data['publisher']
        self.release_date = data['release_date']
        self.price = data['price']
        self.cover = data['cover']

    title = db.Column(db.String(150), primary_key=True)
    subtitle = db.Column(db.String(150), primary_key=True)
    publisher = db.Column(db.String(6))
    release_date = db.Column(db.DateTime, nullable=False, primary_key=True)
    price = db.Column(db.Float(), nullable=False, default=0)
    cover = db.Column(db.Text())


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
def manga():
    # try:
    m = Manga.query.order_by(Manga.title).all()
    if session.get('logged_in', False):
        u = UserManga.query.filter_by(user_id=session['user_id']).all()
        ul = [x.manga_id for x in u]
        return render_template('manga.html', MANGA_LIST=m, USER_LIST=ul)
    return render_template('manga.html', MANGA_LIST=m)
    # except Exception as e:
    #    return str(e)


@app.route("/manga/<string:manga_id>")
def manga_item(manga_id):
    user_collection = []
    try:
        m = Manga.query.filter_by(id=manga_id).first()
        collection = Collection.query.filter_by(manga_id=manga_id).join(Manga).order_by(Collection.volume).all()
        release_list = Releases.query.filter_by(manga_id=manga_id).join(Manga).order_by(Releases.release_date).all()
        if session.get('logged_in', False):
            user_c_raw = UserCollection.query.filter_by(user_id=session['user_id'], manga_id=manga_id).all()
            user_collection = [(c.manga_id, c.volume) for c in user_c_raw]
        if m is not None:
            return render_template('item/manga.html', MANGA=m, COLLECTION=collection, RELEASE_LIST=release_list,
                                   USER_COLLECTION=user_collection)
        else:
            return abort(404)
    except Exception as e:
        return str(e)


@app.route("/manga/<string:manga_id>/add", methods=["POST"])
@is_logged_in
def add_manga(manga_id):
    user_id = session['user_id']
    um = UserManga(user_id, manga_id)
    try:
        db.session.add(um)
        db.session.commit()
        return json.dumps({'success': True, 'manga_id': manga_id})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@app.route("/manga/<string:manga_id>/delete", methods=["POST"])
@is_logged_in
def delete_manga(manga_id):
    user_id = session['user_id']
    try:
        um = UserManga.query.filter_by(user_id=user_id, manga_id=manga_id).first()
        db.session.delete(um)
        db.session.commit()
        return json.dumps({'success': True, 'manga_id': manga_id})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@app.route("/releases/<string:manga_id>/<int:volume>/add", methods=["POST"])
@is_logged_in
def add_volume(manga_id, volume):
    try:
        uv = UserCollection(session['user_id'], manga_id, volume)
        db.session.add(uv)
        db.session.commit()
        return json.dumps({'success': True, 'manga_id': manga_id, 'volume': volume})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@app.route("/releases/<string:manga_id>/<int:volume>/delete", methods=["POST"])
@is_logged_in
def delete_volume(manga_id, volume):
    try:
        uv = UserCollection.query.filter_by(user_id=session['user_id'], manga_id=manga_id, volume=volume).first()
        db.session.delete(uv)
        db.session.commit()
        return json.dumps({'success': True, 'manga_id': manga_id, 'volume': volume})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


header = {'prev': 'Previous Weeks', 'this': 'This Week', 'next': 'Next Week', 'future': 'Future Releases'}

@app.route("/releases")
def releases():
    data = Releases.query.join(Manga).order_by(Releases.release_date).all()

    now = datetime.now()
    date_prev = now - timedelta(weeks=8)
    date_next = now + timedelta(weeks=1)
    t_now = now.isocalendar()[:2]
    t_prev = date_prev.isocalendar()[:2]
    t_next = date_next.isocalendar()[:2]

    user_collection = []
    user_manga = []
    if session.get('logged_in', False):
        user_collection = UserCollection.query.filter(UserCollection.user_id == session['user_id']).all()
        user_collection = [(c.manga_id, c.volume) for c in user_collection]
        user_manga = UserManga.query.filter(UserManga.user_id == session['user_id']).all()
        user_manga = [m.manga_id for m in user_manga]
    """
    week_dict = {'prev': Releases.query.filter(
                    Releases.bounds(_from=-8, _to=0) and Releases.user(_collection=user_collection, _manga=user_manga)).all(),
                 'this': Releases.query.filter(
                    Releases.bounds(_at=0) and Releases.user(_collection=user_collection, _manga=user_manga)).all(),
                 'next': Releases.query.filter(
                    Releases.bounds(_at=1) and Releases.user(_collection=user_collection, _manga=user_manga)).all(),
                 'future': Releases.query.filter(
                    Releases.bounds(_from=2) and Releases.user(_collection=user_collection, _manga=user_manga)).all()}
    """
    week_dict = {'prev':[],'this':[],'next':[],'future':[]}
    for r in data:
        if (r.manga_id, r.volume) in user_collection or (user_manga and r.manga_id not in user_manga):
            continue
        t_r = r.release_date.isocalendar()[:2]
        if t_r < t_prev:
            continue
        elif t_prev <= t_r < t_now:
            week_dict['prev'].append(r)
        elif t_r == t_now:
            week_dict['this'].append(r)
        elif t_r == t_next:
            week_dict['next'].append(r)
        else:
            week_dict['future'].append(r)
    price_dict = {key: sum(x.price for x in value) for key, value in week_dict.items()}
    return render_template('releases.html', RELEASE_DICT=week_dict, PRICE=price_dict, HEADER=header)


@app.route("/test")
def test_route():
    return render_template('test.html')


@app.route("/admin")
@is_admin
def admin_login():
    return render_template('admin/admin.html')


@app.route("/admin/unknown")
@is_admin
def unknown():
    u = Unknown.query.all()
    return render_template('admin/unknown.html', unknown=u)


@app.route("/admin/new_manga", methods=['GET', 'POST'])
@is_admin
def admin_new_manga():
    if request.method == 'POST':
        if request.form['btn'] == 'Submit JSON':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            if file and file.filename.endswith('.json'):
                json_data = json.loads(file.read().decode('utf-8'))
                if 'info' in json_data:
                    try:
                        title = json_data['info']['title']
                        db_helper.insert_manga(db, json_data['info'])
                        if 'release' in json_data:
                            for r in json_data['release']:
                                db_helper.insert_release(db, r)
                        if 'collection' in json_data:
                            for i in json_data['collection']:
                                db_helper.insert_collection_item(db, i)
                        message = Markup('<strong>{}</strong> addedd successfully'.format(title))
                        flash(message, 'success')
                        return redirect(url_for('dashboard'))
                    except Exception as e:
                        message = Markup('<strong>Error</strong>\nA problem occurred while adding manga: {}'.format(
                            traceback.format_exc()))
                        flash(message, 'danger')
                        return redirect(request.url)
                else:
                    flash('Uploaded file has wrong format', 'danger')
                    return redirect(request.url)
            else:
                flash('Uploaded file is not JSON')
                return redirect(request.url)
        else:
            form = NewMangaForm(request.form)
            if form.validate():
                try:
                    title = request.form['title']
                    db_helper.insert_manga(db, request.form)
                    message = Markup('<strong>{}</strong> addedd successfully'.format(title))
                    flash(message, 'success')
                    return render_template('admin/new_manga.html', form=form)
                except Exception as e:
                    message = Markup('<strong>Error</strong>\nA problem occurred while adding manga: {}'.format(e))
                    flash(message, 'danger')
                    return render_template('admin/new_manga.html', form=form)
            else:
                return render_template('admin/new_manga.html', form=form)
    else:
        form = NewMangaForm(request.form)
        return render_template('admin/new_manga.html', form=form)


@app.route("/admin/new_release", methods=['GET', 'POST'])
@is_admin
def admin_new_release():
    form = NewReleaseForm(request.form)
    if request.method == 'POST':
        pass
    else:
        q = Manga.query.all()
        title_list = [x.title for x in q]
        title_dict = {x.title: x.id for x in q}
        title = request.args.get('title', '')
        subtitle = request.args.get('subtitle', '')
        release_date = request.args.get('release_date', '')
        price = request.args.get('price', '')
        cover = request.args.get('cover', '')
        return render_template('admin/new_release.html', form=form, title_list=title_list, title_dict=title_dict,
                               title=title, subtitle=subtitle, release_date=release_date, price=price, cover=cover)


@app.route("/admin/upload", methods=["GET", "POST"])
@is_admin
def upload():
    if request.method == 'POST':
        if request.form['btn'] == 'Submit JSON':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            if file and file.filename.endswith('.json'):
                flash(file.read().decode('utf-8'), 'success')
                return redirect(request.url)
    return render_template('admin/upload.html')


@app.route("/api/manga", methods=["GET", "POST"])
def api_manga():
    if request.method == 'POST':
        data = request.get_json()
        return db_helper.insert(db, data)
    else:
        m = Manga.query.all()
        s = json.dumps([db_helper.manga_to_dict(x) for x in m], ensure_ascii=False)
        with open('api.log', 'w+') as f:
            f.write(s)
        return s


@app.route("/api/manga/id", methods=["GET"])
def api_id():
    m = Manga.query.all()
    return json.dumps({"id": [x.id for x in m]})


@app.route("/api/parse_releases", methods=["POST"])
def api_parse_releases():
    data = request.get_json()
    return json.dumps(ReleaseParser(db).parse(data))


@app.route("/api/alias", methods=["GET"])
def api_alias():
    return json.dumps(db_helper.get_titles_with_alias(), indent=4, ensure_ascii=False)


@app.route("/api/update_manga", methods=["POST"])
def api_update_manga():
    r = db_helper.update_manga(db, request.get_json())
    return json.dumps(r)
