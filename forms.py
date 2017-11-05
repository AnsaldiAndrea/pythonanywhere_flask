from wtforms import Form, StringField, PasswordField, SelectField, IntegerField, DateTimeField, FloatField
from wtforms.validators import InputRequired, Email, Length, EqualTo


class RegisterForm(Form):
    name = StringField('Name', [Length(min=1, max=99), InputRequired('Please enter your name')])
    email = StringField('Email', [InputRequired('Please enter your email adress'), Email('Email adress is not valid')])
    username = StringField('Username', [Length(min=1, max=30), InputRequired('Please choose an username')])
    password = PasswordField('Password', [
        Length(min=8, max=255),
        InputRequired('Please choose a password longer than 8 characters'),
        EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


class NewMangaForm(Form):
    id = StringField('Id', [Length(min=1, max=16), InputRequired('Unique id')])
    title = StringField('Title', [Length(min=1, max=100), InputRequired('Insert title')])
    volumes = IntegerField('Volumes', [InputRequired('Released Volumes in country of origin')])
    released = IntegerField('Released Volumes', [InputRequired('Released Volumes')])
    publisher = SelectField('Publisher', choices=[('planet', 'Planet Manga'), ('star', 'StarComics'), ('jpop', 'J-POP'),
                                                  ('goen', 'GOEN')])
    status = SelectField('Status', choices=[('ongoing', 'Ongoing'), ('complete', 'Complete'), ('tba', 'TBA')])
    author = StringField('Author(s)', [InputRequired('Author')])
    artist = StringField('Artist(s)', [InputRequired('Artist')])
    complete = SelectField('Complete', choices=[('true', 'Yes'), ('false', 'No')])
    cover = StringField('Cover')


class NewReleaseForm(Form):
    id = StringField('Id', [Length(min=1, max=16), InputRequired('Unique id')])
    title = StringField('Title', [Length(min=1, max=100), InputRequired('Insert title')])
    subtitle = StringField('Subtitle', [Length(min=1, max=150)])
    volume = IntegerField('Volume', [InputRequired('Volume')])
    release_date = DateTimeField('Release Date', [InputRequired('Release Date')], format='%d/%m/%Y')
    price = FloatField('Price', [InputRequired('Price')])
    cover = StringField('Cover')
