from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from database.db import get_db
from utils.auth import login_required, role_required, hash_password, check_password
from utils.email_service import send_password_reset
from utils.financial import calculate_monthly_interest, get_group_financial_summary, generate_pdf_statement
from config import Config
import datetime

app = Flask(__name__)
app.config.from_object(Config)

bcrypt = Bcrypt(app)
mail = Mail(app)
db = get_db()

# Home route
@app.route('/')
def index():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({"email": email})
        
        if user and check_password(password, user['password']):
            session['user'] = user
            flash('Login successful!', 'success')
            return redirect(url_for('member_dashboard'))
        else:
            flash('Login failed. Please check your credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email and password:  # Ensure both fields are filled
            hashed_password = hash_password(password)
            user_data = {
                "email": email,
                "password": hashed_password,
                "role": "member",  # Default role; you can change this logic as needed
                "created_at": datetime.datetime.now()
            }
            db.users.insert_one(user_data)
            flash('Signup successful! You can now login.', 'success')
            return redirect(url_for('login'))
        
        flash('Signup failed. Please provide valid information.', 'danger')
        return render_template('signup.html')  # Render signup form again if failed

    return render_template('signup.html')  # Render the signup page for GET requests

# Forgot password route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # Password reset logic
    pass

# Admin Dashboard - Full Access
@app.route('/dashboard/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    users = list(db.users.find())
    transactions = list(db.transactions.find())
    loans = list(db.loans.find())
    return render_template('dashboard/admin_dashboard.html', users=users, transactions=transactions, loans=loans)

# Chairman Dashboard - View Only Access
@app.route('/dashboard/chairman')
@login_required
@role_required('chairman')
def chairman_dashboard():
    total_funds = db.funds.find_one({}, {"total_funds": 1}).get("total_funds", 0)
    contributions = list(db.transactions.find({"type": "deposit"}))
    loans = list(db.loans.find())
    return render_template('dashboard/chairman_dashboard.html', total_funds=total_funds, contributions=contributions, loans=loans)

# Treasurer Dashboard - Manage Deposits and Loans
@app.route('/dashboard/treasurer')
@login_required
@role_required('treasurer')
def treasurer_dashboard():
    deposits = list(db.transactions.find({"type": "deposit"}))
    pending_loans = list(db.loans.find({"status": "pending"}))
    return render_template('dashboard/treasurer_dashboard.html', deposits=deposits, pending_loans=pending_loans)

# Member Dashboard - View Balance and Loan Details, Make Deposits
@app.route('/dashboard/member')
@login_required
@role_required('member')
def member_dashboard():
    user_id = session['user']['_id']
    balance = sum([txn['amount'] for txn in db.transactions.find({"member_id": user_id, "type": "deposit"})])
    loans = list(db.loans.find({"member_id": user_id}))
    return render_template('dashboard/member_dashboard.html', balance=balance, loans=loans)

# M-Pesa deposit webhook simulation
@app.route('/mpesa/deposit', methods=['POST'])
def mpesa_deposit():
    data = request.json
    amount = data.get("amount")
    member_id = data.get("member_id")
    
    if amount and member_id:
        transaction = {
            "member_id": member_id,
            "amount": amount,
            "type": "deposit",
            "timestamp": datetime.datetime.now()
        }
        db.transactions.insert_one(transaction)
        db.funds.update_one({}, {'$inc': {'total_funds': amount}}, upsert=True)
        return jsonify({"status": "success", "message": "Deposit recorded"}), 200
    return jsonify({"status": "error", "message": "Invalid data"}), 400

# Add new loan route
@app.route('/loans/add', methods=['POST'])
def add_loan():
    data = request.json
    principal = data.get("principal")
    member_id = data.get("member_id")

    if principal and member_id:
        loan = {
            "member_id": member_id,
            "principal": principal,
            "interest_rate": 0.10,
            "monthly_interest": principal * 0.10,
            "total_interest": 0,
            "start_date": datetime.datetime.now(),
            "status": "active"
        }
        db.loans.insert_one(loan)
        return jsonify({"status": "success", "message": "Loan created"}), 200
    return jsonify({"status": "error", "message": "Invalid data"}), 400

# Financial summary route
@app.route('/financial_summary', methods=['GET'])
@login_required
def financial_summary():
    summary = get_group_financial_summary()
    return render_template('financial_summary.html', summary=summary)

# Generate PDF statement route
@app.route('/generate_statement', methods=['GET'])
def generate_statement():
    member_id = request.args.get("member_id")
    pdf_path = generate_pdf_statement(member_id)
    return redirect(url_for('static', filename=pdf_path))

if __name__ == '__main__':
    app.run(debug=True)
