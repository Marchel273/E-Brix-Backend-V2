from flask import Blueprint
from controllers.auth_controller import (
    register, login, get_profile, request_otp, reset_password
)

auth_bp = Blueprint("auth", __name__)

auth_bp.add_url_rule("/auth/register", view_func=register, methods=["POST"])
auth_bp.add_url_rule("/auth/login", view_func=login, methods=["POST"])
auth_bp.add_url_rule("/auth/profile", view_func=get_profile, methods=["GET"])
auth_bp.add_url_rule("/auth/request-otp", view_func=request_otp, methods=["POST"])
auth_bp.add_url_rule("/auth/reset-password", view_func=reset_password, methods=["POST"])
