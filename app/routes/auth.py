from flask import Blueprint, request, jsonify
from ..models import OTP, User
from ..db import db
import jwt
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import or_, and_
from ..utils import token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print("Data in signup request:", data)

    role = data.get('role')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    print("Password is here:", password)

    existing_user = User.query.filter(
    or_(
        and_(User.email == email, email is not None),
        and_(User.phone == phone, phone is not None)
    )
    ).first()
    if existing_user:
        return jsonify({"message": "User already exists"}), 409

    new_user = User(role=role)
    if email:
        new_user.email = email
    if phone:
        new_user.phone = phone
    new_user.set_password(password)  
    db.session.add(new_user)
    db.session.commit()
    token_data = {
        'user_id': new_user.id,
        'role': new_user.role,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION_DELTA'])
    }
    token = jwt.encode(token_data, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


    return jsonify({
        "message": "New registration successful",
        "user_id": new_user.id,
        "token":token
    }), 201

@auth_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    print("data", data)
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    if not email and not phone:
        return jsonify({"message": "Either email or phone number must be provided"}), 400

    user = User.query.filter((User.email == email) | (User.phone == phone)).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404

    if not user.check_password(password):
        return jsonify({"message": "Invalid password"}), 401

    token_data = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION_DELTA'])
    }
    token = jwt.encode(token_data, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user_id":user.id
    }), 200

@auth_bp.route('/mobile-otp', methods=['POST'])
@token_required
def mobile_otp():
    data = request.get_json()
    phone = data.get('phone')
    user_id = data.get('user_id')

    if not phone or not user_id:
        return jsonify({"message": "Phone number and user_id are required"}), 400

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # OTP valid for 5 minutes

    token_user_id = request.user_data.get('user_id')
    if token_user_id != user_id:
        return jsonify({"message": "Authentication error: User ID mismatch"}), 403
    
    new_otp = OTP(
        user_id=user_id,
        phone=phone,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp":otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/resend-mobile-otp', methods=['POST'])
@token_required
def resend_mobile_otp():
    data = request.get_json()
    phone = data.get('phone')
    user_id = data.get('user_id')

    if not phone or not user_id:
        return jsonify({"message": "Phone number and user_id are required"}), 400

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  

    new_otp = OTP(
        user_id=user_id,
        phone=phone,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp":otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/verify-mobile-otp', methods=['POST'])
@token_required
def verify_mobile_otp():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    otp_code = data.get('otp')
    user_id = data.get("user_id")

    if not transaction_id or not otp_code:
        return jsonify({"message": "Transaction ID and OTP are required"}), 400

    otp_entry = OTP.query.filter_by(transaction_id=transaction_id).first()

    if not otp_entry:
        return jsonify({"message": "Invalid transaction ID"}), 404

    if otp_entry.otp == otp_code and datetime.utcnow() < otp_entry.expires_at:
        user = User.query.get(user_id)
        # if user:
        #     user.phone = otp_entry.phone  
        #     db.session.commit()
        return jsonify({"message": "OTP verification successful"}), 200
    else:
        return jsonify({"message": "OTP verification failed or expired"}), 400

@auth_bp.route('/email-otp', methods=['POST'])
@token_required
def email_otp():
    data = request.get_json()
    email = data.get('email')
    user_id = data.get('user_id')

    if not email or not user_id:
        return jsonify({"message": "Email Id and user_id are required"}), 400

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  

    new_otp = OTP(
        user_id=user_id,
        email=email,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp":otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/resend-email-otp', methods=['POST'])
@token_required
def resend_email_otp():
    data = request.get_json()
    email = data.get('email')
    user_id = data.get('user_id')

    if not email or not user_id:
        return jsonify({"message": "Email Id and user_id are required"}), 400

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  

    new_otp = OTP(
        user_id=user_id,
        email=email,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp":otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/verify-email-otp', methods=['POST'])
@token_required
def verify_email_otp():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    otp_code = data.get('otp')
    user_id = data.get("user_id")

    if not transaction_id or not otp_code:
        return jsonify({"message": "Transaction ID and OTP are required"}), 400

    otp_entry = OTP.query.filter_by(transaction_id=transaction_id).first()

    if not otp_entry:
        return jsonify({"message": "Invalid transaction ID"}), 404

    if otp_entry.otp == otp_code and datetime.utcnow() < otp_entry.expires_at:
        user = User.query.get(user_id)
        # if user:
        #     user.email = otp_entry.email
        #     db.session.commit()

        return jsonify({
            "message": "OTP verification successful",
            "user": user.to_dict()
        }), 200
    else:
        return jsonify({"message": "OTP verification failed or expired"}), 400

def register_routes(app):
    app.register_blueprint(auth_bp)
