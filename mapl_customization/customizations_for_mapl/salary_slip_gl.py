import frappe
from frappe.utils import cint, format_date, getdate
from erpnext import get_default_cost_center
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.general_ledger import make_gl_entries

def on_submit(doc, method):
    if not cint(frappe.db.get_single_value("Payroll Settings", "gl_entry_on_salary_slip_submit")):
        return
    salary_slip_gl_entry_hook = frappe.get_hooks(hook="salary_slip_gl_entry")
    create_gl_entries(doc, method)

def before_cancel(doc, method):
    if not cint(frappe.db.get_single_value("Payroll Settings", "gl_entry_on_salary_slip_submit")):
        return
    salary_slip_gl_entry_hook = frappe.get_hooks(hook="salary_slip_gl_entry")
    frappe.db.sql("""delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s""", (doc.doctype, doc.name))

def create_gl_entries(doc, method, cancel=0):
    if not doc.salary_payable_account:
        frappe.throw("Salary Payable Account Not Found")
    gle_map = []
    gle_map.append(
        frappe._dict({
			'company': doc.company,
			'posting_date': doc.posting_date,
			'fiscal_year': get_fiscal_year(doc.posting_date)[0],
			'voucher_type': doc.doctype,
			'voucher_no': doc.name,
			'remarks': "Salary Slip for the Period:"+format_date(doc.start_date,"dd-mm-yyyy")+" - "+format_date(doc.end_date,"dd-mm-yyyy")+";"+doc.salary_payable_account,
            'account': doc.salary_payable_account,
			'debit': 0,
			'credit': doc.net_pay,
			'debit_in_account_currency': 0,
			'credit_in_account_currency': doc.net_pay,
			'party_type': "Employee",
			'party': doc.employee,
            'cost_center': get_default_cost_center(doc.company)
        })
    )
    #Do Earnings & Deductions:
    for e in doc.earnings+doc.deductions:
        account = frappe.get_list("Salary Component Account", filters={"parent":e.salary_component}, fields=["account"])[0].account
        gle_map.append(
            frappe._dict({
			    'company': doc.company,
			    'posting_date': doc.posting_date,
			    'fiscal_year': get_fiscal_year(doc.posting_date)[0],
			    'voucher_type': doc.doctype,
			    'voucher_no': doc.name,
			    'remarks': "Salary Slip for the Period:"+format_date(doc.start_date,"dd-mm-yyyy")+" - "+format_date(doc.end_date,"dd-mm-yyyy")+";"+e.salary_component,
                'account': account,
			    'debit': e.amount if e.parentfield == 'earnings' else 0,
			    'credit': e.amount if e.parentfield == 'deductions' else 0,
			    'debit_in_account_currency': e.amount if e.parentfield == 'earnings' else 0,
			    'credit_in_account_currency': e.amount if e.parentfield == 'deductions' else 0,
                'cost_center': get_default_cost_center(doc.company)
            })
        )

    #Deduct Advances:
    for l in doc.loans:
        account = frappe.db.get_value("Loan", l.loan , "loan_account")
        gle_map.append(
            frappe._dict({
			    'company': doc.company,
			    'posting_date': doc.posting_date,
			    'fiscal_year': get_fiscal_year(doc.posting_date)[0],
			    'voucher_type': doc.doctype,
			    'voucher_no': doc.name,
			    'remarks': "Salary Slip for the Period:"+format_date(doc.start_date,"dd-mm-yyyy")+" - "+format_date(doc.end_date,"dd-mm-yyyy")+";"+account,
                'account': account,
			    'debit': 0,
			    'credit': l.total_payment,
			    'debit_in_account_currency': 0,
			    'credit_in_account_currency': l.total_payment,
                'cost_center': get_default_cost_center(doc.company),
                'party': doc.employee,
                'party_type': "Employee"
            })
        )
    
    make_gl_entries(gle_map, cancel=cancel, merge_entries=False)
