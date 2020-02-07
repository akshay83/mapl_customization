# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import datetime
from frappe.utils import flt

class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(DateTimeEncoder, self).default(obj)

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
			"width": 100
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
			"fieldname":"leave_without_pay",
			"label":"Absence",
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
			"fieldname":"leave_availed",
			"label":"Leave Availed",
			"fieldtype":"Int",
			"width":50
		},
		{
			"fieldname":"total_present_days",
			"label":"Present Days",
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
					  `tabLoan Deduction Detail` dd,
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
					  struct.base
					from
					  `tabSalary Slip` slip,
					  `tabSalary Structure Employee` struct
					where
					  struct.parent = slip.salary_structure
					  and slip.docstatus = 1
					  and struct.employee = slip.employee
					  and slip.start_date = %s
					  and slip.end_date = %s
					order by
					  slip.branch, slip.employee_name""",
					(filters.get("from_date"), filters.get("to_date")), as_dict=True)

	for e in emp_details:
		build_row = {}
		build_row["salary_slip_id"] = e.name
		build_row["employee_id"] = e.employee
		build_row["employee_name"] = e.employee_name
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

		build_row.update(get_earnings_and_deductions(e.name))
		build_row.update(get_loan_details(e.name))

		if build_row.get("total_loan",0) == 0:
			build_row["total_loan"] = e.total_loan_repayment
		build_row["net_pay"] = build_row.get("total_earnings",0)-(build_row.get("total_deductions")+build_row.get("total_loan",0))
		build_row.update(get_total_leaves(e.employee, filters))

		#If Biometric Attendance is Available
		if frappe.db.table_exists("Biometric Users"):
			build_row["biometric_attendance"] = get_biometric_attendance(e.employee, filters)

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
					  `tabLoan Deduction Detail`
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

def get_biometric_attendance(employee, filters):
	query = """
		select
			  users.name as `User Code`,
			  users.employee as `Employee Code`,
			  users.user_name as `User Name`,
			  machine.branch as `Branch`,
			  branch.opening_time as `Branch Opening Time`,
			  branch.closing_time as `Branch Closing Time`,
			  cast(att.timestamp as date) as `Punch Date`,
			  count(*) as `Punch Count`,
			  cast(min(att.timestamp) as Time) as `Earliest Punch`,
			  cast(max(att.timestamp) as Time) as `Last Punch`
		from
			  `tabBiometric Users` users,
			  `tabBiometric Attendance` att,
			  `tabBranch Settings` branch,
			  `tabEnrolled Users` enrolled,
			  `tabBiometric Machine` machine
		where
			  att.user_id = cast(substring(users.name,3) as Integer)
			  and cast(att.timestamp as date) >= %s
			  and cast(att.timestamp as date) <= %s
			  and machine.branch = branch.branch
			  and enrolled.parent = machine.name
			  and enrolled.user = users.name
			  and users.employee = %s
		group by
			  cast(att.timestamp as date),
			  users.name
		order by
			  cast(att.timestamp as date),
			  users.user_name
		"""

	ba = frappe.db.sql(query, (filters.get("from_date"), filters.get("to_date"), employee), as_dict=1)
	return DateTimeEncoder().encode(ba)
