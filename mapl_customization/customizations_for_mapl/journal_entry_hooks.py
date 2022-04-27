import frappe
from frappe.utils import cint
from frappe.exceptions import DoesNotExistError

def on_submit(doc, method):
    submit_loan_disbursal_entry(doc, method)

def submit_loan_disbursal_entry(doc, method):
    if not cint(frappe.db.get_single_value("Payroll Settings", "simplify_employee_loan_repayment")):
        return
    for a in doc.accounts:
        if a.reference_type == "Loan":
            loan_doc = frappe.get_doc("Loan", a.reference_name)
            if loan_doc.status in ["Sanctioned", "Partially Disbursed"]:
                if abs(a.debit) > (abs(loan_doc.loan_amount) - abs(loan_doc.disbursed_amount)):
                    frappe.throw("Cannot disburse More than the Total Loan Amount")
                frappe.db.sql("Update `tabLoan` set disbursed_amount=disbursed_amount+{0},status='{1}' where name = '{2}'"
                            .format(
                                abs(a.debit),
                                "Disbursed" if abs(a.debit) == (abs(loan_doc.loan_amount) - abs(loan_doc.disbursed_amount)) else "Partially Disbursed",
                                loan_doc.name
                            ))
                break

def on_cancel(doc, method):
    update_loan_on_cancel(doc, method)
    update_finance_payment_tool(doc, method)

def update_loan_on_cancel(doc, method):
    if not cint(frappe.db.get_single_value("Payroll Settings", "simplify_employee_loan_repayment")):
        return
    for a in doc.accounts:
        if a.reference_type == "Loan":
            loan_doc = frappe.get_doc("Loan", a.reference_name)
            if loan_doc.status in ["Partially Disbursed", "Disbursed"]:
                frappe.db.sql("Update `tabLoan` set disbursed_amount=disbursed_amount-{0},status='{1}' where name = '{2}'"
                            .format(
                                abs(a.debit),
                                "Partially Disbursed" if (abs(loan_doc.disbursed_amount) - abs(a.debit)) != 0 else "Sanctioned",
                                loan_doc.name
                            ))
                break

def update_finance_payment_tool(doc, method):
    if not frappe.db.exists("Finance Payment Details", {"journal_reference":doc.name}):
        return
    finance_row = frappe.get_doc("Finance Payment Details", {"journal_reference":doc.name})
    if finance_row and not finance_row.is_new():
        finance_row.journal_reference = None
        finance_row.imported = 0
        finance_row.save()