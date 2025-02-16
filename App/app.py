from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Ensure Supabase credentials are set
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found. Check your .env file.")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session key

@app.route('/')
def landing_register():
    return render_template('landing_register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    if not username or not password or not confirm_password:
        flash('All fields are required!', 'warning')
        return redirect(url_for('landing_register'))

    if password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return redirect(url_for('landing_register'))

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        # Check if username exists
        existing_user = supabase.table("Users").select("username").eq("username", username).execute()
        if existing_user.data:
            flash('Username already taken!', 'danger')
            return redirect(url_for('landing_register'))

        # Insert user into Supabase
        response = supabase.table("Users").insert({"username": username, "password": hashed_password}).execute()

        if response.data:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Try again.', 'danger')

    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')

    return redirect(url_for('landing_register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('All fields are required!', 'warning')
            return redirect(url_for('login'))

        try:
            # Fetch user from Supabase
            user = supabase.table("Users").select("password").eq("username", username).execute()

            if user.data:
                stored_password = user.data[0]['password']
                if check_password_hash(stored_password, password):
                    session['username'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Invalid username or password!', 'danger')
            else:
                flash('User not found!', 'danger')

        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')

    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
