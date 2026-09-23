from flask import Blueprint
from controllers.lahan_controller import (
    create_lahan, get_all_lahan, get_lahan_by_id, update_lahan, delete_lahan
)

lahan_bp = Blueprint("lahan", __name__)

lahan_bp.add_url_rule("/lahan", view_func=create_lahan, methods=["POST"])
lahan_bp.add_url_rule("/lahan", view_func=get_all_lahan, methods=["GET"])
lahan_bp.add_url_rule("/lahan/<string:id>", view_func=get_lahan_by_id, methods=["GET"])
lahan_bp.add_url_rule("/lahan/<string:id>", view_func=update_lahan, methods=["PUT"])
lahan_bp.add_url_rule("/lahan/<string:id>", view_func=delete_lahan, methods=["DELETE"])