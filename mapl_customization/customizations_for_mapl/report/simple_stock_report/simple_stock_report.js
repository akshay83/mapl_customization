frappe.query_reports['Simple Stock Report'] = {

	"filters": [

					{
					  "fieldname":"item_code",
					  "label":__("Item Code"),
					  "fieldtype": "Link",
                      "options":"Item",
					},
					{
					  "fieldname":"from_date",
					  "label":__("From Date"),
					  "fieldtype": "Date",
					  "default":sys_defaults.year_start_date
					},
					{
					  "fieldname":"to_date",
					  "label":__("To Date"),
					  "fieldtype": "Date",
					  "default":frappe.datetime.get_today()
					},
					{
					  "fieldname":"warehouse",
					  "label":__("Warehouse"),
					  "fieldtype": "Link",
					  "options":"Warehouse"
					},
					{
					  "fieldname":"company",
					  "label":__("Company"),
					  "fieldtype": "Link",
					  "options":"Company",
                      "default":frappe.defaults.get_user_default("Company")
					}
			   ]	


	}