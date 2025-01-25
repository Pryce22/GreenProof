from flask import Flask, jsonify
from supabase import create_client, Client


def create_app():
    app = Flask(__name__)

    SUPABASE_URL = "https://cjoykzgrtvlghogxzdjq.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqb3lremdydHZsZ2hvZ3h6ZGpxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDMwMDY4NiwiZXhwIjoyMDQ5ODc2Njg2fQ.JkShNd00ZSc7QmsthH49aS8fQPqmHuM-Xj3WuSgEsPc"
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    #Creazione della tabella al momento dell'inizializzazione dell'applicazione
    try:
        query = '''
            CREATE TABLE IF NOT EXISTS my_table (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            );
        '''
        response = supabase.postgrest.rpc('execute_sql', {'sql': query}).execute()
        print("Table created successfully")
    except Exception as e:
        print(f"Error creating table: {e}")


    @app.route('/data')
    def get_data():
        response = supabase.table('my_table').select('*').execute()
        data = response.data
        return jsonify(data)

    return app
