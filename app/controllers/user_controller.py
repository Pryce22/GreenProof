from werkzeug.security import generate_password_hash, check_password_hash
import models.user as user_model
import uuid


def create_user(email, username, password):
    id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)
    user = user_model.User(id, email=email, username=username, password_hash=password_hash)
    user.save()
    return user

def check_password(password_hash, password):
    return check_password_hash(password_hash, password)

def verify_email(email):
    user = user_model.User.get_by_email(email)
    return user is not None

def login_user(email, password):
    user = user_model.User.get_by_email(email)
    if user is None:
        return None
    if check_password(user.password_hash, password):
        return user
    return None



