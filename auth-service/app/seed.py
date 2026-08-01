from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import ROLE_DIRECTOR, User

DIRECTOR_FORENAME = "Scrooge"
DIRECTOR_SURNAME = "McDuck"
DIRECTOR_EMAIL = "onlymoney@gmail.com"
DIRECTOR_PASSWORD = "evenmoremoney"


def seed_director():
    if User.query.filter_by(email=DIRECTOR_EMAIL).first() is not None:
        return

    director = User(
        forename=DIRECTOR_FORENAME,
        surname=DIRECTOR_SURNAME,
        email=DIRECTOR_EMAIL,
        password_hash=generate_password_hash(DIRECTOR_PASSWORD),
        role=ROLE_DIRECTOR,
    )
    db.session.add(director)
    db.session.commit()
