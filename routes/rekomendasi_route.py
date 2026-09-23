from flask import Blueprint
from controllers.rekomendasi_controller import (
    get_rekomendasi_panen, get_rekomendasi_by_lahan, get_statistik_brix
)

rekomendasi_bp = Blueprint("rekomendasi", __name__)

rekomendasi_bp.add_url_rule("/rekomendasi/blok/<string:id>", view_func=get_rekomendasi_panen, methods=["GET"])
rekomendasi_bp.add_url_rule("/rekomendasi/lahan/<string:id>", view_func=get_rekomendasi_by_lahan, methods=["GET"])
rekomendasi_bp.add_url_rule("/statistik/blok/<string:id>", view_func=get_statistik_brix, methods=["GET"])
