from flask import Blueprint
from controllers.petani_controller import (
    create_petani, get_all_petani, get_petani_by_id, update_petani, delete_petani
)

petani_bp = Blueprint("petani", __name__)

petani_bp.add_url_rule("/petani", view_func=create_petani, methods=["POST"])
petani_bp.add_url_rule("/petani", view_func=get_all_petani, methods=["GET"])
petani_bp.add_url_rule("/petani/<string:id>", view_func=get_petani_by_id, methods=["GET"])
petani_bp.add_url_rule("/petani/<string:id>", view_func=update_petani, methods=["PUT"])
petani_bp.add_url_rule("/petani/<string:id>", view_func=delete_petani, methods=["DELETE"])
