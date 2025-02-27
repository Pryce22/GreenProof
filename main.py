import threading
from app import app
from app.controllers import scheduler_controller

thread = threading.Thread(target=scheduler_controller.run_scheduler, daemon=True)
thread.start()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
