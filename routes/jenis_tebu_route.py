from flask import Blueprint
from controllers.jenis_tebu_controller import (
    create_jenis_tebu, get_all_jenis_tebu, get_jenis_tebu_by_id, update_jenis_tebu, delete_jenis_tebu
)

jenis_tebu_bp = Blueprint("jenis_tebu", __name__)

jenis_tebu_bp.add_url_rule("/jenis-tebu", view_func=create_jenis_tebu, methods=["POST"])
jenis_tebu_bp.add_url_rule("/jenis-tebu", view_func=get_all_jenis_tebu, methods=["GET"])
jenis_tebu_bp.add_url_rule("/jenis-tebu/<string:id>", view_func=get_jenis_tebu_by_id, methods=["GET"])
jenis_tebu_bp.add_url_rule("/jenis-tebu/<string:id>", view_func=update_jenis_tebu, methods=["PUT"])
jenis_tebu_bp.add_url_rule("/jenis-tebu/<string:id>", view_func=delete_jenis_tebu, methods=["DELETE"])
