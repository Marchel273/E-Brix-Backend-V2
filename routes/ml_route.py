from flask import Blueprint
from controllers.ml_controller import (
    predict_brix, predict_yield, predict_sugar, predict_nira,
    predict_duration, classify_disease, calculate_winter_carp,
    analyze_seasons, infer_multi_target, get_ml_info
)

ml_bp = Blueprint("ml", __name__)

ml_bp.add_url_rule("/ml/predict-brix", view_func=predict_brix, methods=["POST"])
ml_bp.add_url_rule("/ml/predict-yield", view_func=predict_yield, methods=["POST"])
ml_bp.add_url_rule("/ml/predict-sugar", view_func=predict_sugar, methods=["POST"])
ml_bp.add_url_rule("/ml/predict-nira", view_func=predict_nira, methods=["POST"])
ml_bp.add_url_rule("/ml/predict-duration", view_func=predict_duration, methods=["POST"])
ml_bp.add_url_rule("/ml/classify-disease", view_func=classify_disease, methods=["POST"])
ml_bp.add_url_rule("/ml/winter-carp", view_func=calculate_winter_carp, methods=["POST"])
ml_bp.add_url_rule("/ml/analyze-seasons", view_func=analyze_seasons, methods=["POST"])
ml_bp.add_url_rule("/ml/infer", view_func=infer_multi_target, methods=["POST"])
ml_bp.add_url_rule("/ml/info", view_func=get_ml_info, methods=["GET"])
