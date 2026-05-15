from flask import Blueprint
from controllers.blok_controller import create_blok, get_all_blok, get_blok_by_id, update_blok, delete_blok

blok_bp = Blueprint("blok", __name__)

blok_bp.add_url_rule("/blok", view_func=create_blok, methods=["POST"])
blok_bp.add_url_rule("/blok", view_func=get_all_blok, methods=["GET"])
blok_bp.add_url_rule("/blok/<int:id>", view_func=get_blok_by_id, methods=["GET"])
blok_bp.add_url_rule("/blok/<int:id>", view_func=update_blok, methods=["PUT"])
blok_bp.add_url_rule("/blok/<int:id>", view_func=delete_blok, methods=["DELETE"])