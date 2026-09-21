"""
Analytics engine implementing:
1. Attendance percentage
2. Overtime pay
3. Final salary
4. Below-threshold detection
5. Comprehensive summary report
"""

from typing import Dict, List
from payroll import PayrollSystem


class PayrollAnalytics:
    def __init__(self, payroll: PayrollSystem, attendance_threshold: float = 75.0):
        self.payroll = payroll
        self.attendance_threshold = attendance_threshold

    # ---------- 1. Attendance Percentage ----------
    def calculate_attendance_percentage(self, emp_id: str) -> Dict:
        emp = self.payroll.get_employee(emp_id)
        if not emp:
            return {"error": f"Employee '{emp_id}' not found."}
        total = self.payroll.total_working_days
        pct = (emp.days_present / total) * 100 if total > 0 else 0.0
        return {
            "emp_id": emp.emp_id,
            "emp_name": emp.emp_name,
            "days_present": emp.days_present,
            "total_working_days": total,
            "attendance_pct": round(pct, 2),
            "status": self._attendance_status(pct),
        }

    def calculate_all_attendance(self) -> List[Dict]:
        return [self.calculate_attendance_percentage(eid) for eid in self.payroll.employees]

    # ---------- 2. Overtime Pay ----------
    def calculate_overtime_pay(self, emp_id: str) -> Dict:
        emp = self.payroll.get_employee(emp_id)
        if not emp:
            return {"error": f"Employee '{emp_id}' not found."}
        ot_pay = emp.overtime_hours * emp.overtime_rate_per_hour
        return {
            "emp_id": emp.emp_id,
            "emp_name": emp.emp_name,
            "overtime_hours": emp.overtime_hours,
            "overtime_rate": emp.overtime_rate_per_hour,
            "overtime_pay": round(ot_pay, 2),
        }

    def calculate_all_overtime(self) -> List[Dict]:
        return [self.calculate_overtime_pay(eid) for eid in self.payroll.employees]

    # ---------- 3. Final Salary ----------
    def calculate_final_salary(self, emp_id: str) -> Dict:
        emp = self.payroll.get_employee(emp_id)
        if not emp:
            return {"error": f"Employee '{emp_id}' not found."}
        d = emp.calculate_salary_details(self.payroll.total_working_days)
        d.update({
            "emp_id": emp.emp_id,
            "emp_name": emp.emp_name,
            "dept_name": emp.department.dept_name,
        })
        return d

    def calculate_all_final_salaries(self) -> List[Dict]:
        return [self.calculate_final_salary(eid) for eid in self.payroll.employees]

    # ---------- 4. Below Attendance Threshold ----------
    def get_below_threshold_employees(self, threshold: float = None) -> List[Dict]:
        threshold = threshold if threshold is not None else self.attendance_threshold
        total = self.payroll.total_working_days
        flagged = []
        for emp in self.payroll.employees.values():
            pct = (emp.days_present / total) * 100 if total > 0 else 0.0
            if pct < threshold:
                flagged.append({
                    "emp_id": emp.emp_id,
                    "emp_name": emp.emp_name,
                    "dept_name": emp.department.dept_name,
                    "days_present": emp.days_present,
                    "total_working_days": total,
                    "attendance_pct": round(pct, 2),
                    "shortfall_pct": round(threshold - pct, 2),
                    "status": self._attendance_status(pct),
                })
        flagged.sort(key=lambda x: x["attendance_pct"])
        return flagged

    # ---------- 5. Summary Report ----------
    def generate_summary_report(self) -> Dict:
        employees = list(self.payroll.employees.values())
        if not employees:
            return {"empty": True, "message": "No employee records available."}

        total = self.payroll.total_working_days
        totals = {
            "fixed_basic": 0.0, "earned_basic": 0.0, "overtime_pay": 0.0,
            "gross_salary": 0.0, "tax_deduction": 0.0, "pf_deduction": 0.0,
            "total_deductions": 0.0, "net_salary": 0.0,
            "overtime_hours": 0.0, "days_present": 0,
        }

        attendance_records, ot_records = [], []
        for emp in employees:
            s = emp.calculate_salary_details(total)
            totals["fixed_basic"] += s["fixed_basic"]
            totals["earned_basic"] += s["earned_basic"]
            totals["overtime_pay"] += s["overtime_pay"]
            totals["gross_salary"] += s["gross_salary"]
            totals["tax_deduction"] += s["tax_deduction"]
            totals["pf_deduction"] += s["pf_deduction"]
            totals["total_deductions"] += s["total_deductions"]
            totals["net_salary"] += s["net_salary"]
            totals["overtime_hours"] += emp.overtime_hours
            totals["days_present"] += emp.days_present

            attendance_records.append({
                "emp_id": emp.emp_id,
                "emp_name": emp.emp_name,
                "attendance_pct": s["attendance_pct"],
            })
            ot_records.append({
                "emp_id": emp.emp_id,
                "emp_name": emp.emp_name,
                "overtime_hours": emp.overtime_hours,
                "overtime_pay": s["overtime_pay"],
            })

        totals = {k: round(v, 2) for k, v in totals.items()}

        attn_values = [r["attendance_pct"] for r in attendance_records]
        best = max(attendance_records, key=lambda x: x["attendance_pct"])
        worst = min(attendance_records, key=lambda x: x["attendance_pct"])

        top_ot = sorted(ot_records, key=lambda x: x["overtime_pay"], reverse=True)[:5]
        below = self.get_below_threshold_employees()
        depts = self.payroll.get_department_summary()

        return {
            "empty": False,
            "total_employees": len(employees),
            "total_working_days": total,
            "attendance_threshold": self.attendance_threshold,
            "totals": totals,
            "attendance": {
                "average": round(sum(attn_values) / len(attn_values), 2),
                "best": best,
                "worst": worst,
                "below_threshold_count": len(below),
            },
            "top_overtime_earners": top_ot,
            "below_threshold": below,
            "departments": depts,
        }

    @staticmethod
    def _attendance_status(pct: float) -> str:
        if pct >= 95: return "Excellent"
        if pct >= 85: return "Good"
        if pct >= 75: return "Satisfactory"
        if pct >= 60: return "Warning"
        return "Critical"
