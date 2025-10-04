from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',       # your MySQL username
    'password': '',       # your MySQL password
    'database': 'expense_db'
}

# Initialize DB: Create table if it doesn't exist
def init_db():
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()
@app.route('/')
def home():
    return render_template('index.html')

# Admin Signup
@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = "Admin"

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                      (name, email, password, role))
            conn.commit()
            flash("Admin created successfully!", "success")
            return redirect(url_for('admin_login'))
        except mysql.connector.errors.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()
    return render_template('admin_signup.html')

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='Admin'", (email, password))
        admin = c.fetchone()
        conn.close()

        if admin:
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('admin_login.html')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return f"Welcome Admin {session['admin_name']}! This is the dashboard."



@app.route('/manager_signup', methods=['GET', 'POST'])
def manager_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = "Manager"

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('manager_signup'))

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                      (name, email, password, role))
            conn.commit()
            flash("Manager created successfully!", "success")
            return redirect(url_for('manager_login'))
        except mysql.connector.errors.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()
    return render_template('manager_signup.html')


@app.route('/manager_login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='Manager'", (email, password))
        manager = c.fetchone()
        conn.close()

        if manager:
            session['manager_id'] = manager['id']
            session['manager_name'] = manager['name']
            return redirect(url_for('manager_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('manager_login.html')


@app.route('/manager_dashboard')
def manager_dashboard():
    if 'manager_id' not in session:
        return redirect(url_for('manager_login'))
    return f"Welcome Manager {session['manager_name']}! This is the dashboard."


# ------------------- Employee -------------------
@app.route('/employee_signup', methods=['GET', 'POST'])
def employee_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = "Employee"

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('employee_signup'))

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                      (name, email, password, role))
            conn.commit()
            flash("Employee created successfully!", "success")
            return redirect(url_for('employee_login'))
        except mysql.connector.errors.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()
    return render_template('employee_signup.html')


@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='Employee'", (email, password))
        employee = c.fetchone()
        conn.close()

        if employee:
            session['employee_id'] = employee['id']
            session['employee_name'] = employee['name']
            return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('employee_login.html')


@app.route('/employee_dashboard')
def employee_dashboard():
    if 'employee_id' not in session:
        return redirect(url_for('employee_login'))
    return f"Welcome Employee {session['employee_name']}! This is the dashboard."



# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
