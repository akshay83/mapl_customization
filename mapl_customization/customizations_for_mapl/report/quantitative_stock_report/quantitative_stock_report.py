# Copyright (c) 2024, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
import json
import os

def execute(filters=None):
	columns, data = [], []
	data = execute_query(filters)
	insert_categories(data)
	columns  = extract_columns(data) if len(data) > 0 else []
	return columns, data

def load_map():
	with open(os.path.join(os.path.dirname(__file__), "map.json")) as file:
		map_json = json.loads(file.read())
	lowercase_map = {k.lower():v for k,v in map_json.items()}
	return lowercase_map

def insert_categories(data, group_key="item_group"):
	#group_key identifies the column name returned by SQL Query
	#As Categories depend on Item_Group, Check whether it exits in data or not
	if not any(group_key in i for i in data[0].keys()):
		return
	#Insert Default Values for the First Data Row, other wise "extract_columns" won't handle the Category & Sub Category Columns well
	data[0].update({"Category":None})
	data[0].update({"Sub Category":None})
	category_map = load_map()	
	for d in data:
		item_group = category_map.get(d.get(group_key).lower())
		if not item_group:
			continue
		d.update({"Category":item_group.get("Category")})
		d.update({"Sub Category":item_group.get("Sub Category")})

def execute_query(filters=None):
	query = """
				SELECT
				item.name,
				item.item_group,
				item.brand,
				(
						SELECT ifnull(Sum(stock_value_difference),0)
						FROM   `tabStock Ledger Entry`
						WHERE  posting_date < '{from_date}'
						AND    item_code = item.name
				) AS `Opening Value`,
				(
						SELECT ifnull(Sum(actual_qty),0)
						FROM   `tabStock Ledger Entry`
						WHERE  posting_date < '{from_date}'
						AND    item_code = item.name
				) AS `Opening Qty`,  
				(
						SELECT DISTINCT si.income_account
						FROM            `tabSales Invoice Item` si,
										`tabSales Invoice` inv
						WHERE           inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND             item.name = si.item_code
						AND             inv.docstatus=1
						AND             si.parent=inv.name
				) AS `Sales Income Account`,
				(
						SELECT ifnull(sum(si.net_amount),0)
						FROM   `tabSales Invoice Item` si,
								`tabSales Invoice` inv
						WHERE  inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    item.name = si.item_code
						AND    inv.docstatus=1
						AND    si.parent=inv.name    
				) AS `Sales Value`,
				(
						SELECT ifnull(sum(outward.qty),0)
						FROM   ((select inv.posting_date, si.qty, inv.docstatus, si.item_code from `tabSales Invoice Item` si,
								`tabSales Invoice` inv where inv.name=si.parent and inv.update_stock=1) union all 
								(select dn.posting_date, di.qty, dn.docstatus, di.item_code from `tabDelivery Note Item` di,
								`tabDelivery Note` dn where dn.name=di.parent)) outward
						WHERE  outward.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    outward.docstatus=1
						AND    outward.item_code=item.name
				) AS `Sales Qty`,  
				(
						SELECT ifnull(sum(if((si.s_warehouse is not null and t_warehouse is null),-1*si.qty, if((si.s_warehouse is null and t_warehouse is not null),si.qty,0))),0)
						FROM   `tabStock Entry Detail` si,
								`tabStock Entry` inv
						WHERE  inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    item.name = si.item_code
						AND    inv.docstatus=1
						AND    si.parent=inv.name
				) AS `Adjustment Qty`,    
				(
						SELECT ifnull(sum(if((inv.total_incoming_value <> 0 and inv.total_outgoing_value <> 0 and inv.total_incoming_value <> inv.total_outgoing_value),
						if((si.s_warehouse is not null and t_warehouse is null), -1*si.amount,
							if((si.s_warehouse is null and t_warehouse is not null), si.amount, 0)),0)),0)
						FROM   `tabStock Entry Detail` si,
								`tabStock Entry` inv
						WHERE  inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    item.name = si.item_code
						AND    inv.docstatus=1
						AND    si.parent=inv.name
				) AS `Adjustment Value`,    

				(
						SELECT ifnull(sum(si.net_amount),0)
						FROM   `tabPurchase Invoice Item` si,
								`tabPurchase Invoice` inv
						WHERE  inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    item.name = si.item_code
						AND    inv.docstatus=1
						AND    si.parent=inv.name
				) AS `Purchase Value`,
				(
						SELECT ifnull(sum(si.qty),0)
						FROM   `tabPurchase Invoice Item` si,
								`tabPurchase Invoice` inv
						WHERE  inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    item.name = si.item_code
						AND    inv.docstatus=1
						AND    si.parent=inv.name
				) AS `Purchase Qty`,  
				(
						SELECT DISTINCT si.expense_account
						FROM            `tabPurchase Invoice Item` si,
										`tabPurchase Invoice` inv
						WHERE           inv.posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND             item.name = si.item_code
						AND             inv.docstatus=1
						AND             si.parent=inv.name
				) AS `Purchase Expense Account`,
				(
						SELECT ifnull(sum(stock_value_difference),0)
						FROM   `tabStock Ledger Entry`
						WHERE  item_code = item.item_code
						AND    posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    voucher_type in ('Sales Invoice','Delivery Note')
				) AS `Cost of Goods Sold`,
				(
						SELECT ifnull(sum(actual_qty),0)
						FROM   `tabStock Ledger Entry`
						WHERE  item_code = item.item_code
						AND    posting_date BETWEEN '{from_date}' AND '{to_date}'
						AND    voucher_type in ('Sales Invoice','Delivery Note')
				) AS `Goods Sold Qty`,  
				(
						SELECT ifnull(sum(stock_value_difference),0)
						FROM   `tabStock Ledger Entry`
						WHERE  posting_date <= '{to_date}'
						AND    item_code = item.name
				) AS `Closing Value`,
				(
						SELECT ifnull(sum(actual_qty),0)
						FROM   `tabStock Ledger Entry`
						WHERE  posting_date <= '{to_date}'
						AND    item_code = item.name
				) AS `Closing Qty`  
				FROM
					`tabItem` item
				WHERE
					item.is_stock_item = 1
				GROUP BY
					item.name
				HAVING
					abs(`Opening Qty`)+abs(`Purchase Qty`)+abs(`Sales Qty`)+abs(`Closing Qty`)>0					
				ORDER BY
					item.name
	"""
	query = query.format(**{
                    "from_date": filters.get("from_date"),
                    "to_date": filters.get("to_date")
                    })
	return frappe.db.sql(query, as_dict=1)

def extract_columns(query_result):
    list_keys = query_result[0].keys()
    columns = []
    for key in list_keys:
        broken_key = key.split(":")
        link = None
        try:
            link = broken_key[1].split("/")
        except:
            pass
        columns.append({
			"fieldname":key,
			"label":broken_key[0],
			"fieldtype:":link[0] if link else "Data",
            "options": link[1] if (link and len(link)>1) else None,
			"width": broken_key[2] if len(broken_key)>1 else 100,
            "default": 0 if (link and link[0].lower() in ("currency","float")) else None
        })
    #--DEBUG--print (columns)
    return columns
