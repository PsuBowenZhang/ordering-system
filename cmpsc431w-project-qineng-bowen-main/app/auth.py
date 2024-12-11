from email_validator import validate_email, EmailNotValidError
from flask import request, flash, redirect, url_for, Blueprint, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user

from app.models import User
from db import con_my_sql

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route("/login", methods=['POST'])
def login_check():
    email = request.form['email'].strip()
    password = request.form['password'].strip()

    # validate email
    try:
        email_info = validate_email(email, check_deliverability=False)
        email = email_info.normalized
    except EmailNotValidError as e:
        flash("Invalid email format.", "danger")
        return redirect(url_for("index.login"))

    # validate password
    if password is None or len(password) < 6:
        flash("Password must contain at least one letter, one number, and be at least 6 characters long.", "danger")
        return redirect(url_for("index.login"))

    # query users table
    sql_check = "SELECT UserID, UserName, Role, Email, Password, IsActive FROM users WHERE email = %s"
    cursor_ans = con_my_sql(sql_check, email)
    user_select = cursor_ans.fetchone()
    cursor_ans.close()
    if user_select is not None and len(user_select) > 0:
        if user_select['IsActive'] == 0:
            flash("User is locked, please contact the administrator.", "danger")
            return redirect(url_for("index.login"))
        if check_password_hash(user_select['Password'], password):  # check password
            user = User.get_user_by_id(user_select['UserID'])
            login_user(user)
            flash("Login successful.", "success")
            role = user_select['Role'].lower()
            return redirect(url_for(f"{role}.index"))
        else:
            flash("Incorrect password.", "danger")
            return redirect(url_for("index.login"))
    else:
        flash("User not found.", "danger")
        return redirect(url_for("index.login"))


@auth_bp.route("/register", methods=['POST'])
def register_check():
    username = request.form['username'].strip()
    email = request.form['email'].strip()
    password = request.form['password'].strip()
    confirm_password = request.form['confirmPassword'].strip()

    # Username validation
    if len(username) < 5:
        flash("Username must be at least 5 characters long.", "danger")
        return redirect(url_for("register"))

    # Email validation
    try:
        email_info = validate_email(email, check_deliverability=False)
        email = email_info.normalized
    except EmailNotValidError as e:
        flash("Invalid email format.", "danger")
        return redirect(url_for("index.register"))

    # Password validation
    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "danger")
        return redirect(url_for("index.register"))

    # Confirm password validation
    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("index.register"))

    # Check if email already exists
    sql_check = "SELECT COUNT(*) AS con FROM users WHERE email = %s"
    cursor_ans = con_my_sql(sql_check, email)
    if cursor_ans.fetchone()['con'] > 0:
        flash("Email already registered.", "danger")
        return redirect(url_for("index.register"))
    cursor_ans.close()
    # Hash password and save to database
    hashed_password = generate_password_hash(password)
    sql_insert = "INSERT INTO users (UserName, Role, Email, Password) VALUES (%s, 'Customer', %s, %s)"
    con_my_sql(sql_insert, (username, email, hashed_password))

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("index.login"))


@auth_bp.route("/api_login", methods=['POST'])
def api_login():
    email = request.form['email'].strip()
    password = request.form['password'].strip()

    # validate email
    try:
        email_info = validate_email(email, check_deliverability=False)
        email = email_info.normalized
    except EmailNotValidError as e:
        return jsonify({"code": 200, "message": "Invalid email format."}), 200

    # validate password
    if password is None or len(password) < 6:
        return jsonify({"code": 200, "message": "Password must contain at least one letter, one number, and be at least 6 characters long."}), 200

    # query users table
    sql_check = "SELECT UserID, UserName, Role, Email, Password, IsActive FROM users WHERE email = %s"
    cursor_ans = con_my_sql(sql_check, email)
    user_select = cursor_ans.fetchone()
    cursor_ans.close()
    if user_select is not None and len(user_select) > 0:
        if user_select['IsActive'] == 0:
            return jsonify({"code": 200, "message": "User is locked, please contact the administrator."}), 200
        if check_password_hash(user_select['Password'], password):  # check password
            user = User.get_user_by_id(user_select['UserID'])
            login_user(user)
            return jsonify({"code": 200, "message": "Login successful!"}), 200
        else:
            return jsonify({"code": 200, "message": "Incorrect password."}), 200
    else:
        return jsonify({"code": 200, "message": "User not found."}), 200