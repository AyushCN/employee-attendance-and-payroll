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
        self.basic_salary = basic_salary  # Fixed Monthly Basic Salary
        self.overtime_rate_per_hour = overtime_rate_per_hour
        self.days_present = days_present
        self.overtime_hours = overtime_hours

    def calculate_salary_details(
        self,
        total_working_days: int = 22,
        tax_rate: float = 0.10,
        pf_rate: float = 0.05,
    ) -> Dict[str, float]:
        """Calculates attendance %, earned basic, overtime pay, deductions, and net salary."""
        # 1. Attendance Percentage Calculation
        attendance_pct = (
            (self.days_present / total_working_days) * 100
            if total_working_days > 0
            else 0.0
        )

        # 2. Fixed & Earned Basic Salary (Pro-rated by attendance)
        daily_rate = (
            self.basic_salary / total_working_days
            if total_working_days > 0
            else 0.0
        )
        earned_basic = daily_rate * self.days_present

        # 3. Overtime Calculation
        overtime_pay = self.overtime_hours * self.overtime_rate_per_hour

        # 4. Gross Earnings Calculation
        gross_salary = earned_basic + overtime_pay

        # 5. Deductions Calculation (Tax + Provident Fund / PF)
        tax_deduction = gross_salary * tax_rate
        pf_deduction = earned_basic * pf_rate
        total_deductions = tax_deduction + pf_deduction

        # 6. Net Take-Home Salary Calculation
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


class PayrollSystem:
    def __init__(
        self, total_working_days: int = 22, csv_file: str = "employees.csv"
    ):
        self.employees: Dict[str, Employee] = {}
        self.total_working_days = total_working_days
        self.csv_file = csv_file
        self.load_from_csv()

    # ------------------ Persistence (CSV) ------------------

    def save_to_csv(self) -> None:
        """Saves current employee records to CSV file."""
        fieldnames = [
            "emp_id",
            "emp_name",
            "dept_id",
            "dept_name",
            "basic_salary",
            "overtime_rate",
            "days_present",
            "overtime_hours",
        ]
        try:
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for emp in self.employees.values():
                    writer.writerow(
                        {
                            "emp_id": emp.emp_id,
                            "emp_name": emp.emp_name,
                            "dept_id": emp.department.dept_id,
                            "dept_name": emp.department.dept_name,
                            "basic_salary": emp.basic_salary,
                            "overtime_rate": emp.overtime_rate_per_hour,
                            "days_present": emp.days_present,
                            "overtime_hours": emp.overtime_hours,
                        }
                    )
            print(f"[+] Data successfully saved to '{self.csv_file}'.")
        except Exception as e:
            print(f"[-] Error saving to CSV: {e}")

    def load_from_csv(self) -> None:
        """Loads employee records from CSV file if present."""
        if not os.path.exists(self.csv_file):
            return

        try:
            with open(self.csv_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dept = Department(
                        dept_id=row["dept_id"], dept_name=row["dept_name"]
                    )
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
            print(
                f"[+] Loaded {len(self.employees)} employee(s) from '{self.csv_file}'."
            )
        except Exception as e:
            print(f"[-] Error loading CSV data: {e}")

    # ------------------ Employee Operations ------------------

    def add_employee(self, emp: Employee) -> None:
        if emp.emp_id in self.employees:
            print(f"[-] Error: Employee ID '{emp.emp_id}' already exists.")
            return
        self.employees[emp.emp_id] = emp
        print(f"[+] Employee '{emp.emp_name}' added successfully.")

    def update_employee(self, emp_id: str) -> None:
        """Interactive update for employee fields."""
        emp = self.employees.get(emp_id)
        if not emp:
            print(f"[-] Error: Employee ID '{emp_id}' not found.")
            return

        print(f"\n--- Updating Employee: {emp.emp_name} ({emp.emp_id}) ---")
        print("Leave blank to keep current value.")

        name = input(f"Name [{emp.emp_name}]: ").strip()
        if name:
            emp.emp_name = name

        dept_id = input(f"Dept ID [{emp.department.dept_id}]: ").strip()
        dept_name = input(f"Dept Name [{emp.department.dept_name}]: ").strip()
        if dept_id:
            emp.department.dept_id = dept_id
        if dept_name:
            emp.department.dept_name = dept_name

        sal_str = input(f"Fixed Basic Salary [{emp.basic_salary}]: ").strip()
        if sal_str:
            try:
                emp.basic_salary = float(sal_str)
            except ValueError:
                print("[-] Invalid input. Retained old basic salary.")

        ot_rate_str = input(
            f"Overtime Rate/Hr [{emp.overtime_rate_per_hour}]: "
        ).strip()
        if ot_rate_str:
            try:
                emp.overtime_rate_per_hour = float(ot_rate_str)
            except ValueError:
                print("[-] Invalid input. Retained old overtime rate.")

        days_str = input(f"Days Present [{emp.days_present}]: ").strip()
        if days_str:
            try:
                emp.days_present = int(days_str)
            except ValueError:
                print("[-] Invalid input. Retained old days present.")

        ot_hrs_str = input(f"Overtime Hours [{emp.overtime_hours}]: ").strip()
        if ot_hrs_str:
            try:
                emp.overtime_hours = float(ot_hrs_str)
            except ValueError:
                print("[-] Invalid input. Retained old overtime hours.")

        print(f"[+] Record updated for employee ID {emp_id}.")

    def mark_attendance_and_overtime(self, emp_id: str) -> None:
        emp = self.employees.get(emp_id)
        if not emp:
            print(f"[-] Error: Employee ID '{emp_id}' not found.")
            return

        try:
            days = int(
                input(
                    f"Enter days present for {emp.emp_name} (Max {self.total_working_days}): "
                )
            )
            ot = float(input(f"Enter overtime hours for {emp.emp_name}: "))
            emp.days_present = days
            emp.overtime_hours = ot
            pct = (days / self.total_working_days) * 100
            print(
                f"[+] Attendance updated: {days}/{self.total_working_days} days ({pct:.1f}%), {ot} OT hours."
            )
        except ValueError:
            print("[-] Invalid numerical input.")

    def delete_employee(self, emp_id: str) -> None:
        if emp_id in self.employees:
            removed = self.employees.pop(emp_id)
            print(f"[+] Removed employee '{removed.emp_name}' (ID: {emp_id}).")
        else:
            print(f"[-] Error: Employee ID '{emp_id}' not found.")

    # ------------------ Reports & Analytics ------------------

    def generate_payslip(self, emp_id: str) -> None:
        emp = self.employees.get(emp_id)
        if not emp:
            print(f"[-] Error: Employee ID '{emp_id}' not found.")
            return

        s = emp.calculate_salary_details(self.total_working_days)

        print("\n" + "=" * 60)
        print("                  DETAILED SALARY PAYSLIP")
        print("=" * 60)
        print(f"Employee ID    : {emp.emp_id:<15} Name : {emp.emp_name}")
        print(f"Department     : {emp.department.dept_name} (ID: {emp.department.dept_id})")
        print(f"Attendance     : {s['days_present']}/{self.total_working_days} Days ({s['attendance_pct']}%)")
        print(f"Overtime Hours : {s['overtime_hours']} Hrs @ ${s['overtime_rate']}/hr")
        print("-" * 60)
        print(f"Fixed Basic Salary  : ${s['fixed_basic']:>12,.2f}")
        print(f"Earned Basic Salary : ${s['earned_basic']:>12,.2f}")
        print(f"Overtime Allowance  : ${s['overtime_pay']:>12,.2f}")
        print("-" * 60)
        print(f"GROSS SALARY        : ${s['gross_salary']:>12,.2f}")
        print("-" * 60)
        print(f"Deductions:")
        print(f"  - Income Tax (10%): ${s['tax_deduction']:>12,.2f}")
        print(f"  - Provident (5%)  : ${s['pf_deduction']:>12,.2f}")
        print(f"Total Deductions    : -${s['total_deductions']:>11,.2f}")
        print("=" * 60)
        print(f"NET SALARY PAYABLE  : ${s['net_salary']:>12,.2f}")
        print("=" * 60 + "\n")

    def print_payroll_summary(self) -> None:
        if not self.employees:
            print("\n[-] No employee records available.\n")
            return

        print("\n" + "=" * 105)
        print(
            f"{'ID':<6} {'Name':<16} {'Dept':<12} {'Attn %':<8} {'Fixed Sal':<11} "
            f"{'Earned Sal':<11} {'OT Pay':<9} {'Gross':<10} {'Deductions':<11} {'Net Pay':<10}"
        )
        print("=" * 105)

        tot_fixed = tot_earned = tot_ot = tot_gross = tot_ded = tot_net = 0.0

        for emp in self.employees.values():
            s = emp.calculate_salary_details(self.total_working_days)
            tot_fixed += s["fixed_basic"]
            tot_earned += s["earned_basic"]
            tot_ot += s["overtime_pay"]
            tot_gross += s["gross_salary"]
            tot_ded += s["total_deductions"]
            tot_net += s["net_salary"]

            print(
                f"{emp.emp_id:<6} {emp.emp_name:<16} {emp.department.dept_name:<12} "
                f"{s['attendance_pct']:<8.1f} ${s['fixed_basic']:<10,.2f} ${s['earned_basic']:<10,.2f} "
                f"${s['overtime_pay']:<8,.2f} ${s['gross_salary']:<9,.2f} ${s['total_deductions']:<10,.2f} "
                f"${s['net_salary']:<10,.2f}"
            )

        print("=" * 105)
        print(
            f"{'TOTALS':<36} ${tot_fixed:<10,.2f} ${tot_earned:<10,.2f} ${tot_ot:<8,.2f} "
            f"${tot_gross:<9,.2f} ${tot_ded:<10,.2f} ${tot_net:<10,.2f}"
        )
        print("=" * 105 + "\n")

    def print_department_summary(self) -> None:
        """Prints aggregated payroll metrics broken down by department."""
        if not self.employees:
            print("\n[-] No employee records available.\n")
            return

        dept_data: Dict[str, Dict[str, float]] = {}

        for emp in self.employees.values():
            dname = emp.department.dept_name
            s = emp.calculate_salary_details(self.total_working_days)

            if dname not in dept_data:
                dept_data[dname] = {
                    "count": 0,
                    "attn_pct_sum": 0.0,
                    "ot_pay": 0.0,
                    "gross_pay": 0.0,
                    "net_pay": 0.0,
                }

            dept_data[dname]["count"] += 1
            dept_data[dname]["attn_pct_sum"] += s["attendance_pct"]
            dept_data[dname]["ot_pay"] += s["overtime_pay"]
            dept_data[dname]["gross_pay"] += s["gross_salary"]
            dept_data[dname]["net_pay"] += s["net_salary"]

        print("\n" + "=" * 75)
        print("                 DEPARTMENT PAYROLL ANALYTICS")
        print("=" * 75)
        print(
            f"{'Department':<18} {'Count':<7} {'Avg Attn %':<12} {'Total OT Pay':<14} "
            f"{'Total Gross':<13} {'Total Net Pay':<13}"
        )
        print("-" * 75)

        for dname, metrics in dept_data.items():
            avg_attn = metrics["attn_pct_sum"] / metrics["count"]
            print(
                f"{dname:<18} {metrics['count']:<7} {avg_attn:<12.1f}% "
                f"${metrics['ot_pay']:<13,.2f} ${metrics['gross_pay']:<12,.2f} ${metrics['net_pay']:<12,.2f}"
            )

        print("=" * 75 + "\n")


# ---------------------------------------------------------
# Interactive Menu Drive
# ---------------------------------------------------------

def main_menu():
    payroll = PayrollSystem(total_working_days=22, csv_file="employees.csv")

    while True:
        print("==================================================")
        print("   EMPLOYEE PAYROLL & ATTENDANCE MANAGEMENT SYSTEM ")
        print("==================================================")
        print("1. View Company Payroll Summary Report")
        print("2. Print Individual Employee Payslip")
        print("3. View Department Analytics Summary")
        print("4. Add New Employee")
        print("5. Update Employee Record")
        print("6. Mark Attendance & Overtime Hours")
        print("7. Delete Employee Record")
        print("8. Save Data to CSV File")
        print("9. Save & Exit")
        print("--------------------------------------------------")

        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            payroll.print_payroll_summary()

        elif choice == "2":
            emp_id = input("Enter Employee ID: ").strip()
            payroll.generate_payslip(emp_id)

        elif choice == "3":
            payroll.print_department_summary()

        elif choice == "4":
            print("\n--- Add New Employee ---")
            emp_id = input("Enter Employee ID: ").strip()
            emp_name = input("Enter Employee Name: ").strip()
            dept_id = input("Enter Department ID: ").strip()
            dept_name = input("Enter Department Name: ").strip()

            try:
                basic_sal = float(input("Enter Fixed Base Monthly Salary: "))
                ot_rate = float(
                    input("Enter Overtime Rate per Hour (Default 25.0): ") or 25.0
                )
            except ValueError:
                print("[-] Invalid numeric input. Creation canceled.")
                continue

            dept = Department(dept_id=dept_id, dept_name=dept_name)
            emp = Employee(
                emp_id=emp_id,
                emp_name=emp_name,
                department=dept,
                basic_salary=basic_sal,
                overtime_rate_per_hour=ot_rate,
            )
            payroll.add_employee(emp)

        elif choice == "5":
            emp_id = input("Enter Employee ID to Update: ").strip()
            payroll.update_employee(emp_id)

        elif choice == "6":
            emp_id = input("Enter Employee ID: ").strip()
            payroll.mark_attendance_and_overtime(emp_id)

        elif choice == "7":
            emp_id = input("Enter Employee ID to Delete: ").strip()
            payroll.delete_employee(emp_id)

        elif choice == "8":
            payroll.save_to_csv()

        elif choice == "9":
            payroll.save_to_csv()
            print("Exiting Payroll System. Goodbye!")
            break

        else:
            print("[-] Invalid choice. Please select an option between 1 and 9.\n")


if __name__ == "__main__":
    main_menu()
