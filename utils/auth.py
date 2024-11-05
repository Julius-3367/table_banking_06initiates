from functools import wraps
from flask import redirect, url_for, session, flash
from flask_bcrypt import Bcrypt

# Initialize Bcrypt outside of app context
bcrypt = Bcrypt()

# Password hashing and verification functions
def hash_password(password):
    from app import app  # Import app only within this function to avoid circular dependency
    bcrypt.init_app(app)
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    from app import app  # Import app only within this function to avoid circular dependency
    bcrypt.init_app(app)
    return bcrypt.check_password_hash(hashed_password, password)

# Decorator for login requirement
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator for role-based access control
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session or session['user']['role'] != role:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
