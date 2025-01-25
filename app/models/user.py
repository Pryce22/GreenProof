import json
import os

USER_FILE = os.path.join(os.path.dirname(__file__), '../data/user.json')

class User():
    def __init__(self, id, email, username, password_hash):
        self.id = id
        self.email = email
        self.username = username
        
        self.password_hash = password_hash

    def save(self):
        users = load_users_from_file()
        users.append({
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'password_hash': self.password_hash,
            'verified': False,
            'verification_token': None
        })
        save_users_to_file(users)

def load_users_from_file():
    try:
        with open(USER_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_users_to_file(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file)

