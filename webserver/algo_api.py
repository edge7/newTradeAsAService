from flask import Blueprint, jsonify, request, send_file
from flask import current_app as app

algo_api = Blueprint('algo_api', __name__)


@algo_api.route("/return_all")
def return_all():
    obj = app.config["algo_object"]
    res = obj.get_info()
    return jsonify(res)


@algo_api.route("/get_info_equity")
def get_info_equity():

    symbol = request.args.get("symbol")
    strategy = request.args.get("strategy")
    obj = app.config["algo_object"]
    filename = obj.get_info_equity_path(symbol, strategy)
    return send_file(filename, mimetype='image/png')

@algo_api.route("/get_info_back")
def get_info_back():

    symbol = request.args.get("symbol")
    strategy = request.args.get("strategy")
    obj = app.config["algo_object"]
    filename = obj.get_info_back_path(symbol, strategy)
    return send_file(filename, mimetype='image/png')
