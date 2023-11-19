#Based on https://github.com/aldinokemal/go-whatsapp-web-multidevice
#Configure SMS Settings to Match with Whatsapp API First
from __future__ import unicode_literals
import frappe
import six
import time
from frappe.core.doctype.sms_settings.sms_settings import validate_receiver_nos, create_sms_log, get_headers
from frappe import _, throw, msgprint
from frappe.utils import nowdate
from frappe.model.document import Document
from six import string_types

def check_country_code(receiver_list):
    country_list = []
    for l in receiver_list:
        if l.startswith("+"):
            l =l[1:]
        if not l.startswith("91"):
            l = "91"+l
        country_list.append(l)
    return country_list

def get_base_url(url):
    if url:
        return url.rsplit('/', 1)[0]
    else:
        msgprint(_("Please Update SMS Settings"))

def send_whatsapp_image_via_gateway(arg):
    ss = frappe.get_doc('SMS Settings', 'SMS Settings')
    headers = get_headers(ss)
    use_json = headers.get("Content-Type") == "application/json"

    request_args = {"caption": arg.get('caption')}
    for d in ss.get("parameters"):
        if not d.header:
            request_args[d.parameter] = d.value

    base_url = get_base_url(ss.sms_gateway_url)
    whatsapp_send_url = base_url+'/image'
    files = {"image":("image.jpg", arg.get('binary_image'), "image/jpeg")}

    request_args["view_once"] = False
    request_args["compress"] = False

    success_list = []
    sleep_time = arg.get('sleep',0)
    for d in arg.get('receiver_list'):
        request_args[ss.receiver_parameter] = d
        #--DEBUG--print (request_args)
        #--DEBUG--print (headers)
        status = send_request(whatsapp_send_url, request_args, headers=headers, files=files, use_post=True, use_json=False)

        if 200 <= status < 300:
            success_list.append(d)
        
        if  sleep_time > 0:
            print ("Waiting for %s seconds".format(sleep_time))
            time.sleep(sleep_time)

    if len(success_list) > 0:
        request_args.update(arg)
        #--DISABLED--create_sms_log(request_args, success_list)
        if arg.get('success_msg'):
            frappe.msgprint(_("Whatsapp sent to following numbers: {0}").format("\n" + "\n".join(success_list)))

@frappe.whitelist()
def send_whatsapp_image(receiver_list, caption, image_link=None, success_msg=False, sleep=0):
    receiver_list = sanitize_receiver_list(receiver_list)
    receiver_list = validate_receiver_nos(receiver_list)
    receiver_list = check_country_code(receiver_list)
    if not image_link:
        frappe.throw("Invalid Image URL")
    try:
        from urllib.request import urlopen
        binary_image = urlopen(image_link).read()
    except Exception:
        frappe.throw("Invalid Image URL")

    arg = {
        'receiver_list' : receiver_list,
        'caption'		: caption,
        'image_link'    : image_link,
        'binary_image'  : binary_image,
        'success_msg'   : success_msg,
        'sleep'         : sleep
    }

    if frappe.db.get_value('SMS Settings', None, 'sms_gateway_url'):
        send_whatsapp_image_via_gateway(arg)
    else:
        msgprint(_("Please Update SMS Settings"))

def sanitize_receiver_list(receiver_list):
    import json
    if isinstance(receiver_list, string_types):
        receiver_list = json.loads(receiver_list)
        if not isinstance(receiver_list, list):
            receiver_list = [receiver_list]
    return receiver_list

def send_request(gateway_url, params, headers=None, files=None, use_post=False, use_json=False):
    import requests

    if not headers:
        headers = get_headers()
    kwargs = {"headers": headers}

    if use_json:
        kwargs["json"] = params
    elif use_post:
        kwargs["data"] = params
    else:
        kwargs["params"] = params
    if files:
        kwargs["files"] = files

    if use_post:
        response = requests.post(gateway_url, **kwargs)
    else:
        response = requests.get(gateway_url, **kwargs)
    #--DEBUG--print (response.content)
    response.raise_for_status()
    return response.status_code