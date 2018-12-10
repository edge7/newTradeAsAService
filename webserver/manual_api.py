from flask import Blueprint, jsonify
from flask import current_app as app

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
