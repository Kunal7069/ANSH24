import random
import uuid
from datetime import datetime, timedelta
from ..db import db

class OTP(db.Model):
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(36), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    otp = db.Column(db.String(4), nullable=False)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def generate_otp():
        return f"{random.randint(1000, 9999)}"  

    def generate_transaction_id():
        return str(uuid.uuid4())  
