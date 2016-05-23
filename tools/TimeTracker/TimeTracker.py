__author__ = 'Natasha'

from flask import Flask

app = Flask(__name__)

wsgi_app = app.wsgi_app

from routes import *

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_HOST', '6001'))
    except ValueError:
        PORT = 6001
    app.run(host='0.0.0.0', port=PORT)
