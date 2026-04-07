from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE CONFIG =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))

class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100))
    category = db.Column(db.String(50))
    sales = db.Column(db.Float)
    profit = db.Column(db.Float)
    region = db.Column(db.String(50))
    month = db.Column(db.String(20))

# ================= INIT DB + DEFAULT DATA =================
with app.app_context():
    db.create_all()

    # Insert default data only if table is empty
    if Sales.query.count() == 0:
        sample_data = [
            Sales(product="Laptop", category="Electronics", sales=50000, profit=8000, region="North", month="January"),
            Sales(product="Mobile", category="Electronics", sales=30000, profit=5000, region="South", month="February"),
            Sales(product="Tablet", category="Electronics", sales=20000, profit=3000, region="East", month="March"),
            Sales(product="Shoes", category="Fashion", sales=15000, profit=2000, region="West", month="April"),
            Sales(product="Watch", category="Accessories", sales=12000, profit=1800, region="North", month="May"),
            Sales(product="Bag", category="Fashion", sales=18000, profit=2500, region="South", month="June"),
            Sales(product="Camera", category="Electronics", sales=40000, profit=7000, region="East", month="July"),
            Sales(product="Headphones", category="Electronics", sales=10000, profit=1500, region="West", month="August"),
            Sales(product="Chair", category="Furniture", sales=22000, profit=3500, region="North", month="September"),
            Sales(product="Table", category="Furniture", sales=27000, profit=4000, region="South", month="October"),
        ]
        db.session.bulk_save_objects(sample_data)
        db.session.commit()

# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user'] = user.username
            return redirect('/dashboard')

        flash("Invalid Credentials")

    return render_template('login.html')

# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # ✅ Check if user already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists! Try another.")
            return redirect('/register')

        # ✅ Hash password
        hashed = generate_password_hash(password)

        user = User(username=username, password=hashed)

        db.session.add(user)
        db.session.commit()

        flash("Registered Successfully!")
        return redirect('/')

    return render_template('register.html')

# ================= DASHBOARD =================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/')

    # Add new sales
    if request.method == 'POST':
        sale = Sales(
            product=request.form['product'],
            category=request.form['category'],
            sales=float(request.form['sales']),
            profit=float(request.form['profit']),
            region=request.form['region'],
            month=request.form['month']
        )
        db.session.add(sale)
        db.session.commit()
        flash("Sales Added Successfully!")

    data = Sales.query.all()

    total = len(data)
    revenue = sum([d.sales for d in data])
    avg = revenue / total if total > 0 else 0

    months = [d.month for d in data]
    sales_data = [d.sales for d in data]
    profits = [d.profit for d in data]

    # Aggregations
    region_dict = {}
    product_dict = {}

    for d in data:
        region_dict[d.region] = region_dict.get(d.region, 0) + d.sales
        product_dict[d.product] = product_dict.get(d.product, 0) + d.sales

    return render_template("dashboard.html",
        total=total,
        revenue=round(revenue, 2),
        avg=round(avg, 2),
        months_json=json.dumps(months),
        sales_json=json.dumps(sales_data),
        profit_json=json.dumps(profits),
        regions_json=json.dumps(list(region_dict.keys())),
        region_sales_json=json.dumps(list(region_dict.values())),
        products_json=json.dumps(list(product_dict.keys())),
        product_sales_json=json.dumps(list(product_dict.values()))
    )

# ================= HOME =================
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')

    data = Sales.query.all()

    months = [d.month for d in data]
    sales = [d.sales for d in data]

    product_dict = {}
    for d in data:
        product_dict[d.product] = product_dict.get(d.product, 0) + d.sales

    return render_template("home.html",
        months_json=json.dumps(months),
        sales_json=json.dumps(sales),
        products_json=json.dumps(list(product_dict.keys())),
        product_sales_json=json.dumps(list(product_dict.values()))
    )

# ================= ANALYTICS =================
@app.route('/analytics')
def analytics():
    if 'user' not in session:
        return redirect('/')

    data = Sales.query.all()

    months = [d.month for d in data]
    sales = [d.sales for d in data]

    region_dict = {}
    for d in data:
        region_dict[d.region] = region_dict.get(d.region, 0) + d.sales

    return render_template("analytics.html",
        months_json=json.dumps(months),
        sales_json=json.dumps(sales),
        regions_json=json.dumps(list(region_dict.keys())),
        region_sales_json=json.dumps(list(region_dict.values()))
    )

# ================= REPORTS =================
@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect('/')

    data = Sales.query.all()

    reports = [(d.product, d.category, d.sales, d.profit, d.region, d.month) for d in data]

    return render_template("reports.html", reports=reports)

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)