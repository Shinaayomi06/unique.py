import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-me")

# Initialize Supabase (it is recommended to use environment variables)
url: str = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
    
    try:
        # 1. Supabase Auth registration
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            # 2. Write to profiles table to store username and role
            supabase.table('profiles').insert({
                "id": res.user.id,
                "username": username,
                "role": "member"  # Default is regular member
            }).execute()
            flash("Registration successful, please log in")
        else:
            flash("Registration failed")
    except Exception as e:
        flash(f"Registration error: {str(e)}")
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        # Supabase Auth login
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            session['user_id'] = res.user.id
            session['email'] = res.user.email
            
            # Query role to determine redirect destination
            profile = supabase.table('profiles').select("role, username").eq("id", res.user.id).single().execute()
            if profile.data:
                session['username'] = profile.data.get('username')
                session['role'] = profile.data.get('role')
                
                if profile.data.get('role') == 'admin':
                    return redirect(url_for('admin_panel'))
                else:
                    return redirect(url_for('dashboard'))
        else:
            flash("Login failed")
    except Exception as e:
        flash("Incorrect email or password")
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', username=session.get('username'), role=session.get('role'))

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        return "Access denied: Admin only", 403
    return render_template('dashboard.html', username=session.get('username'), role='admin')

@app.route('/logout')
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)