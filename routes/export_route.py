from flask import Blueprint
from controllers.export_controller import export_csv, export_pdf

export_bp = Blueprint("export", __name__)

export_bp.add_url_rule("/export/data-brix/csv", view_func=export_csv, methods=["GET"])
export_bp.add_url_rule("/export/data-brix/pdf", view_func=export_pdf, methods=["GET"])
