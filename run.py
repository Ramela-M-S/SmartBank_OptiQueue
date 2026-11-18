from app import socketio
from app import app

if "__main__" == __name__:
    socketio.run(app, debug=True)