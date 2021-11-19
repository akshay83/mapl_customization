import frappe
from mapl_customization.customizations_for_mapl.monkey_patch import do_monkey_patch

#Monkey Patch
def check_and_patch():
    if not "mapl_customization" in frappe.get_installed_apps():
        return
    do_monkey_patch()

check_and_patch()