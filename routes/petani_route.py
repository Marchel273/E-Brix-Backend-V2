from flask import Blueprint
from controllers.petani_controller import (
    create_petani, get_all_petani, get_petani_by_id, update_petani, delete_petani,
    get_admin_petani_pending, get_admin_petani_approved, get_admin_petani_inactive,
    review_admin_petani, edit_admin_petani, delete_admin_petani
)

petani_bp = Blueprint("petani", __name__)

petani_bp.add_url_rule("/petani", view_func=create_petani, methods=["POST"])
petani_bp.add_url_rule("/petani", view_func=get_all_petani, methods=["GET"])
petani_bp.add_url_rule("/petani/<string:id>", view_func=get_petani_by_id, methods=["GET"])
petani_bp.add_url_rule("/petani/<string:id>", view_func=update_petani, methods=["PUT"])
petani_bp.add_url_rule("/petani/<string:id>", view_func=delete_petani, methods=["DELETE"])

# Admin Petani routes (Web Dashboard)
petani_bp.add_url_rule("/admin/petani/pending", view_func=get_admin_petani_pending, methods=["GET"])
petani_bp.add_url_rule("/admin/petani/approved", view_func=get_admin_petani_approved, methods=["GET"])
petani_bp.add_url_rule("/admin/petani/inactive", view_func=get_admin_petani_inactive, methods=["GET"])
petani_bp.add_url_rule("/admin/petani/review/<string:id_user>", view_func=review_admin_petani, methods=["PUT"])
petani_bp.add_url_rule("/admin/petani/edit/<string:id_user>", view_func=edit_admin_petani, methods=["PUT"])
petani_bp.add_url_rule("/admin/petani/<string:id_user>", view_func=delete_admin_petani, methods=["DELETE"])

