# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import datetime
from frappe.utils import flt

def execute(filters=None):
	columns, data = [], []

	#if filters.get("date_range"):
	#	filters.update({"from_date": filters.get("date_range")[0], "to_date":filters.get("date_range")[1]})
	#else:
	#	return

	columns = get_default_columns(filters)
	columns.extend(get_earnings_columns(filters))

	data = get_employee_details(filters)
	return columns, data

def get_default_columns(filters):
	columns = [
		{
			"fieldname":"employee_id",
			"label":"Employee ID",
			"fieldtype":"Link",
			"options":"Employee",
			"width":100
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
			"fieldname":"struct_name",
			"label":"Active Salary Structure",
			"fieldtype":"Link",
			"options":"Salary Structure",
			"width":120
		},
		{
			"fieldname":"from_date",
			"label":"Applicable From",
			"fieldtype":"Date",
			"width":120
		},		
		{
			"fieldname":"base",
			"label":"Reported Salary",
			"fieldtype":"Float",
			"width":70
		},
		{
			"fieldname":"actual_salary",
			"label":"Actual Salary",
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
									distinct sc.salary_component
								from `tabSalary Detail` sc, `tabSalary Structure` struct
								where
									struct.name = sc.parent""", as_dict=True)

	for e in earnings:
		build_column = {}
		build_column["fieldname"] = e.salary_component+"formula"
		build_column["filedtype"] = "Text"
		build_column["label"] = e.salary_component+" Formula"
		build_column["width"] = 120
		columns.append(build_column)
		build_column = {}
		build_column["fieldname"] = e.salary_component+"rounding"
		build_column["filedtype"] = "Text"
		build_column["label"] = e.salary_component+" Rounding"
		build_column["width"] = 120
		columns.append(build_column)
		build_column = {}
		build_column["fieldname"] = e.salary_component+"lwp"
		build_column["filedtype"] = "Text"
		build_column["label"] = e.salary_component+" LWP"
		build_column["width"] = 120
		columns.append(build_column)
		build_column = {}
		build_column["fieldname"] = e.salary_component+"amt"
		build_column["filedtype"] = "Text"
		build_column["label"] = e.salary_component+" Amount"
		build_column["width"] = 120
		columns.append(build_column)

	return columns

def get_employee_details(filters):
	rows = []
	emp_details = frappe.db.sql("""select
					  employee.name,
					  employee.employee_name,
					  employee.branch,
					  employee.designation,
					  employee.department,
					  employee.bank_name,
					  employee.ifsc_code,
					  employee.bank_ac_no,
					  struct.name as struct_name,
					  struct_emp.from_date,
					  struct_emp.base,
					  struct_emp.actual_salary
					from
					  `tabEmployee` employee join
					  `tabSalary Structure Assignment` struct_emp
						on (struct_emp.employee = employee.name) join
					  `tabSalary Structure` struct on (struct.name = struct_emp.salary_structure and struct.is_active='Yes')
					where 
					  employee.status = 'Active'
					  and struct_emp.docstatus = 1
					  and struct_emp.from_date = (
								select max(from_date)
								from `tabSalary Structure Assignment` assign
								where assign.employee=employee.name and assign.salary_structure=struct.name and assign.docstatus=1)
					  and struct.docstatus = 1
					order by
					  employee.branch, employee.employee_name""", as_dict=True)

	for e in emp_details:
		build_row = {}
		build_row["employee_id"] = e.name
		build_row["employee_name"] = e.employee_name
		build_row["branch"] = e.branch
		build_row["department"] = e.department
		build_row["designation"] = e.designation
		build_row["struct_name"] = e.struct_name
		build_row["base"] = e.base
		build_row["actual_salary"] = e.actual_salary
		build_row["bank_name"] = e.bank_name
		build_row["ifsc"] = e.ifsc_code
		build_row["account_no"] = e.bank_ac_no
		build_row["from_date"] = e.from_date

		build_row.update(get_earnings_and_deductions(e.struct_name))

		rows.append(build_row)

	return rows

def get_earnings_and_deductions(struct_name):
	build_row = {}
	earnings = 0
	deductions = 0
	details = frappe.db.sql("""select
					  formula,
					  depends_on_payment_days,
					  salary_component,
					  rounding,
					  amount
					from
					  `tabSalary Detail`
					where
					  parent=%s""", struct_name, as_dict=1)

	for d in details:
		build_row[d.salary_component+"formula"] = d.formula
		build_row[d.salary_component+"lwp"] = d.depends_on_payment_days
		build_row[d.salary_component+"rounding"] = d.rounding
		build_row[d.salary_component+"amt"] = d.amount

	return build_row
