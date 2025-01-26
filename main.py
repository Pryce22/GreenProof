from flask import Flask, render_template, request, redirect, url_for, session
from app.config import Config
from app.controllers import user_controller

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

@app.route('/')
def home():
    user_id = session.get('user_id')
    username = session.get('username')
    return render_template('index.html', user_id=user_id, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_controller.login_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard', user_id=user['id']))
    return render_template('login.html')

@app.route('/MFA', methods=['GET', 'POST'])
def MFA():
    #if request.method == 'POST':
        #token = request.form['token']
        #if user_controller.verify_token(token):
    return render_template('MFA.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if user_controller.create_user(email, username, password):
            user = user_controller.login_user(email, password)
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard', user_id=user['id']))
    return render_template('register.html')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    tokens = user_controller.get_user_tokens(user_id)
    return render_template('dashboard.html', tokens=tokens, user_id=user_id)

@app.route('/add_token/<user_id>', methods=['POST'])
def add_token(user_id):
    token = request.form['token']
    user_controller.add_token_to_user(user_id, token)
    return redirect(url_for('dashboard', user_id=user_id))

@app.route('/search_companies', methods=['GET', 'POST'])
def seach_companies():
    return render_template('search_companies.html')

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = user_controller.get_user_by_id(user_id)
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)