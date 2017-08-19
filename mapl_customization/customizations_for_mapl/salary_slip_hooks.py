import frappe

def salary_slip_before_save(doc, method):
	loan_details = frappe.db.sql("""select 
					  loan.name,
					  loan.loan_amount,
					  loan.loan_type,
					  sch.principal_amount, 
					  sch.interest_amount,
					  sch.total_payment 
					from 
					  `tabRepayment Schedule` sch,
					  `tabEmployee Loan` loan
					where 
					  loan.name = sch.parent
					  and sch.payment_date between %s and %s
					  and loan.employee = %s
					  and loan.repay_from_salary = 1 
					  and loan.docstatus = 1""",
					(doc.start_date, doc.end_date, doc.employee), as_dict=True)

	doc.set('loan_deduction_detail', [])

	for l in loan_details:
		doc.append('loan_deduction_detail', {
			"loan_reference": l.name,
			"loan_type": l.loan_type,
			"total_loan_amount": l.loan_amount,
			"principal_amount": l.principal_amount,
			"interest_amount": l.interest_amount,
			"total_payment": l.total_payment
		})

