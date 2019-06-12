from flask import Blueprint, jsonify
from flask import current_app as app
from flask import send_file
from flask import request

manual_api = Blueprint('manual_api', __name__)


@manual_api.route("/return_all")
def return_all():
    obj = app.config["manual_object"]
    res = obj.get_info()
    return jsonify(res)


@manual_api.route("/refresh")
def refresh_info():
    obj = app.config["manual_object"]
    obj.run()
    return return_all()


@manual_api.route("/get_chart")
def get_chart():
    symbol = request.args.get("symbol")
    obj = app.config["manual_object"]
    filename = obj.create_chart(symbol)
    return send_file(filename, mimetype='image/png')
