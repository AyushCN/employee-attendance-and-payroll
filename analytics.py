"""
Advanced payroll analytics:
1. Attendance percentage calculation
2. Overtime pay calculation
3. Final salary calculation
4. Identify employees below attendance threshold
5. Generate summary reports
"""

from typing import Dict, List
from payroll import PayrollSystem, Employee


class PayrollAnalytics:
    """Provides analytical methods over a PayrollSystem instance."""

    def __init__(self, payroll: PayrollSystem, attendance_threshold: float = 75.0):
        self.payroll = payroll
        self.attendance_threshold = attendance_threshold  # percent

    # ------------------------------------------------------------------
    # 1. ATTENDANCE PERCENTAGE
    # ------------------------------------------------------------------
    def calculate_attendance_percentage(self, emp_id: str) -> Dict:
        """
        Returns attendance % for a single employee.
        Formula: (days_present / total_working_days) * 100
        """
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
        """Returns attendance % for every employee."""
        return [self.calculate_attendance_percentage(eid) for eid in self.payroll.employees]

    # ------------------------------------------------------------------
    # 2. OVERTIME PAY
    # ------------------------------------------------------------------
    def calculate_overtime_pay(self, emp_id: str) -> Dict:
        """
        Returns overtime pay for a single employee.
        Formula: overtime_hours * overtime_rate_per_hour
        """
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
        """Returns overtime pay for every employee."""
        return [self.calculate_overtime_pay(eid) for eid in self.payroll.employees]

    # ------------------------------------------------------------------
    # 3. FINAL SALARY (NET TAKE-HOME)
    # ------------------------------------------------------------------
    def calculate_final_salary(self, emp_id: str) -> Dict:
        """
        Returns the complete final salary breakdown for one employee.
        Delegates to Employee.calculate_salary_details().
        """
        emp = self.payroll.get_employee(emp_id)
        if not emp:
            return {"error": f"Employee '{emp_id}' not found."}

        details = emp.calculate_salary_details(self.payroll.total_working_days)
        details["emp_id"] = emp.emp_id
        details["emp_name"] = emp.emp_name
        details["dept_name"] = emp.department.dept_name
        return details

    def calculate_all_final_salaries(self) -> List[Dict]:
        """Returns final salary details for every employee."""
        return [self.calculate_final_salary(eid) for eid in self.payroll.employees]

    # ------------------------------------------------------------------
    # 4. EMPLOYEES BELOW ATTENDANCE THRESHOLD
    # ------------------------------------------------------------------
    def get_below_threshold_employees(self, threshold: float = None) -> List[Dict]:
        """
        Returns list of employees whose attendance % is below the threshold.
        Default threshold comes from self.attendance_threshold.
        """
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

        # Sort lowest attendance first
        flagged.sort(key=lambda x: x["attendance_pct"])
        return flagged

    # ------------------------------------------------------------------
    # 5. SUMMARY REPORT
    # ------------------------------------------------------------------
    def generate_summary_report(self) -> Dict:
        """
        Comprehensive summary report containing:
        - Company totals (gross, net, overtime, deductions)
        - Attendance overview (avg, best, worst)
        - Department breakdown
        - Employees below attendance threshold
        - Top overtime earners
        """
        employees = list(self.payroll.employees.values())

        if not employees:
            return {
                "empty": True,
                "message": "No employee records available.",
            }

        total = self.payroll.total_working_days
        totals = {
            "fixed_basic": 0.0,
            "earned_basic": 0.0,
            "overtime_pay": 0.0,
            "gross_salary": 0.0,
            "tax_deduction": 0.0,
            "pf_deduction": 0.0,
            "total_deductions": 0.0,
            "net_salary": 0.0,
            "overtime_hours": 0.0,
            "days_present": 0,
        }

        attendance_records = []
        ot_records = []

        for emp in employees:
            s = emp.calculate_salary_details(total)
            for k in totals:
                if k == "days_present":
                    totals[k] += emp.days_present
                elif k == "overtime_hours":
                    totals[k] += emp.overtime_hours
                elif k == "fixed_basic":
                    totals[k] += s["fixed_basic"]
                else:
                    totals[k] += s.get(k, 0.0)

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

        # Round totals
        for k in totals:
            if isinstance(totals[k], float):
                totals[k] = round(totals[k], 2)

        # Attendance stats
        attn_values = [r["attendance_pct"] for r in attendance_records]
        avg_attendance = round(sum(attn_values) / len(attn_values), 2)
        best = max(attendance_records, key=lambda x: x["attendance_pct"])
        worst = min(attendance_records, key=lambda x: x["attendance_pct"])

        # Top 5 overtime earners
        top_ot = sorted(ot_records, key=lambda x: x["overtime_pay"], reverse=True)[:5]

        # Below threshold
        below = self.get_below_threshold_employees()

        # Department breakdown
        dept_summary = self.payroll.get_department_summary()

        return {
            "empty": False,
            "total_employees": len(employees),
            "total_working_days": total,
            "attendance_threshold": self.attendance_threshold,
            "totals": totals,
            "attendance": {
                "average": avg_attendance,
                "best": best,
                "worst": worst,
                "below_threshold_count": len(below),
            },
            "top_overtime_earners": top_ot,
            "below_threshold": below,
            "departments": dept_summary,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _attendance_status(pct: float) -> str:
        if pct >= 95:
            return "Excellent"
        elif pct >= 85:
            return "Good"
        elif pct >= 75:
            return "Satisfactory"
        elif pct >= 60:
            return "Warning"
        else:
            return "Critical"
