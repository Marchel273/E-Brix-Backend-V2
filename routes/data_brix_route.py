from flask import Blueprint
from controllers.data_brix_controller import (
    create_brix, get_all_brix, get_brix_by_id, update_brix, delete_brix, sync_batch,
    api_get_scans, api_create_scan, api_delete_scan
)

data_brix_bp = Blueprint("data_brix", __name__)

data_brix_bp.add_url_rule("/data-brix", view_func=create_brix, methods=["POST"])
data_brix_bp.add_url_rule("/data-brix", view_func=get_all_brix, methods=["GET"])
data_brix_bp.add_url_rule("/data-brix/<string:id>", view_func=get_brix_by_id, methods=["GET"])
data_brix_bp.add_url_rule("/data-brix/<string:id>", view_func=update_brix, methods=["PUT"])
data_brix_bp.add_url_rule("/data-brix/<string:id>", view_func=delete_brix, methods=["DELETE"])
data_brix_bp.add_url_rule("/data-brix/sync", view_func=sync_batch, methods=["POST"])

# Endpoint /api/scans khusus aplikasi Android new-E-Brix
data_brix_bp.add_url_rule("/api/scans", view_func=api_create_scan, methods=["POST"])
data_brix_bp.add_url_rule("/api/scans", view_func=api_get_scans, methods=["GET"])
data_brix_bp.add_url_rule("/api/scans/<string:id>", view_func=get_brix_by_id, methods=["GET"])
data_brix_bp.add_url_rule("/api/scans/<string:id>", view_func=update_brix, methods=["PUT"])
data_brix_bp.add_url_rule("/api/scans/<string:id>", view_func=api_delete_scan, methods=["DELETE"])