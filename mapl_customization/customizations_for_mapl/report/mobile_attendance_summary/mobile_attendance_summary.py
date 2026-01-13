# Copyright (c) 2025, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe

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
				"width": 250
			},
			{
				"fieldname":"branch",
				"label":"Branch",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"full_day_count",
				"label":"Full Day Count",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"half_day_count",
				"label":"Half Day Count",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"absent_count",
				"label":"Absent Count",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"total_working_hours",
				"label":"Total Working Hours",
				"fieldtype":"Data",
				"width": 150
			}
	]

	for d in frappe.db.sql(get_query(filters), as_dict=1):
		build_row = {}
		build_row["employee_code"]=d.employee
		build_row["employee_name"]=d.employee_name
		build_row["branch"]=d.branch
		build_row["full_day_count"]=d.full_day_count
		build_row["half_day_count"]=d.half_day_count
		build_row["absent_count"]=d.absent_count
		build_row["total_working_hours"]=d.total_hours_worked
		data.append(build_row)
	return columns, data


def get_query(filters):
	query = """
			WITH
			-- Use employee's branch coordinates instead of static geo_places
			branch_geo AS (
				SELECT
					b.name AS branch_name,
					b.latitude,
					b.longitude,
					b.radius_to_measure
				FROM `tabBranch` b
			),

			first_in AS (
				SELECT *
				FROM (
					SELECT attn.*,
						ROW_NUMBER() OVER (PARTITION BY attn.employee, attn.attendance_date
											ORDER BY attn.in_time ASC) AS rn_in
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
					SELECT attn.*,
						ROW_NUMBER() OVER (PARTITION BY attn.employee, attn.attendance_date
											ORDER BY attn.out_time DESC) AS rn_out
					FROM `tabAttendance` attn
					WHERE attn.docstatus = 1
					AND attn.attendance_date BETWEEN '{from_date}' AND '{to_date}'
					{particular_employee}
				) t
				WHERE rn_out = 1
			),

			attendance_daily AS (
				SELECT
					emp.name AS employee,
					emp.employee_name,
					fi.attendance_date,

					-- IN place: nearest branch within employee's branch radius
					(
						SELECT bg.branch_name
						FROM branch_geo bg
						WHERE bg.branch_name = emp.branch
						AND 6371000 * 2 * ASIN(
								SQRT(
									POWER(SIN(RADIANS(bg.latitude - fi.latitude)/2), 2) +
									COS(RADIANS(fi.latitude)) * COS(RADIANS(bg.latitude)) *
									POWER(SIN(RADIANS(bg.longitude - fi.longitude)/2), 2)
								)
							) <= bg.radius_to_measure
						ORDER BY 6371000 * 2 * ASIN(
									SQRT(
										POWER(SIN(RADIANS(bg.latitude - fi.latitude)/2), 2) +
										COS(RADIANS(fi.latitude)) * COS(RADIANS(bg.latitude)) *
										POWER(SIN(RADIANS(bg.longitude - fi.longitude)/2), 2)
									)
						)
						LIMIT 1
					) AS in_place_name,

					-- OUT place: nearest branch within employee's branch radius
					(
						SELECT bg.branch_name
						FROM branch_geo bg
						WHERE bg.branch_name = emp.branch
						AND 6371000 * 2 * ASIN(
								SQRT(
									POWER(SIN(RADIANS(bg.latitude - lo.latitude)/2), 2) +
									COS(RADIANS(lo.latitude)) * COS(RADIANS(bg.latitude)) *
									POWER(SIN(RADIANS(bg.longitude - lo.longitude)/2), 2)
								)
							) <= bg.radius_to_measure
						ORDER BY 6371000 * 2 * ASIN(
									SQRT(
										POWER(SIN(RADIANS(bg.latitude - lo.latitude)/2), 2) +
										COS(RADIANS(lo.latitude)) * COS(RADIANS(bg.latitude)) *
										POWER(SIN(RADIANS(bg.longitude - lo.longitude)/2), 2)
									)
						)
						LIMIT 1
					) AS out_place_name,

					TIMESTAMPDIFF(MINUTE, fi.in_time, lo.out_time)/60.0 AS hours_worked

				FROM first_in fi
				JOIN last_out lo
				ON fi.employee = lo.employee
				AND fi.attendance_date = lo.attendance_date
				JOIN `tabEmployee` emp
				ON emp.name = fi.employee
			),

			attendance_daily_status AS (
				SELECT
					employee,
					employee_name,
					attendance_date,
					CASE
						WHEN in_place_name IS NULL AND out_place_name IS NULL THEN 'Absent'
						WHEN in_place_name IS NOT NULL AND out_place_name IS NOT NULL AND hours_worked >= 7 THEN 'Full Day'
						ELSE 'Half Day'
					END AS attendance_status,
					hours_worked
				FROM attendance_daily
			)

			SELECT
				ds.employee,
				ds.employee_name,
				emp.branch,
				COUNT(CASE WHEN ds.attendance_status = 'Full Day' THEN 1 END) AS full_day_count,
				COUNT(CASE WHEN ds.attendance_status = 'Half Day' THEN 1 END) AS half_day_count,
				COUNT(CASE WHEN ds.attendance_status = 'Absent' THEN 1 END) AS absent_count,
				ROUND(SUM(ds.hours_worked), 2) AS total_hours_worked
			FROM attendance_daily_status ds
			JOIN `tabEmployee` emp
			ON emp.name = ds.employee
			GROUP BY ds.employee, ds.employee_name, emp.branch
			ORDER BY emp.branch, ds.employee_name;
			"""
	query = query.format(**{
				"from_date": filters.get("from_date"),
				"to_date": filters.get("to_date"),
				"particular_employee": "and employee='{0}'".format(filters.get("employee")) if filters.get("employee") else ""
				})		

	#--DEBUG--print (query)

	return query				