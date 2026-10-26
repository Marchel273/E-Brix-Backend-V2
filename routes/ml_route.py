from flask import Blueprint
from controllers.ml_controller import (
    ml_predict, ml_history, ml_delete_history, ml_clear_history
)

ml_bp = Blueprint("ml", __name__)

ml_bp.add_url_rule("/ml/predict", view_func=ml_predict, methods=["POST"])
ml_bp.add_url_rule("/ml/history", view_func=ml_history, methods=["GET"])
ml_bp.add_url_rule("/ml/history/<int:entry_id>", view_func=ml_delete_history, methods=["DELETE"])
ml_bp.add_url_rule("/ml/history", view_func=ml_clear_history, methods=["DELETE"])
