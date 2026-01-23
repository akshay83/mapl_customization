# Copyright (c) 2025, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
import math
from frappe.utils import format_datetime, format_time, cint
from mapl_customization.customizations_for_mapl.employee_gps_attendance import get_nearby_places

def execute(filters=None):
	columns, data = [], []
	columns = [
			{
				"fieldname":"employee_code",
				"label":"Employee Code",
				"fieldtype":"Link",
				"options": "Employee",
				"width": 100
			},
			{
				"fieldname":"employee_name",
				"label":"Employee Name",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"attendance_date",
				"label":"Attendance Date",
				"fieldtype":"Date",
				"width": 100
			},
			{
				"fieldname":"in_time",
				"label":"In Time",
				"fieldtype":"Time",
				"width": 100
			},
			{
				"fieldname":"out_time",
				"label":"Out Time",
				"fieldtype":"Time",
				"width": 100
			},
			{
				"fieldname":"in_lat_long",
				"label":"In Lat/Long",
				"fieldtype":"Data",
				"width": 125
			},
			{
				"fieldname":"in_place",
				"label":"In Place",
				"fieldtype":"Data",
				"width": 75
			},
			{
				"fieldname":"out_lat_long",
				"label":"Out Lat/Long",
				"fieldtype":"Data",
				"width": 125
			},
			{
				"fieldname":"out_place",
				"label":"Out Place",
				"fieldtype":"Data",
				"width": 75
			}
	]
	if cint(filters.get("include_images")):
		columns.extend([
			{
				"fieldname":"in_image",
				"label":"In Image",
				"fieldtype":"Long Text",
				"width": 125
			},
			{
				"fieldname":"out_image",
				"label":"Out Image",
				"fieldtype":"Long Text",
				"width": 125
			}
		])

	if not filters.get("order_by"):
		del filters["order_by"]

	for d in frappe.db.sql(get_query(filters), as_dict=1):
		build_row = {}
		build_row["employee_code"] = d.employee
		build_row["employee_name"] = d.employee_name
		build_row["branch"]  = d.branch
		build_row["attendance_date"] = d.attendance_date
		build_row["in_time"] = format_time(d.first_in_time)
		build_row["out_time"] = format_time(d.last_out_time)

		# Build lat/long string
		build_row["in_lat_long"] = f"{d.in_latitude},{d.in_longitude}"
		nearby_places = get_nearby_places(d.in_latitude, d.in_longitude)
		if nearby_places:
			place = nearby_places[0]
			build_row["in_place"] = (
				f"{place['name']} "
				f"({round(place['distance_m'], 2)} m)"
			)
		else:
			build_row["in_place"] = "Unknown"

		# Build lat/long string
		build_row["out_lat_long"] = f"{d.out_latitude},{d.out_longitude}"
		nearby_places = get_nearby_places(d.out_latitude, d.out_longitude)
		if nearby_places:
			place = nearby_places[0]
			build_row["out_place"] = (
				f"{place['name']} "
				f"({round(place['distance_m'], 2)} m)"
			)
		else:
			build_row["out_place"] = "Unknown"

		if cint(filters.get("include_images")):
			build_row["in_image"] = d.in_image
			build_row["out_image"] = d.out_image
		data.append(build_row)
	
	return columns, data

def get_query(filters=None):
	query = """
				WITH first_in AS (
					SELECT *
					FROM (
						SELECT
							attn.*,
							ROW_NUMBER() OVER (PARTITION BY attn.employee, attn.attendance_date ORDER BY attn.in_time ASC) AS rn_in
						FROM `tabAttendance` attn
						WHERE attn.docstatus = 1
						AND attn.attendance_date BETWEEN '{from_date}' AND '{to_date}'
						{particular_employee}
					) t
					WHERE rn_in = 1
				),
				last_out AS (
					SELECT *
					FROM (
						SELECT
							attn.*,
							ROW_NUMBER() OVER (PARTITION BY attn.employee, attn.attendance_date ORDER BY attn.out_time DESC) AS rn_out
						FROM `tabAttendance` attn
						WHERE attn.docstatus = 1
						AND attn.attendance_date BETWEEN '{from_date}' AND '{to_date}'
						{particular_employee}
					) t
					WHERE rn_out = 1
				)
				SELECT
					emp.name AS employee,
					emp.employee_name,
					emp.branch,
					fi.attendance_date,

					-- First IN and Last OUT times
					fi.in_time  AS first_in_time,
					lo.out_time AS last_out_time,

					-- IN coordinates
					fi.latitude  AS in_latitude,
					fi.longitude AS in_longitude,

					-- OUT coordinates
					lo.latitude  AS out_latitude,
					lo.longitude AS out_longitude

					-- Images
					{include_images}

				FROM first_in fi
				JOIN last_out lo
					ON fi.employee = lo.employee
				AND fi.attendance_date = lo.attendance_date
				JOIN `tabEmployee` emp
					ON emp.name = fi.employee
				ORDER BY {order_by}
			"""
	query = query.format(**{
				"include_images": ",fi.image_data AS in_image,lo.image_data AS out_image" if cint(filters.get("include_images")) else "",
				"from_date": filters.get("from_date"),
				"to_date": filters.get("to_date"),
				"particular_employee": "and employee='{0}'".format(filters.get("employee")) if filters.get("employee") else "",
				"order_by": filters.get("order_by", "fi.attendance_date, emp.employee_name")
				})

	#--DEBUG--print (query)
	return query	