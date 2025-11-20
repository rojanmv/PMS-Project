from flask import Flask
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
#Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///payroll_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

#model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    basic_pay = db.Column(db.Integer)
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    present_days = db.Column(db.Integer)

    employee = db.relationship("Employee")

#login
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

#ROUTES
@app.route("/")
def home():
    return "Welcome to PayRoll Management System"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['username']
        pwd = request.form['password']

        # hash password
        hashed_pwd = generate_password_hash(pwd)

        # create admin/user
        new_user = Admin(username=uname, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect("/dashboard")
    return render_template("login.html")

# DASHBOARD PAGE
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/employees")
def employees_page():
    employees = Employee.query.all()
    return render_template("employees.html", employees=employees)

@app.route("/add_employee", methods=["POST"])
def add_employee():
    e = Employee(
        name=request.form['name'],
        designation=request.form['designation'],
        basic_pay=request.form['basic_pay']
    )
    db.session.add(e)
    db.session.commit()
    return redirect("/employees")
def calculate_salary(basic, present):
    per_day = basic / 26
    return round(per_day * present)


@app.route("/payroll", methods=["GET", "POST"])
def payroll():
    employees = Employee.query.all()

    if request.method == "POST":
        emp_id = request.form['emp_id']

        # Fetch attendance record
        att = Attendance.query.filter_by(employee_id=emp_id).first()

        present_days = att.present_days if att else 0

        emp = Employee.query.get(emp_id)
        basic = emp.basic_pay

        salary = round((basic / 26) * present_days, 2)

        return render_template(
            "payroll.html",
            employees=employees,
            salary=salary,
            present_days=present_days,
            selected_employee=emp
        )

    return render_template("payroll.html", employees=employees)

#pdf payslip generation
from reportlab.pdfgen import canvas
from flask import send_file
import io

@app.route("/payslip/<int:emp_id>/<int:present_days>")
def generate_payslip(emp_id, present_days):
    emp = Employee.query.get(emp_id)

    basic = emp.basic_pay
    salary = round((basic / 30) * present_days, 2)

    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    p = canvas.Canvas(pdf_buffer)

    # PDF Content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "PAYSLIP")

    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Employee Name: {emp.name}")
    p.drawString(50, 740, f"Designation: {emp.designation}")
    p.drawString(50, 720, f"Basic Pay: ₹{emp.basic_pay}")

    p.drawString(50, 690, f"Present Days: {present_days}")
    p.drawString(50, 670, f"Calculated Salary: ₹{salary}")

    p.drawString(50, 640, "Status: Generated Automatically")
    p.drawString(50, 620, "Signature: ______________________")

    p.showPage()
    p.save()

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Payslip_{emp.name}.pdf",
        mimetype='application/pdf'
    )

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    employees = Employee.query.all()

    if request.method == "POST":
        emp_id = request.form['emp_id']
        days = int(request.form['present_days'])

        att = Attendance(employee_id=emp_id, present_days=days)
        db.session.add(att)
        db.session.commit()

        return redirect("/attendance")

    all_att = Attendance.query.all()
    return render_template("attendance.html", employees=employees, attendance=all_att)


#RUN
if __name__ == "__main__":
    app.run(debug=True)