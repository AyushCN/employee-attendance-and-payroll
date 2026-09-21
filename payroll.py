"""
Core payroll business logic: Department, Employee, PayrollSystem.
Handles salary calculations and CSV persistence.
"""

import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Department:
    dept_id: str
    dept_name: str


class Employee:
    def __init__(
        self,
        emp_id: str,
        emp_name: str,
        department: Department,
        basic_salary: float,
        overtime_rate_per_hour: float = 25.0,
        days_present: int = 0,
        overtime_hours: float = 0.0,
    ):
        self.emp_id = emp_id
        self.emp_name = emp_name
        self.department = department
        self.basic_salary = basic_salary
        self.overtime_rate_per_hour = overtime_rate_per_hour
        self.days_present = days_present
        self.overtime_hours = overtime_hours

    def calculate_salary_details(
        self,
        total_working_days: int = 22,
        tax_rate: float = 0.10,
        pf_rate: float = 0.05,
    ) -> Dict[str, float]:
        """Compute attendance %, earned basic, OT pay, deductions, net salary."""
        attendance_pct = (
            (self.days_present / total_working_days) * 100
            if total_working_days > 0 else 0.0
        )
        daily_rate = (
            self.basic_salary / total_working_days
            if total_working_days > 0 else 0.0
        )
        earned_basic = daily_rate * self.days_present
        overtime_pay = self.overtime_hours * self.overtime_rate_per_hour
        gross_salary = earned_basic + overtime_pay

        tax_deduction = gross_salary * tax_rate
        pf_deduction = earned_basic * pf_rate
        total_deductions = tax_deduction + pf_deduction
        net_salary = gross_salary - total_deductions

        return {
            "fixed_basic": self.basic_salary,
            "days_present": self.days_present,
            "attendance_pct": round(attendance_pct, 2),
            "earned_basic": round(earned_basic, 2),
            "overtime_hours": self.overtime_hours,
            "overtime_rate": self.overtime_rate_per_hour,
            "overtime_pay": round(overtime_pay, 2),
            "gross_salary": round(gross_salary, 2),
            "tax_deduction": round(tax_deduction, 2),
            "pf_deduction": round(pf_deduction, 2),
            "total_deductions": round(total_deductions, 2),
            "net_salary": round(net_salary, 2),
        }

    def to_dict(self) -> Dict:
        return {
            "emp_id": self.emp_id,
            "emp_name": self.emp_name,
            "dept_id": self.department.dept_id,
            "dept_name": self.department.dept_name,
            "basic_salary": self.basic_salary,
            "overtime_rate": self.overtime_rate_per_hour,
            "days_present": self.days_present,
            "overtime_hours": self.overtime_hours,
        }


class PayrollSystem:
    def __init__(self, total_working_days: int = 22, csv_file: str = "employees.csv"):
        self.employees: Dict[str, Employee] = {}
        self.total_working_days = total_working_days
        self.csv_file = csv_file
        self.load_from_csv()

    # ------------------ CSV Persistence ------------------

    def save_to_csv(self) -> bool:
        fieldnames = [
            "emp_id", "emp_name", "dept_id", "dept_name",
            "basic_salary", "overtime_rate", "days_present", "overtime_hours",
        ]
        try:
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for emp in self.employees.values():
                    writer.writerow(emp.to_dict())
            return True
        except Exception as e:
            print(f"[-] Error saving to CSV: {e}")
            return False

    def load_from_csv(self) -> None:
        if not os.path.exists(self.csv_file):
            return
        try:
            with open(self.csv_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dept = Department(dept_id=row["dept_id"], dept_name=row["dept_name"])
                    emp = Employee(
                        emp_id=row["emp_id"],
                        emp_name=row["emp_name"],
                        department=dept,
                        basic_salary=float(row["basic_salary"]),
                        overtime_rate_per_hour=float(row["overtime_rate"]),
                        days_present=int(row["days_present"]),
                        overtime_hours=float(row["overtime_hours"]),
                    )
                    self.employees[emp.emp_id] = emp
        except Exception as e:
            print(f"[-] Error loading CSV data: {e}")

    # ------------------ CRUD ------------------

    def add_employee(self, emp: Employee) -> bool:
        if emp.emp_id in self.employees:
            return False
        self.employees[emp.emp_id] = emp
        return True

    def get_employee(self, emp_id: str) -> Optional[Employee]:
        return self.employees.get(emp_id)

    def update_employee(self, emp_id: str, **kwargs) -> bool:
        emp = self.employees.get(emp_id)
        if not emp:
            return False
        if kwargs.get("emp_name"):
            emp.emp_name = kwargs["emp_name"]
        if kwargs.get("dept_id"):
            emp.department.dept_id = kwargs["dept_id"]
        if kwargs.get("dept_name"):
            emp.department.dept_name = kwargs["dept_name"]
        if kwargs.get("basic_salary") is not None:
            emp.basic_salary = float(kwargs["basic_salary"])
        if kwargs.get("overtime_rate_per_hour") is not None:
            emp.overtime_rate_per_hour = float(kwargs["overtime_rate_per_hour"])
        if kwargs.get("days_present") is not None:
            emp.days_present = int(kwargs["days_present"])
        if kwargs.get("overtime_hours") is not None:
            emp.overtime_hours = float(kwargs["overtime_hours"])
        return True

    def delete_employee(self, emp_id: str) -> bool:
        if emp_id in self.employees:
            del self.employees[emp_id]
            return True
        return False

    def mark_attendance_and_overtime(self, emp_id: str, days: int, ot_hours: float) -> bool:
        emp = self.employees.get(emp_id)
        if not emp:
            return False
        emp.days_present = days
        emp.overtime_hours = ot_hours
        return True

    # ------------------ Reports ------------------

    def get_payslip(self, emp_id: str) -> Optional[Dict]:
        emp = self.employees.get(emp_id)
        if not emp:
            return None
        s = emp.calculate_salary_details(self.total_working_days)
        s.update({
            "emp_id": emp.emp_id,
            "emp_name": emp.emp_name,
            "dept_id": emp.department.dept_id,
            "dept_name": emp.department.dept_name,
        })
        return s

    def get_payroll_summary(self) -> Dict:
        if not self.employees:
            return {"employees": [], "totals": {}}

        rows = []
        tot = {k: 0.0 for k in
               ["fixed_basic", "earned_basic", "overtime_pay",
                "gross_salary", "total_deductions", "net_salary"]}

        for emp in self.employees.values():
            s = emp.calculate_salary_details(self.total_working_days)
            for k in tot:
                tot[k] += s[k]
            rows.append({
                "emp_id": emp.emp_id,
                "emp_name": emp.emp_name,
                "dept_name": emp.department.dept_name,
                "attendance_pct": s["attendance_pct"],
                "fixed_basic": s["fixed_basic"],
                "earned_basic": s["earned_basic"],
                "overtime_pay": s["overtime_pay"],
                "gross_salary": s["gross_salary"],
                "total_deductions": s["total_deductions"],
                "net_salary": s["net_salary"],
            })

        totals = {k: round(v, 2) for k, v in tot.items()}
        return {"employees": rows, "totals": totals}

    def get_department_summary(self) -> List[Dict]:
        if not self.employees:
            return []

        dept_data: Dict[str, Dict[str, float]] = {}
        for emp in self.employees.values():
            d = emp.department.dept_name
            s = emp.calculate_salary_details(self.total_working_days)
            if d not in dept_data:
                dept_data[d] = {"count": 0, "attn": 0.0, "ot": 0.0, "gross": 0.0, "net": 0.0}
            dept_data[d]["count"] += 1
            dept_data[d]["attn"] += s["attendance_pct"]
            dept_data[d]["ot"] += s["overtime_pay"]
            dept_data[d]["gross"] += s["gross_salary"]
            dept_data[d]["net"] += s["net_salary"]

        return [
            {
                "dept_name": d,
                "count": m["count"],
                "avg_attendance": round(m["attn"] / m["count"], 2),
                "total_overtime_pay": round(m["ot"], 2),
                "total_gross": round(m["gross"], 2),
                "total_net": round(m["net"], 2),
            }
            for d, m in dept_data.items()
        ]

    def get_all_employees(self) -> List[Dict]:
        return [emp.to_dict() for emp in self.employees.values()]
