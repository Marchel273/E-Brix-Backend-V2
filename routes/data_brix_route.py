from flask import Blueprint
from controllers.data_brix_controller import (
    create_brix, get_all_brix, get_brix_by_id, update_brix, delete_brix, sync_batch
)

data_brix_bp = Blueprint("data_brix", __name__)

data_brix_bp.add_url_rule("/data-brix", view_func=create_brix, methods=["POST"])
data_brix_bp.add_url_rule("/data-brix", view_func=get_all_brix, methods=["GET"])
data_brix_bp.add_url_rule("/data-brix/<string:id>", view_func=get_brix_by_id, methods=["GET"])
data_brix_bp.add_url_rule("/data-brix/<string:id>", view_func=update_brix, methods=["PUT"])
data_brix_bp.add_url_rule("/data-brix/<string:id>", view_func=delete_brix, methods=["DELETE"])
data_brix_bp.add_url_rule("/data-brix/sync", view_func=sync_batch, methods=["POST"])