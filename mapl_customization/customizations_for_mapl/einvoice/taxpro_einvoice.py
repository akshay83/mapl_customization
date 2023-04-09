import frappe
import base64
import os
import json
from frappe import _
from erpnext.regional.india.e_invoice.utils import GSPConnector, log_error, RequestFailed, make_einvoice, get_eway_bill_details, CancellationNotAllowed, show_bulk_action_failure_message
from frappe.utils.data import add_to_date, time_diff_in_hours, now_datetime
from frappe.utils import cint
from frappe.exceptions import CharacterLengthExceededError
from frappe.integrations.utils import make_get_request, make_post_request

@frappe.whitelist()
def validate_eligibility(doc, taxpro=0):
    if not taxpro:
        return False
    from erpnext.regional.india.e_invoice.utils import validate_eligibility
    return validate_eligibility(doc)

class TaxproGSP(GSPConnector):
    def __init__(self, doctype=None, docname=None):
        self.doctype = doctype
        self.docname = docname

        self.set_invoice()
        self.set_credentials()

        self.base_url = 'https://einvapi.charteredinfo.com' if not self.e_invoice_settings.sandbox_mode else 'http://gstsandbox.charteredinfo.com'
        self.authenticate_url = self.base_url + '/eivital/dec/v1.04/auth'

        self.base_eway_bill_url = self.base_url + ("/v1.03/dec" if not self.e_invoice_settings.sandbox_mode else "/ewaybillapi/dec/v1.03")
        self.eway_auth_url = self.base_eway_bill_url + "/auth?action=ACCESSTOKEN" #NOT USED
        self.base_url_eway_bill_actions = self.base_eway_bill_url + '/ewayapi'

        self.cancel_irn_url = self.base_url + '/eicore/dec/v1.03/Invoice/Cancel'
        self.irn_details_url = self.base_url + '/eicore/dec/v1.03/Invoice/irn'
        self.generate_irn_url = self.base_url + '/eicore/dec/v1.03/Invoice'

        #self.gstin_details_url = self.base_url + '/eivital/dec/v1.04/Master/gstin'        
        #self.cancel_ewaybill_url = self.base_url + '/ewaybillapi/dec/v1.03/ewayapi?action=CANEWB' if not self.e_invoice_settings.sandbox_mode else '/v1.03/dec/ewayapi?action=CANEWB'
        self.generate_ewaybill_by_irn_url = self.base_url + '/eiewb/dec/v1.03/ewaybill'
        #self.eway_bill_by_irn = self.base_url + '/eiewb/dec/v1.03/ewaybill/irn'

    def make_request(self, request_type, url, headers=None, data=None):
        if request_type == 'post':
            res = make_post_request(url, headers=headers, data=data)
        else:
            res = make_get_request(url, headers=headers, data=data)

        self.log_request(url, headers, data, res)
        ##--DEBUG--print ('-------------REQUEST RESULT--------------')
        ##--DEBUG--print (frappe.flags.integration_request.json())
        ##--DEBUG--print ('-----------------------------------------')
        return res        

    def fetch_auth_token(self):
        headers = self.get_headers(withAuthToken=False)
        res = {}
        try:
            res = self.make_request('get', self.authenticate_url, headers)
            ##--DEBUG--print ('----------------AuthToken----------------')
            ##--DEBUG--print (res)
            ##--DEBUG--print ('-----------------------------------------')
            res = res.get("Data")
            if isinstance(res, str):
                res = json.loads(res)
            self.e_invoice_settings.auth_token = "{}".format(res.get('AuthToken'))
            self.e_invoice_settings.token_expiry = res.get('TokenExpiry')
            self.e_invoice_settings.save(ignore_permissions=True)
            self.e_invoice_settings.reload()

        except Exception:
            log_error(res)
            self.raise_error(True)

    def get_headers(self, withAuthToken=True, forEwayBill=False):
        headers = {
			'Content-Type': 'application/json; charset=utf-8',
			'user_name': self.credentials.username if not self.e_invoice_settings.sandbox_mode else 'TaxProEnvPON',
			'eInvPwd': self.credentials.get_password() if not self.e_invoice_settings.sandbox_mode else 'abc34*',
			'Gstin': self.credentials.gstin if not self.e_invoice_settings.sandbox_mode else '34AACCC1596Q002',
			'requestid': str(base64.b64encode(os.urandom(18))),
        }
        client_id, client_secret = self.get_client_credentials()
        headers.update({"aspid":client_id,"password":client_secret})        
        if withAuthToken:
            headers.update({'AuthToken': self.get_auth_token()})
        if forEwayBill:
            headers.update({
                "username":self.credentials.username if not self.e_invoice_settings.sandbox_mode else 'TaxProEnvPON',
                "ewbpwd":self.credentials.get_password() if not self.e_invoice_settings.sandbox_mode else 'abc34*',
            })
        return headers

    def generate_irn(self):
        data = {}
        try:
            headers = self.get_headers()
            einvoice = make_einvoice(self.invoice)
            data = json.dumps(einvoice, indent=4)
            res = self.make_request('post', self.generate_irn_url, headers, data)
            ##--DEBUG--print ('----------------Generate IRN----------------')
            ##--DEBUG--print (res)
            ##--DEBUG--print ('-----------------------------------------')

            if res.get('Status') == "1":
                self.set_einvoice_data(json.loads(res.get('Data')))

            elif res.get('Status') == "0" and res.get('ErrorDetails')[0].get("ErrorCode") == "2150":
                # IRN already generated but not updated in invoice
                # Extract the IRN from the response description and fetch irn details
                irn = res.get('InfoDtls')[0].get('Desc').get('Irn')
                irn_details = json.loads(self.get_irn_details(irn))
                if irn_details:
                    self.set_einvoice_data(irn_details)
                else:
                    raise RequestFailed('IRN has already been generated for the invoice but cannot fetch details for it.')
            elif res.get('Status') == "0" and res.get('ErrorDetails')[0].get("ErrorCode") == "2278":
                frappe.throw("IRN Already Generated or Cancelled")
            elif res.get('Status') == "0" and res.get('ErrorDetails')[0].get("ErrorCode") == "3074":
                frappe.throw("Customer GSTIN is Cancelled or Wrong")
            elif res.get('Status') == "0" and res.get('ErrorDetails')[0].get("ErrorCode") == "3028":
                frappe.throw("Customer GSTIN is Wrong")
            else:
                raise RequestFailed

        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.set_failed_status(errors=errors)
            self.raise_error(errors=errors)

        except Exception as e:
            self.set_failed_status(errors=str(e))
            log_error(data)
            self.raise_error(True)

    def get_irn_details(self, irn):
        headers = self.get_headers()
        try:
            params = '/{irn}'.format(irn=irn)
            res = self.make_request('get', self.irn_details_url + params, headers)
            if res.get('Status') == "1":
                return res.get('Data')
            else:
                raise RequestFailed
        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.raise_error(errors=errors)
        except Exception:
            log_error()
            self.raise_error(True)

    def get_eway_bill_by_irn_details(self, irn):
        headers = self.get_headers()
        try:
            params = '/{irn}'.format(irn=irn)
            res = self.make_request('get', self.irn_details_url + params, headers)
            if res.get('Status') == "1":
                return res.get('Data')
            else:
                raise RequestFailed
        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.raise_error(errors=errors)
        except Exception:
            log_error()
            self.raise_error(True)

    def cancel_irn(self, irn, reason, remark):
        data, res = {}, {}
        try:
            # validate cancellation
            if time_diff_in_hours(now_datetime(), self.invoice.ack_date) > 24:
                frappe.throw(_('E-Invoice cannot be cancelled after 24 hours of IRN generation.'), title=_('Not Allowed'), exc=CancellationNotAllowed)
            if not irn:
                frappe.throw(_('IRN not found. You must generate IRN before cancelling.'), title=_('Not Allowed'), exc=CancellationNotAllowed)

            headers = self.get_headers()
            data = json.dumps({
                'Irn': irn,
                'Cnlrsn': reason,
                'Cnlrem': remark
            }, indent=4)

            res = self.make_request('post', self.cancel_irn_url, headers, data)
            ##--DEBUG--print ('----------------Cancel IRN----------------')
            ##--DEBUG--print (res)
            ##--DEBUG--print ('-----------------------------------------')
            if res.get('Status') == "1":
                self.invoice.irn_cancelled = 1
                res = res.get("Data")
                if isinstance(res, str):
                    res = json.loads(res)
                self.invoice.irn_cancel_date = res.get('CancelDate')
                self.invoice.einvoice_status = 'Cancelled'
                self.invoice.flags.updater_reference = {
                    'doctype': self.invoice.doctype,
                    'docname': self.invoice.reporting_name,
                    'label': _('IRN Cancelled - {}').format(remark)
                }
                self.update_invoice()

            else:
                raise RequestFailed

        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.set_failed_status(errors=errors)
            self.raise_error(errors=errors)

        except CancellationNotAllowed as e:
            self.set_failed_status(errors=str(e))
            self.raise_error(errors=str(e))

        except Exception as e:
            self.set_failed_status(errors=str(e))
            log_error(data)
            self.raise_error(True)

    def generate_eway_bill_by_json(self, **kwargs):
        from erpnext.regional.india.utils import generate_ewb_json
        from requests import request
        args = frappe._dict(kwargs)
        if args:
            self.invoice.update(args)
            self.invoice.flags.updater_reference = {
                    'doctype': self.invoice.doctype,
					'docname': self.invoice.reporting_name,
					'label': _('Transport Details Updated')
            }
            self.update_invoice()            
        data = generate_ewb_json('Sales Invoice', json.dumps([self.invoice.name]))['billLists'][0]
        data = make_supporting_request_data(data)
        #--DEBUG--data1 = {'action':'GENEWAYBILL','data':base64.b64encode(str(data).encode('utf-8'))}
        #--DEBUG--return data
        headers = self.get_headers(forEwayBill=True)
        try:
            res = request(
                        'POST', 
                        self.build_url_with_params_for_ewaybill(self.base_url_eway_bill_actions+"?action=GENEWAYBILL",headers),
                        headers={"Content-Type":"application/json"}, 
                        data=json.dumps(data)
                )
            self.log_request(
                    self.build_url_with_params_for_ewaybill(self.base_url_eway_bill_actions+"?action=GENEWAYBILL",headers),
                    {"Content-Type":"application/json"}, 
                    json.dumps(data), 
                    res.text
                )
            res_json = json.loads(res.text)
            #--DEBUG--print ('----------------Generate EWAY JSON----------------')
            #--DEBUG--print (res.text)
            #--DEBUG--print (cint(res_json.get("status_cd",1)), res_json.get('ewayBillNo'))
            #--DEBUG--print ('-----------------------------------------')            
            if cint(res_json.get("status_cd",1))==1 and res_json.get('ewayBillNo'):
                self.update_eway_bill_details_by_json(res_json)
            else:
                raise RequestFailed

        except RequestFailed:
            self.raise_error(errors=res_json.get("error").get("message"))

        except Exception:
            log_error(data)
            self.raise_error(True)

    def generate_eway_bill_by_irn(self, **kwargs):
        args = frappe._dict(kwargs)
        self.validate_sales_invoice_for_ewaybill()
        headers = self.get_headers()
        eway_bill_details = get_eway_bill_details(args)
        data = json.dumps({
			'Irn': args.irn,
			'Distance': cint(eway_bill_details.distance),
			'TransMode': eway_bill_details.mode_of_transport,
			'TransId': eway_bill_details.gstin,
			'TransName': eway_bill_details.transporter,
			'TrnDocDt': eway_bill_details.document_date,
			'TrnDocNo': eway_bill_details.document_name,
			'VehNo': eway_bill_details.vehicle_no,
			'VehType': eway_bill_details.vehicle_type
        }, indent=4)

        try:
            res = self.make_request('post', self.generate_ewaybill_by_irn_url, headers, data)
            ##--DEBUG--print ('----------------Generate EWAY----------------')
            ##--DEBUG--print (res)
            ##--DEBUG--print ('-----------------------------------------')
            if res.get('Status') == "1":
                res = json.loads(res.get("Data"))
                self.update_eway_bill_details_by_irn(res, args)
            elif res.get('Status') == "0" and res.get('ErrorDetails')[0].get('ErrorCode') == "4002":
                res = json.loads(self.get_eway_bill_by_irn_details(self.invoice.irn))
                self.update_eway_bill_details_by_irn(res, args)
            else:
                raise RequestFailed

        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.raise_error(errors=errors)

        except Exception:
            log_error(data)
            self.raise_error(True)

    def update_eway_bill_details_by_irn(self, eway_bill_data, args):
        self.invoice.ewaybill = eway_bill_data.get('EwbNo')
        self.invoice.eway_bill_validity = eway_bill_data.get('EwbValidTill')
        self.invoice.eway_bill_cancelled = 0
        self.invoice.update(args)
        self.invoice.flags.updater_reference = {
					'doctype': self.invoice.doctype,
					'docname': self.invoice.reporting_name,
					'label': _('E-Way Bill Generated')
        }
        self.update_invoice()

    def update_eway_bill_details_by_json(self, eway_bill_data):
        self.invoice.ewaybill = eway_bill_data.get('ewayBillNo')
        self.invoice.eway_bill_validity = eway_bill_data.get('validUpto')
        self.invoice.eway_bill_cancelled = 0
        self.invoice.flags.updater_reference = {
					'doctype': self.invoice.doctype,
					'docname': self.invoice.reporting_name,
					'label': _('E-Way Bill Generated')
        }
        self.update_invoice()

    def cancel_eway_bill(self, reason, remark):
        headers = self.get_headers(forEwayBill=True)
        data = json.dumps({
			'ewbNo': self.invoice.ewaybill,
			'cancelRsnCode': reason,
			'cancelRmrk': remark
        }, indent=4)     
        try:
            res = self.make_request(
                        'post', 
                        self.build_url_with_params_for_ewaybill(self.base_url_eway_bill_actions+"?action=CANEWB", headers), 
                        headers={"Content-Type":"application/json"}, 
                        data=data
                    )
            ##--DEBUG--print ('----------------Cancel EWAY----------------')
            ##--DEBUG--print (res)
            ##--DEBUG--print ('-----------------------------------------')
            if res.get('cancelDate'):
                self.invoice.ewaybill = None
                self.invoice.eway_bill_cancelled = 1
                self.invoice.eway_bill_validity = None
                self.invoice.flags.updater_reference = {
					'doctype': self.invoice.doctype,
					'docname': self.invoice.reporting_name,
					'label': _('E-Way Bill Cancelled - {}').format(remark)
                }
                self.update_invoice()
            else:
                raise RequestFailed

        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.raise_error(errors=errors)

        except Exception:
            log_error(data)
            self.raise_error(True)

    def get_eway_bill_details(self, **kwargs):
        args = frappe._dict(kwargs)
        headers = self.get_headers()
        #headers.update({'ewbNo':self.invoice.ewaybill or args.ewaybill_no})
        try:
            ewbNo = getattr(self, 'invoice',None)
            ewbNo = ewbNo.ewaybill if ewbNo else args.ewaybill_no
            res = self.make_request(
                    'get', 
                    self.build_url_with_params_for_ewaybill(self.base_url_eway_bill_actions+"?action=GetEwayBill", headers)+"&ewbNo="+ewbNo, 
                    headers={}
                )
            ##--DEBUG--print ('----------------Print EWAY----------------')
            ##--DEBUG--print (headers)
            ##--DEBUG--print (res)
            ##--DEBUG--print ('-----------------------------------------')
            return res
        except RequestFailed:
            errors = self.sanitize_error_message(res)
            self.raise_error(errors=errors)
        except Exception:
            log_error()
            self.raise_error(True)
           
    def build_url_with_params_for_ewaybill(self,base_url, headers):
        url_params = "aspid={0}&password={1}&gstin={2}&AuthToken={3}".format(
                headers.get('aspid'),
                headers.get('password'),
                headers.get('Gstin'),
                headers.get('AuthToken'))
        if "?" in base_url:
            url_params = "&"+url_params
        else:
            url_params = "?"+url_params
        #--DEBUG--print (base_url+url_params)
        return base_url+url_params

    def validate_sales_invoice_for_ewaybill(self):
        if self.invoice.docstatus != 1:
            frappe.throw(_('E-Way Bill JSON can only be generated from submitted document'))
        if self.invoice.is_return:
            frappe.throw(_('E-Way Bill JSON cannot be generated for Sales Return as of now'))
        if self.invoice.ewaybill:
            frappe.throw(_('e-Way Bill already exists for this document'))

    @staticmethod
    def bulk_generate_irn(invoices):
        gsp_connector = TaxproGSP()
        gsp_connector.doctype = 'Sales Invoice'

        failed = []

        for invoice in invoices:
            try:
                gsp_connector.docname = invoice
                gsp_connector.set_invoice()
                gsp_connector.set_credentials()
                gsp_connector.generate_irn()

            except Exception as e:
                failed.append({
                    'docname': invoice,
                    'message': str(e)
                })

        return failed

def make_supporting_request_data(ewb):
    # TODO: check if this is common for all gsp's 
    # Note: so far all these changes are due to diff in ewb upload json and ewb api json formats
    mapping_keys = {'actualFromStateCode':'actFromStateCode', 'actualToStateCode':'actToStateCode', 'transType':'transactionType', 'OthValue':'otherValue'}
    for key in mapping_keys:
        if key in ewb:
            ewb[mapping_keys[key]] = ewb[key]
            del ewb[key]
    if 'transporterId' in ewb and ewb['transporterId']:
        if 'transDocNo' in ewb:
            del ewb['transDocNo']
        if 'transMode' in ewb:
            del ewb['transMode']
        if 'vehicleNo' in ewb:
            del ewb['vehicleNo']
    return ewb

@frappe.whitelist()
def get_einvoice(doctype, docname):
    invoice = frappe.get_doc(doctype, docname)
    return make_einvoice(invoice)

@frappe.whitelist()
def generate_irn(doctype, docname):
    gsp_connector = TaxproGSP(doctype, docname)
    gsp_connector.generate_irn()

@frappe.whitelist()
def cancel_irn(doctype, docname, irn, reason, remark):
    gsp_connector = TaxproGSP(doctype, docname)
    gsp_connector.cancel_irn(irn, reason, remark)

@frappe.whitelist()
def generate_eway_bill_by_json(doctype, docname, **kwargs):
	gsp_connector = TaxproGSP(doctype, docname)
	gsp_connector.generate_eway_bill_by_json(**kwargs)

@frappe.whitelist()
def generate_eway_bill_by_irn(doctype, docname, **kwargs):
	gsp_connector = TaxproGSP(doctype, docname)
	gsp_connector.generate_eway_bill_by_irn(**kwargs)

@frappe.whitelist()
def get_eway_bill_details(doctype, docname, **kwargs):
	gsp_connector = TaxproGSP(doctype, docname)
	return gsp_connector.get_eway_bill_details(**kwargs)

@frappe.whitelist()
def cancel_eway_bill(doctype, docname, reason, remark):
	# TODO: uncomment when eway_bill api from Adequare is enabled
	gsp_connector = TaxproGSP(doctype, docname)
	gsp_connector.cancel_eway_bill(reason, remark)

	frappe.db.set_value(doctype, docname, 'ewaybill', '')
	frappe.db.set_value(doctype, docname, 'eway_bill_cancelled', 1)

@frappe.whitelist()
def generate_einvoices(docnames):
    docnames = json.loads(docnames) or []

    failures = TaxproGSP.bulk_generate_irn(docnames)
    frappe.local.message_log = []

    if failures:
        show_bulk_action_failure_message(failures)

    success = len(docnames) - len(failures)
    frappe.msgprint(
        _('{} e-invoices generated successfully').format(success),
        title=_('Bulk E-Invoice Generation Complete')
    )

@frappe.whitelist()
def cancel_irns(docnames, reason, remark):
    docnames = json.loads(docnames) or []

    failures = TaxproGSP.bulk_cancel_irn(docnames, reason, remark)
    frappe.local.message_log = []

    if failures:
        show_bulk_action_failure_message(failures)

    success = len(docnames) - len(failures)
    frappe.msgprint(
        _('{} e-invoices cancelled successfully').format(success),
        title=_('Bulk E-Invoice Cancellation Complete')
    )