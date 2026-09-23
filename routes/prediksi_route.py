from flask import Blueprint
from controllers.prediksi_controller import (
    create_prediksi, get_all_prediksi, get_prediksi_by_id, update_prediksi, delete_prediksi
)

prediksi_bp = Blueprint("prediksi", __name__)

prediksi_bp.add_url_rule("/prediksi", view_func=create_prediksi, methods=["POST"])
prediksi_bp.add_url_rule("/prediksi", view_func=get_all_prediksi, methods=["GET"])
prediksi_bp.add_url_rule("/prediksi/<string:id>", view_func=get_prediksi_by_id, methods=["GET"])
prediksi_bp.add_url_rule("/prediksi/<string:id>", view_func=update_prediksi, methods=["PUT"])
prediksi_bp.add_url_rule("/prediksi/<string:id>", view_func=delete_prediksi, methods=["DELETE"])