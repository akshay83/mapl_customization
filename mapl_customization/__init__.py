import frappe
from mapl_customization.customizations_for_mapl.monkey_patch import do_monkey_patch

__version__ = '0.1.13'

#Monkey Patch
def check_and_patch():
    try:
        if not "mapl_customization" in frappe.get_installed_apps():
            return
        do_monkey_patch()
    except Exception:
        return

check_and_patch()