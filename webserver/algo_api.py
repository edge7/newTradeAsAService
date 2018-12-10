from flask import Blueprint, jsonify
from flask import current_app as app

algo_api = Blueprint('algo_api', __name__)



@algo_api.route("/return_all")
def return_all():
    pass