from __future__ import unicode_literals
import frappe
import erpnext
import math

from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words

def update_component_row(self, struct_row, amount, key):
		component_row = None
		for d in self.get(key):
			if d.salary_component == struct_row.salary_component:
				component_row = d

		#include our Custom Field 'Rounding'
		if not component_row:
			self.append(key, {
				'amount': amount,
				'default_amount': amount,
				'depends_on_lwp' : struct_row.depends_on_lwp,
				'salary_component' : struct_row.salary_component,
				'rounding' : struct_row.rounding
			})
		else:
			component_row.amount = amount


def sum_components(self, component_type, total_field):
		joining_date, relieving_date = frappe.db.get_value("Employee", self.employee,
			["date_of_joining", "relieving_date"])
		
		if not relieving_date:
			relieving_date = getdate(self.end_date)

		if not joining_date:
			frappe.throw(_("Please set the Date Of Joining for employee {0}").format(frappe.bold(self.employee_name)))

		for d in self.get(component_type):
			if (self.salary_structure and
				cint(d.depends_on_lwp) and
				(not
				    self.salary_slip_based_on_timesheet or
					getdate(self.start_date) < joining_date or
					getdate(self.end_date) > relieving_date
				)):

				#Same - Let the System do Rounding According to System Precision
				d.amount = rounded(
					(flt(d.default_amount) * flt(self.payment_days)
					/ cint(self.total_working_days)), self.precision("amount", component_type)
				)

				#Apply Our rounding Method
				d.amount = custom_round(d.rounding, d.amount)

			elif not self.payment_days and not self.salary_slip_based_on_timesheet:
				d.amount = 0
			elif not d.amount:
				d.amount = d.default_amount
			self.set(total_field, self.get(total_field) + flt(d.amount))


def custom_round(d, amt):
	if d and d != '':
		if d.lower() == 'downwards':
			return int(amt)
		elif d.lower() == 'upwards':
			return math.ceil(amt)
		else:
			return round(amt, 0)
	return amt
