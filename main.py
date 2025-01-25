# filepath: /c:/Users/valer/Documents/Software-Security-and-Blockchain/main.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)