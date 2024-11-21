def register_routes(app):
    from .auth import auth_bp
    from .users import user_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')

