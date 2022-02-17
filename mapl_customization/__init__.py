import frappe
from mapl_customization.customizations_for_mapl.monkey_patch import do_monkey_patch
from frappe.utils import cint

__version__ = '0.1.13'

#Monkey Patch
def check_and_patch():
    try:
        if not is_this_app_installed():
            return
        do_monkey_patch()
    except Exception:
        return

def is_this_app_installed():    
    return cint("mapl_customization" in frappe.get_installed_apps())

check_and_patch()