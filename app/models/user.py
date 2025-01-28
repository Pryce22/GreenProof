class User():
    def __init__(self, id, email, name, surname, password_hash, phone_number, birthday):
        self.id = id
        self.email = email
        self.username = name
        self.surname = surname
        self.password_hash = password_hash
        self.phone_number = phone_number
        self.birthay = birthday