import os
from app import app
from app.controllers import scheduler_controller


if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'True': 
        scheduler_controller.start_scheduler()
    app.run(debug=True, port=5000)
