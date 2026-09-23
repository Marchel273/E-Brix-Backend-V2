from flask import Blueprint
from controllers.blok_lahan_controller import (
    create_blok_lahan, get_all_blok_lahan, get_blok_lahan_by_id, update_blok_lahan, delete_blok_lahan
)

blok_lahan_bp = Blueprint("blok_lahan", __name__)

blok_lahan_bp.add_url_rule("/blok-lahan", view_func=create_blok_lahan, methods=["POST"])
blok_lahan_bp.add_url_rule("/blok-lahan", view_func=get_all_blok_lahan, methods=["GET"])
blok_lahan_bp.add_url_rule("/blok-lahan/<string:id>", view_func=get_blok_lahan_by_id, methods=["GET"])
blok_lahan_bp.add_url_rule("/blok-lahan/<string:id>", view_func=update_blok_lahan, methods=["PUT"])
blok_lahan_bp.add_url_rule("/blok-lahan/<string:id>", view_func=delete_blok_lahan, methods=["DELETE"])
