from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import requests




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


def load_countries():
    try:
        url = "https://restcountries.com/v3.1/all?fields=name,currencies"
        response = requests.get(url)
        data = response.json()

        countries = []
        for c in data:
            name = c.get("name", {}).get("common", "")
            currencies = c.get("currencies", {})
            if currencies:
                for code in currencies.keys():
                    countries.append({
                        "country": name,
                        "currency": code
                    })
        return sorted(countries, key=lambda x: x["country"])
    except Exception as e:
        print("Error loading countries:", e)
        return []

# Global variable
countries = load_countries()

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
        country = request.form['country']
        currency = request.form['currency']
        role = "Admin"

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (name, email, password, role, country, currency) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, password, role, country, currency)
            )
            conn.commit()
            flash("Admin created successfully!", "success")
            return redirect(url_for('admin_login'))
        except mysql.connector.errors.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()
    return render_template('admin_signup.html', countries=countries)

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
# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = mysql.connector.connect(**db_config)
    c = conn.cursor(dictionary=True)

    # Count users by role
    c.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
    stats = c.fetchall()

    # Fetch all users
    c.execute("SELECT id, name, email, role FROM users")
    users = c.fetchall()

    # Fetch all expenses with employee and manager names
    c.execute("""
        SELECT e.*, u.name as employee_name, m.name as manager_name 
        FROM expenses e 
        JOIN users u ON e.employee_id = u.id 
        LEFT JOIN users m ON e.manager_id = m.id 
        ORDER BY e.created_at DESC
    """)
    expenses = c.fetchall()

    conn.close()

    return render_template(
        'admin_dashboard.html',
        admin_name=session['admin_name'],
        stats=stats,
        users=users,
        expenses=expenses
    )
@app.route('/admin_approve_expense/<int:expense_id>')
def admin_approve_expense(expense_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("UPDATE expenses SET status='Approved' WHERE id=%s", (expense_id,))
    conn.commit()
    conn.close()
    flash("Expense approved by admin!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_deny_expense/<int:expense_id>')
def admin_deny_expense(expense_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("UPDATE expenses SET status='Denied' WHERE id=%s", (expense_id,))
    conn.commit()
    conn.close()
    flash("Expense denied by admin!", "danger")
    return redirect(url_for('admin_dashboard'))


@app.route('/manager_signup', methods=['GET', 'POST'])
def manager_signup():
    import requests  # ensure requests is imported at the top of your file
    countries = []

    # Fetch country & currency list from API
    try:
        response = requests.get("https://restcountries.com/v3.1/all?fields=name,currencies")
        if response.status_code == 200:
            data = response.json()
            for c in data:
                country_name = c['name']['common']
                currency = list(c.get('currencies', {}).keys())[0] if c.get('currencies') else ''
                countries.append({'name': country_name, 'currency': currency})
        else:
            flash("Could not fetch country data.", "danger")
    except Exception as e:
        flash("Could not fetch country data.", "danger")

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        country_currency = request.form.get('country')  # Format: "Country - Currency"

        if not country_currency:
            flash("Please select a country.", "danger")
            return redirect(url_for('manager_signup'))

        country, currency = country_currency.split(" - ")
        role = "Manager"

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('manager_signup'))

        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (name, email, password, role, country, currency) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, password, role, country, currency)
            )
            conn.commit()
            flash("Manager created successfully!", "success")
            return redirect(url_for('manager_login'))
        except mysql.connector.errors.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()

    return render_template('manager_signup.html', countries=countries)

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

# Manager Dashboard
@app.route('/manager_dashboard', methods=['GET', 'POST'])
def manager_dashboard():
    if 'manager_id' not in session:
        return redirect(url_for('manager_login'))

    conn = mysql.connector.connect(**db_config)
    c = conn.cursor(dictionary=True)

    # Fetch all employees
    c.execute("SELECT id, name, email FROM users WHERE role='Employee'")
    employees = c.fetchall()

    # Fetch all expenses for employees
    c.execute("SELECT e.*, u.name as employee_name FROM expenses e JOIN users u ON e.employee_id=u.id ORDER BY e.created_at DESC")
    expenses = c.fetchall()
    conn.close()

    return render_template('manager_dashboard.html', manager_name=session['manager_name'], employees=employees, expenses=expenses)

@app.route('/approve_expense/<int:expense_id>')
def approve_expense(expense_id):
    if 'manager_id' not in session:
        return redirect(url_for('manager_login'))
    
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("UPDATE expenses SET status='Approved', manager_id=%s WHERE id=%s",
              (session['manager_id'], expense_id))
    conn.commit()
    conn.close()
    flash("Expense approved!", "success")
    return redirect(url_for('manager_dashboard'))

@app.route('/deny_expense/<int:expense_id>')
def deny_expense(expense_id):
    if 'manager_id' not in session:
        return redirect(url_for('manager_login'))
    
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("UPDATE expenses SET status='Denied', manager_id=%s WHERE id=%s",
              (session['manager_id'], expense_id))
    conn.commit()
    conn.close()
    flash("Expense denied!", "danger")
    return redirect(url_for('manager_dashboard'))

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


@app.route('/employee_dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    if 'employee_id' not in session:
        return redirect(url_for('employee_login'))

    conn = mysql.connector.connect(**db_config)
    c = conn.cursor(dictionary=True)

    if request.method == 'POST':
        description = request.form.get('description')
        amount = request.form.get('amount')
        employee_id = session['employee_id']

        if not description or not amount:
            flash("All fields are required!", "danger")
            return redirect(url_for('employee_dashboard'))

        # Insert expense
        c.execute("INSERT INTO expenses (employee_id, description, amount) VALUES (%s, %s, %s)",
                  (employee_id, description, amount))
        conn.commit()
        flash("Expense added successfully!", "success")

    # Fetch employee's expenses
    c.execute("SELECT * FROM expenses WHERE employee_id=%s ORDER BY created_at DESC", (session['employee_id'],))
    expenses = c.fetchall()
    conn.close()

    return render_template('employee_dashboard.html', employee_name=session['employee_name'], expenses=expenses)


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'employee_id' not in session:
        return redirect(url_for('employee_login'))

    amount = request.form['amount']
    description = request.form['description']
    employee_id = session['employee_id']

    # Assign manager (optional: you can assign automatically or let admin assign)
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("INSERT INTO expenses (employee_id, amount, description) VALUES (%s, %s, %s)",
              (employee_id, amount, description))
    conn.commit()
    conn.close()

    flash("Expense added successfully!", "success")
    return redirect(url_for('employee_dashboard'))


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
