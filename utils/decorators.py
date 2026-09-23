from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from models.user import User
from extensions import db
import uuid

def admin_required():
    """Decorator: hanya user dengan role 'admin' yang boleh akses."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            try:
                user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
                user = db.session.get(User, user_uuid)
            except Exception:
                user = None
            if not user or user.role != 'admin':
                return jsonify({"message": "Akses ditolak. Hanya admin yang diizinkan."}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def petani_required():
    """Decorator: hanya user dengan role 'petani' yang boleh akses."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            try:
                user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
                user = db.session.get(User, user_uuid)
            except Exception:
                user = None
            if not user or user.role != 'petani':
                return jsonify({"message": "Akses ditolak. Hanya petani yang diizinkan."}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
