frappe.query_reports['Simple Stock Report'] = {

	"filters": [

					{
					  "fieldname":"item_code",
					  "label":__("Item Code"),
					  "fieldtype": "Link",
					  "options":"Item",
					  "width":"200"
					},
					{
					  "fieldname":"from_date",
					  "label":__("From Date"),
					  "fieldtype": "Date",
					  "width":"100",
					  "default":sys_defaults.year_start_date
					},
					{
					  "fieldname":"to_date",
					  "label":__("To Date"),
					  "fieldtype": "Date",
					  "default":frappe.datetime.get_today(),
					  "width":"100"
					},
					{
					  "fieldname":"warehouse",
					  "label":__("Warehouse"),
					  "fieldtype": "Link",
					  "options":"Warehouse",
					  "width":"100"
					},
					{
					  "fieldname":"brand",
					  "label":"Brand",
					  "fieldtype":"Link",
					  "options":"Brand",
					  "width":"100"
					},
					{
					  "fieldname":"company",
					  "label":__("Company"),
					  "fieldtype": "Link",
					  "options":"Company",
					  "default":frappe.defaults.get_user_default("Company"),
					  "width":"150"
					}
			   ]	


	}
