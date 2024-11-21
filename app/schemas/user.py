from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    email = fields.Email(required=True)
    phone = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    password = fields.Str(required=True, validate=validate.Length(min=8))
