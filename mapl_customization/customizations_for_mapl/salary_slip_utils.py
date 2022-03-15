import frappe

@frappe.whitelist()
def get_salary_payable_account(employee, salary_structure, on_date, company):
    salary_structure_assignment_payroll_payable = frappe.get_value("Salary Structure Assignment",
            {
                "employee": employee,
                "salary_structure": salary_structure,
                "from_date": ("<=", on_date),
                "docstatus": 1,
                "company": company
            },
            "payroll_payable_account",
            order_by="from_date desc",
            as_dict=True,
    )
    if not salary_structure_assignment_payroll_payable.payroll_payable_account:
        salary_structure_assignment_payroll_payable.payroll_payable_account = frappe.db.get_value("Company", company, "default_payroll_payable_account")
    return salary_structure_assignment_payroll_payable.payroll_payable_account

def salary_slip_before_save(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	from unrestrict_erpnext.unrestrict_erpnext.custom_salary_slip import get_repayment_schedule
	loan_details = get_repayment_schedule(doc)

	if not loan_details:
		return

	doc.set('loans', [])

	for l in loan_details:
		doc.append('loans', {
			"loan": l.name,
			"loan_type": l.loan_type,
			"interest_income_account": l.interest_income_account,
			#"total_loan_amount": l.loan_amount,
			"principal_amount": l.principal_amount,
			"interest_amount": l.interest_amount,
			"total_payment": l.total_payment
		})
