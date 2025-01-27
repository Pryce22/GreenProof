from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import geonamescache
from app.config import Config
from app.controllers import user_controller

app = Flask(__name__,
            static_folder='app/static',
            template_folder='app/templates')
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

@app.route('/information_company', methods=['GET', 'POST'])
def information_company():
    return render_template('information_company.html')


@app.route('/password_recover', methods=['GET', 'POST'])
def password_recover():
    return render_template('password_recover.html')

@app.route('/company_register', methods=['GET', 'POST'])
def company_register():
    return render_template('company_register.html')

"""
@app.route('/api/countries')
def get_countries():
    response = requests.get('https://restcountries.com/v3.1/all')
    countries = response.json()
    eu_countries = [country for country in countries if 'EU' in country.get('regionalBlocs', [])]
    return jsonify([{
        'id': country['cca2'],
        'name': country['name']['common']
    } for country in eu_countries])
"""
# Inizializza geonamescache
gc = geonamescache.GeonamesCache()

@app.route('/get_countries', methods=['GET'])
def get_countries():
    # Prendi il termine di ricerca dalla query
    query = request.args.get('query', '')
    
    # Ottieni la lista di paesi
    countries = gc.get_countries()
    
    # Filtra i paesi che corrispondono al termine di ricerca
    filtered_countries = [
        {"id": country_code, "text": country_info['name']}
        for country_code, country_info in countries.items()
        if query.lower() in country_info['name'].lower()  # Controlla se il nome del paese contiene il termine
    ]
    
    return jsonify(filtered_countries)

@app.route('/get_cities', methods=['GET'])
def get_cities():
    country_code = request.args.get('country_code')  # Ottieni il codice del paese dalla query string
    if not country_code:
        return jsonify({'error': 'Country code is required'}), 400

    # Ottieni tutte le città dalla cache
    cities = gc.get_cities()

    # Aggiungi un controllo per verificare che i dati siano nel formato corretto
    if isinstance(cities, dict):
        cities_in_country = []
        for city_key, city in cities.items():
            if city['countrycode'] == country_code:
                cities_in_country.append(city['name'])
    else:
        return jsonify({'error': 'Data format is incorrect'}), 500

    return jsonify(cities_in_country)


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