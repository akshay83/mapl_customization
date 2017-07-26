frappe.query_reports['Finance Outstanding'] = {
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
                        "fieldname":"finance_co",
                        "label":__("Finance Company"),
                        "fieldtype": "Link",
                        "options": "Hypothecation Company",
                        "default": "%%"
                }

        ]
}

