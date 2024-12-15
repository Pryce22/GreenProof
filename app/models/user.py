from app import db

class User(db.Model):
    id = db.Column(db.String, primary_key=True)  # UUID come stringa
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, id, email, username, password_hash):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()
