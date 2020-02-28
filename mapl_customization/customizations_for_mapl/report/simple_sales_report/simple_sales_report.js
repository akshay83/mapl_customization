frappe.query_reports['Simple Sales Report'] = {
        "filters": [
                {
                        "fieldname":"from_date",
                        "label":__("From Date"),
                        "fieldtype": "Date",
                        "default": get_today()
                },
                {
                        "fieldname":"to_date",
                        "label":__("To Date"),
                        "fieldtype": "Date",
                        "default": get_today()
                },
                {
                        "fieldname":"let",
                        "label":__("Letter Head"),
                        "fieldtype": "Link",
                        "options": "Letter Head",
                        "default": "%%"
                },
                {
                        "fieldname":"brand",
                        "label":__("Brand"),
                        "fieldtype": "Link",
                        "options": "Brand",
                        "default": "%%"
                },
                {
                        "fieldname":"item_group",
                        "label":__("Item Group"),
                        "fieldtype": "Link",
                        "options": "Item Group",
                        "default": "%%"
                },
                {
                        "fieldname":"show_draft",
                        "label":__("Show Entries"),
                        "fieldtype": "Select",
                        "options": "Submitted\nInclude Draft",
                        "default": "Submitted"
                }
        ]
}

