from flask import Flask
from flask import url_for, redirect
from waitress import serve

from webserver.algo_api import algo_api
from webserver.manual_api import manual_api


def create_app(manual_object, algo_scan_object):
    """Creates a new Flask application and initialize application."""

    app = Flask(__name__, static_url_path='',
                static_folder='../dist',
                template_folder='../dist')

    @app.route('/')
    def home():
        return redirect(url_for('static', filename='index.html'))

    app.url_map.strict_slashes = False
    app.config['manual_object'] = manual_object
    app.config['algo_object']  = algo_scan_object
    app.register_blueprint(manual_api, url_prefix='/api/manual')
    app.register_blueprint(algo_api, url_prefix='/api/algo/')
    return app


def run(manual_scan_object, algo_scan_object):
    serve(create_app(manual_scan_object, algo_scan_object), host='0.0.0.0', port=8807)
