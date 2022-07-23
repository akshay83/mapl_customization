# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import datetime
from frappe.utils import flt

def execute(filters=None):
	columns, data = [], []

	if filters.get("date_range"):
		filters.update({"from_date": filters.get("date_range")[0], "to_date":filters.get("date_range")[1]})
	else:
		return

	columns = get_default_columns(filters)
	columns.extend(get_earnings_columns(filters))
	columns.append({
		"fieldname":"total_earnings",
		"label":"Total Earnings",
		"fieldtype": "Float",
		"width": 80
	})
	columns.extend(get_deductions_columns(filters))
	columns.append({
		"fieldname":"total_deductions",
		"label":"Total Deductions",
		"fieldtype": "Float",
		"width": 80
	})
	columns.extend(get_loan_columns(filters))
	columns.append({
		"fieldname":"total_loan",
		"label":"Total Advances",
		"fieldtype": "Float",
		"width": 80
	})
	columns.append({
		"fieldname":"net_pay",
		"label":"Net Pay",
		"fieldtype": "Float",
		"width": 80
	})
	columns.append({
		"fieldname":"total_leaves",
		"label":"Total Leaves",
		"fieldtype": "Int",
		"width": 80
	})

	#Check if Biometric Attendance in Available
	if(frappe.db.table_exists("Biometric Users")):
		columns.append({
			"fieldname": "biometric_attendance",
			"label": "Biometric Attendance",
			"fieldtype": "Text",
			"width": 0
		})

	data = get_employee_details(filters)
	return columns, data

def get_default_columns(filters):
	columns = [
		{
			"fieldname":"salary_slip_id",
			"label":"Salary Slip ID",
			"fieldtype":"Link",
			"options":"Salary Slip",
			"width":120
		},
		{
			"fieldname":"employee_id",
			"label":"Employee ID",
			"fieldtype":"Link",
			"options":"Employee",
			"width":80
		},
		{
			"fieldname":"employee_name",
			"label":"Employee Name",
			"fieldtype":"Data",
			"width":120
		},
		{
			"fieldname":"employee_uan",
			"label":"UAN No",
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"employee_esic",
			"label":"ESIC No",
			"fieldtype":"Data",
			"width":100
		},		
		{
			"fieldname":"branch",
			"label":"Branch",
			"fieldtype":"Link",
			"options":"Branch",
			"width":80
		},
		{
			"fieldname":"department",
			"label":"Department",
			"fieldtype":"Link",
			"options":"Department",
			"width":80
		},
		{
			"fieldname":"designation",
			"label":"Designation",
			"fieldtype":"Link",
			"options":"Designation",
			"width":80
		},
		{
			"fieldname":"total_present_days",
			"label":"Present Days",
			"fieldtype":"Int",
			"width":50
		},
		{
			"fieldname":"leave_without_pay",
			"label":"Absence",
			"fieldtype":"Int",
			"width":50
		},
		{
			"fieldname":"leave_availed",
			"label":"Leave Availed",
			"fieldtype":"Int",
			"width":50
		},
		{
			"fieldname":"total_payment_days",
			"label":"Payment Days",
			"fieldtype":"Int",
			"width":50
		},
		{
			"fieldname":"base",
			"label":"Base",
			"fieldtype":"Float",
			"width":70
		},
		{
			"fieldname":"bank_name",
			"label":"Bank Name",
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"ifsc",
			"label":"IFSC Code",
			"fieldtype":"Data",
			"width":75
		},
		{
			"fieldname":"account_no",
			"label":"Bank Account No",
			"fieldtype":"Data",
			"width":100
		}
	]

	return columns

def get_earnings_columns(filters):
	columns = []
	earnings = frappe.db.sql("""select
					  distinct sc.name
					from `tabSalary Component` sc
					where
					  sc.type = 'Earning'
					  and (select sum(amount) from `tabSalary Detail` det,`tabSalary Slip` slip
						    where det.parenttype='Salary Slip' and det.salary_component=sc.name and slip.name=det.parent
						    and slip.start_date>=%s and slip.end_date<=%s) > 0""",
					(filters.get("from_date"), filters.get("to_date")), as_dict=True)

	for e in earnings:
		build_column = {}
		build_column["fieldname"] = e.name
		build_column["filedtype"] = "Float"
		build_column["label"] = e.name
		build_column["width"] = 120
		build_column["default"] = 0
		columns.append(build_column)

	return columns

def get_deductions_columns(filters):
	columns = []
	deductions = frappe.db.sql("""select
					  distinct sc.name
					from `tabSalary Component` sc
					where
					  sc.type = 'Deduction'
					  and (select sum(amount) from `tabSalary Detail` det,`tabSalary Slip` slip
						    where det.parenttype='Salary Slip' and det.salary_component=sc.name and slip.name=det.parent
						    and slip.start_date>=%s and slip.end_date<=%s) > 0""",
					(filters.get("from_date"), filters.get("to_date")), as_dict=True)

	for d in deductions:
		build_column = {}
		build_column["fieldname"] = d.name
		build_column["filedtype"] = "Float"
		build_column["label"] = d.name
		build_column["width"] = 120
		columns.append(build_column)

	return columns

def get_loan_columns(filters):
	columns = []
	loan_details = frappe.db.sql("""select
					  distinct dd.loan_type
					from
					  `tabSalary Slip Loan` dd,
					  `tabSalary Slip` slip
					where
					  dd.parent=slip.name
					  and slip.start_date>=%s
					  and slip.end_date<=%s""",
					(filters.get("from_date"), filters.get("to_date")), as_dict=True)

	for l in loan_details:
		build_column = {}
		build_column["fieldname"] = l.loan_type
		build_column["filedtype"] = "Float"
		build_column["label"] = l.loan_type
		build_column["width"] = 120
		columns.append(build_column)

	return columns


def get_employee_details(filters):
	rows = []
	emp_details = frappe.db.sql("""select
					  slip.name,
					  slip.employee_name,
					  slip.employee,
					  ifnull(slip.uan_no,(select uan_no from `tabEmployee` where name=slip.employee limit 1)) as uan_no,
					  ifnull(slip.esic_no,(select esic_no from `tabEmployee` where name=slip.employee limit 1)) as esic_no,
					  slip.branch,
					  slip.designation,
					  slip.department,
					  slip.total_working_days,
					  slip.leave_without_pay,
					  slip.payment_days,
					  slip.leave_availed,
					  slip.total_loan_repayment,
					  slip.bank_name,
					  slip.ifsc_code,
					  slip.bank_account_no,
					  slip.salary_payable_account,
					  slip.company,
					  struct.base,
					  slip.salary_structure,
					  struct.from_date
					from
					  `tabSalary Slip` slip left join
					  `tabSalary Structure Assignment` struct
						on (struct.salary_structure = slip.salary_structure and struct.employee = slip.employee)
					where
					  slip.docstatus = 1
					  and struct.docstatus = 1
					  and slip.start_date = %s
					  and slip.end_date = %s
					  and struct.from_date = (
						select max(from_date)
						from `tabSalary Structure Assignment` assign
						where assign.employee=slip.employee and assign.salary_structure=slip.salary_structure and assign.docstatus=1 and from_date <= %s)
					order by
					  slip.branch, slip.employee_name""",
					(filters.get("from_date"), filters.get("to_date"), filters.get("from_date")), as_dict=True)

	for e in emp_details:
		build_row = frappe._dict()
		build_row["salary_slip_id"] = e.name
		build_row["employee_id"] = e.employee
		build_row["employee_name"] = e.employee_name
		build_row["employee_uan"] = e.uan_no
		build_row["employee_esic"] = e.esic_no
		build_row["branch"] = e.branch
		build_row["department"] = e.department
		build_row["designation"] = e.designation
		build_row["total_payment_days"] = e.payment_days
		build_row["leave_without_pay"] = (e.leave_without_pay + e.leave_availed)
		build_row["leave_availed"] = e.leave_availed
		build_row["total_present_days"] = (e.payment_days - e.leave_availed)
		build_row["base"] = e.base
		build_row["bank_name"] = e.bank_name
		build_row["ifsc"] = e.ifsc_code
		build_row["account_no"] = e.bank_account_no
		build_row["salary_payable_account"] = e.salary_payable_account
		build_row["company"] = e.company
		build_row["salary_structure"] = e.salary_structure
		build_row["salary_from_date"] = e.from_date

		build_row.update(get_earnings_and_deductions(e.name))
		build_row.update(get_loan_details(e.name))

		if build_row.get("total_loan",0) == 0:
			build_row["total_loan"] = e.total_loan_repayment
		build_row["net_pay"] = build_row.get("total_earnings",0)-(build_row.get("total_deductions")+build_row.get("total_loan",0))
		build_row.update(get_total_leaves(e.employee, filters))

		#If Biometric Attendance is Available
		if frappe.db.table_exists("Biometric Users"):
			from biometric_attendance.biometric_attendance.report.monthly_attendance.monthly_attendance import get_biometric_attendance
			build_row["biometric_attendance"] = get_biometric_attendance(employee=e.employee, filters=filters)

		rows.append(build_row)

	return rows

def get_earnings_and_deductions(slip_name):
	build_row = {}
	earnings = 0
	deductions = 0
	details = frappe.db.sql("""select
					  amount,
					  parentfield,
					  salary_component
					from
					  `tabSalary Detail`
					where
					  parent=%s""", slip_name, as_dict=1)

	for d in details:
		build_row[d.salary_component] = build_row.get(d.salary_component,0) + d.amount
		if d.parentfield == 'earnings':
			earnings += d.amount
		else:
			deductions += d.amount

	build_row["total_earnings"] = earnings
	build_row["total_deductions"] = deductions
	return build_row

def get_loan_details(slip_name):
	build_row = {}
	total_loan = 0
	details = frappe.db.sql("""select
					  total_payment,
					  loan_type
					from
					  `tabSalary Slip Loan`
					where
					  parent=%s""", slip_name, as_dict=1)

	for d in details:
		build_row[d.loan_type] = build_row.get(d.loan_type,0) + d.total_payment
		total_loan += d.total_payment

	build_row["total_loan"] = total_loan
	return build_row

def get_total_leaves(employee, filters):
	build_row = {}
	total_loan = 0
	details = frappe.db.sql("""
					select
					  sum(leave_availed) as total_leaves
					from
					  `tabSalary Slip` slip,
					  `tabFiscal Year` yr
					where
					  slip.start_date >= yr.year_start_date
					  and slip.end_date <= yr.year_end_date
					  and slip.docstatus = 1
					  and slip.employee = %s
					  and %s between yr.year_start_date and yr.year_end_date
					  and slip.end_date <= %s
				""", (employee, filters.get("from_date"), filters.get("to_date")), as_dict=1)

	for d in details:
		build_row["total_leaves"] = d.total_leaves

	return build_row
