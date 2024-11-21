from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import User
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate

user_bp = Blueprint('users', __name__)

class UserProfileSchema(Schema):
    user_id = fields.String(required=True)
    role = fields.String(required=True)
    name = fields.String(required=True)
    surname = fields.String(required=True)
    email = fields.Email(required=True)
    phone = fields.String(allow_none=True, validate=validate.Length(min=10, max=15))
    dateOfBirth = fields.String(required=True)
    gender = fields.String(required=True)
    location = fields.String(required=True)

user_schema = UserProfileSchema()

@user_bp.route("/update-profile", methods=["POST"])
@token_required
def update_profile():
    data = request.get_json()

    errors = user_schema.validate(data)
    if errors:
        print("Validation errors:", errors)  # Log the errors for debugging
        return jsonify(errors), 400

    user_id = data["user_id"]
    user = User.query.get(user_id) 

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Handle phone number logic
    new_phone = data.get("phone", user.phone)
    if new_phone:
        existing_user_with_phone = User.query.filter(User.phone == new_phone, User.id != user_id).first()
        if existing_user_with_phone:
            # If the phone number is already in use, set it to None
            new_phone = None 

    user.name = data.get("name", user.name)  
    user.surname = data.get("surname", user.surname)  
    user.email = data.get("email", user.email)
    user.phone = new_phone  # Set the new phone number (or None)
    user.date_of_birth = data.get("dateOfBirth", user.date_of_birth)  
    user.gender = data.get("gender", user.gender)  
    user.location = data.get("location", user.location)  

    try:
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")  # Log the error for debugging
        return jsonify({"message": "An error occurred while updating the profile"}), 500
