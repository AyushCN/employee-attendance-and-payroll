"""
Flask web application for Employee Payroll & Attendance Management System.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from payroll import PayrollSystem, Employee, Department

app = Flask(__name__)
app.secret_key = "payroll-secret-key-change-in-production"

# Global payroll instance
payroll = PayrollSystem(total_working_days=22, csv_file="employees.csv")


# ------------------------- Dashboard -------------------------

@app.route("/")
def index():
    summary = payroll.get_payroll_summary()
    dept_summary = payroll.get_department_summary()
    return render_template(
        "index.html",
        total_employees=len(payroll.employees),
        total_net=summary["totals"].get("net_salary", 0),
        total_gross=summary["totals"].get("gross_salary", 0),
        departments=len(dept_summary),
        total_ot=summary["totals"].get("overtime_pay", 0),
    )


# ------------------------- Employees -------------------------

@app.route("/employees")
def employees():
    emps = payroll.get_all_employees()
    return render_template("employees.html", employees=emps)


@app.route("/employees/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        try:
            emp_id = request.form["emp_id"].strip()
            emp_name = request.form["emp_name"].strip()
            dept_id = request.form["dept_id"].strip()
            dept_name = request.form["dept_name"].strip()
            basic_salary = float(request.form["basic_salary"])
            overtime_rate = float(request.form.get("overtime_rate") or 25.0)
            days_present = int(request.form.get("days_present") or 0)
            overtime_hours = float(request.form.get("overtime_hours") or 0.0)

            dept = Department(dept_id=dept_id, dept_name=dept_name)
            emp = Employee(
                emp_id=emp_id,
                emp_name=emp_name,
                department=dept,
                basic_salary=basic_salary,
                overtime_rate_per_hour=overtime_rate,
                days_present=days_present,
                overtime_hours=overtime_hours,
            )

            if payroll.add_employee(emp):
                payroll.save_to_csv()
                flash(f"Employee '{emp_name}' added successfully.", "success")
            else:
                flash(f"Employee ID '{emp_id}' already exists.", "danger")
        except (ValueError, KeyError) as e:
            flash(f"Invalid input: {e}", "danger")

        return redirect(url_for("employees"))

    return render_template("add_employee.html")


@app.route("/employees/edit/<emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    emp = payroll.get_employee(emp_id)
    if not emp:
        flash(f"Employee ID '{emp_id}' not found.", "danger")
        return redirect(url_for("employees"))

    if request.method == "POST":
        try:
            payroll.update_employee(
                emp_id,
                emp_name=request.form.get("emp_name", "").strip(),
                dept_id=request.form.get("dept_id", "").strip(),
                dept_name=request.form.get("dept_name", "").strip(),
                basic_salary=float(request.form["basic_salary"]) if request.form.get("basic_salary") else None,
                overtime_rate_per_hour=float(request.form["overtime_rate"]) if request.form.get("overtime_rate") else None,
                days_present=int(request.form["days_present"]) if request.form.get("days_present") else None,
                overtime_hours=float(request.form["overtime_hours"]) if request.form.get("overtime_hours") else None,
            )
            payroll.save_to_csv()
            flash(f"Employee '{emp_id}' updated successfully.", "success")
            return redirect(url_for("employees"))
        except ValueError as e:
            flash(f"Invalid input: {e}", "danger")

    return render_template("edit_employee.html", emp=emp)


@app.route("/employees/delete/<emp_id>", methods=["POST"])
def delete_employee(emp_id):
    if payroll.delete_employee(emp_id):
        payroll.save_to_csv()
        flash(f"Employee '{emp_id}' deleted.", "success")
    else:
        flash(f"Employee ID '{emp_id}' not found.", "danger")
    return redirect(url_for("employees"))


# ------------------------- Attendance -------------------------

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if request.method == "POST":
        try:
            emp_id = request.form["emp_id"].strip()
            days = int(request.form["days_present"])
            ot_hours = float(request.form.get("overtime_hours") or 0.0)

            if days < 0 or days > payroll.total_working_days:
                flash(f"Days present must be between 0 and {payroll.total_working_days}.", "danger")
            elif payroll.mark_attendance_and_overtime(emp_id, days, ot_hours):
                payroll.save_to_csv()
                flash(f"Attendance updated for '{emp_id}'.", "success")
            else:
                flash(f"Employee ID '{emp_id}' not found.", "danger")
        except (ValueError, KeyError) as e:
            flash(f"Invalid input: {e}", "danger")
        return redirect(url_for("attendance"))

    return render_template(
        "attendance.html",
        employees=payroll.get_all_employees(),
        total_working_days=payroll.total_working_days,
    )


# ------------------------- Payslip & Reports -------------------------

@app.route("/payslip/<emp_id>")
def payslip(emp_id):
    slip = payroll.get_payslip(emp_id)
    if not slip:
        flash(f"Employee ID '{emp_id}' not found.", "danger")
        return redirect(url_for("employees"))
    return render_template("payslip.html", slip=slip, total_working_days=payroll.total_working_days)


@app.route("/payroll-summary")
def payroll_summary():
    summary = payroll.get_payroll_summary()
    return render_template("payroll_summary.html", summary=summary)


@app.route("/department-summary")
def department_summary():
    depts = payroll.get_department_summary()
    return render_template("department_summary.html", departments=depts)


# ------------------------- Save / Utility -------------------------

@app.route("/save")
def save_data():
    if payroll.save_to_csv():
        flash("Data saved to CSV successfully.", "success")
    else:
        flash("Error saving data to CSV.", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
