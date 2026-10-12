from flask import Blueprint
from controllers.scans_controller import get_scans, create_scan, update_scan, delete_scan

scans_bp = Blueprint("scans", __name__)

scans_bp.add_url_rule("/api/scans", view_func=get_scans, methods=["GET"])
scans_bp.add_url_rule("/api/scans", view_func=create_scan, methods=["POST"])
scans_bp.add_url_rule("/api/scans/<string:id>", view_func=update_scan, methods=["PUT"])
scans_bp.add_url_rule("/api/scans/<string:id>", view_func=delete_scan, methods=["DELETE"])

scans_bp.add_url_rule("/scans", view_func=get_scans, methods=["GET"])
scans_bp.add_url_rule("/scans", view_func=create_scan, methods=["POST"])
scans_bp.add_url_rule("/scans/<string:id>", view_func=update_scan, methods=["PUT"])
scans_bp.add_url_rule("/scans/<string:id>", view_func=delete_scan, methods=["DELETE"])
