# Copyright (c) 2026, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
import math
from frappe.utils import (
    format_time,
    getdate,
    add_days,
    time_diff_in_seconds
)
from mapl_customization.customizations_for_mapl.employee_gps_attendance import get_nearby_places

# ---------------------------
# REPORT ENTRY POINT
# ---------------------------
def execute(filters=None):
    columns = get_columns(filters)
    rows = frappe.db.sql(get_query(), filters, as_dict=1)
    data = build_data(rows, filters)
    return columns, data

# ---------------------------
# DATE RANGE
# ---------------------------
def get_date_range(from_date, to_date):
    dates = []
    current = getdate(from_date)
    end = getdate(to_date)

    while current <= end:
        dates.append(current)
        current = add_days(current, 1)

    return dates

# ---------------------------
# COLUMNS
# ---------------------------
def get_columns(filters):
    columns = [
        {
            "fieldname": "employee_code",
            "label": "Employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "fieldname": "employee_name",
            "label": "Employee Name",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "employee_branch",
            "label": "Employee Base Branch",
            "fieldtype": "Data",
            "width": 160
        }
    ]

    for d in get_date_range(filters.from_date, filters.to_date):
        key = d.strftime("%Y_%m_%d")
        columns.append({
            "fieldname": f"day_{key}",
            "label": d.strftime("%d-%b"),
            "fieldtype": "Data",
            "width": 190
        })

    # Monthly Totals
    columns.extend([
        {
            "fieldname": "present_days",
            "label": "Present Days",
            "fieldtype": "Int",
            "width": 110
        },
        {
            "fieldname": "total_hours",
            "label": "Total Hours",
            "fieldtype": "Float",
            "width": 110
        },
        {
            "fieldname": "avg_hours",
            "label": "Avg Hours",
            "fieldtype": "Float",
            "width": 100
        }
    ])

    return columns


# ---------------------------
# SQL QUERY
# ---------------------------
def get_query():
    return """
        SELECT
            attn.employee,
            emp.employee_name,
            emp.branch,
            attn.attendance_date,
            MIN(attn.in_time)  AS min_in_time,
            MAX(attn.out_time) AS max_out_time,

            -- IN location
            SUBSTRING_INDEX(GROUP_CONCAT(attn.latitude ORDER BY attn.in_time), ',', 1) AS in_latitude,
            SUBSTRING_INDEX(GROUP_CONCAT(attn.longitude ORDER BY attn.in_time), ',', 1) AS in_longitude,

            -- OUT location
            SUBSTRING_INDEX(GROUP_CONCAT(attn.latitude ORDER BY attn.out_time DESC), ',', 1) AS out_latitude,
            SUBSTRING_INDEX(GROUP_CONCAT(attn.longitude ORDER BY attn.out_time DESC), ',', 1) AS out_longitude

        FROM `tabAttendance` attn
        JOIN `tabEmployee` emp ON emp.name = attn.employee
        WHERE
            attn.docstatus = 1
            AND attn.attendance_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY attn.employee, attn.attendance_date
        ORDER BY emp.branch, emp.employee_name, attn.attendance_date
    """

# ---------------------------
# DATA BUILDER
# ---------------------------
def build_data(rows, filters):
    data = {}

    for r in rows:
        emp = r.employee
        date_key = r.attendance_date.strftime("%Y_%m_%d")

        if emp not in data:
            data[emp] = {
                "employee_code": emp,
                "employee_name": r.employee_name,
				"employee_branch": r.branch,
                "present_days": 0,
                "total_hours": 0.0
            }

        # Day cell
        cell_text, worked_hours = format_day_cell(r)
        data[emp][f"day_{date_key}"] = cell_text

        if worked_hours > 0:
            data[emp]["present_days"] += 1
            data[emp]["total_hours"] += worked_hours

    # Average hours
    for emp in data.values():
        if emp["present_days"]:
            emp["avg_hours"] = round(emp["total_hours"] / emp["present_days"], 2)
        else:
            emp["avg_hours"] = 0

        emp["total_hours"] = round(emp["total_hours"], 2)

    return list(data.values())

# ---------------------------
# CELL FORMATTER
# ---------------------------
def format_day_cell(row):
    if not row.min_in_time or not row.max_out_time:
        return "-", 0

    in_time = format_time(row.min_in_time)
    out_time = format_time(row.max_out_time)

    seconds = time_diff_in_seconds(row.max_out_time, row.min_in_time)
    hours = round(seconds / 3600, 2) if seconds > 0 else 0

    # In Place
    in_nearby = get_nearby_places(row.in_latitude, row.in_longitude)
    in_place = in_nearby[0]["name"] if in_nearby else "Unknown"

    # Out Place
    out_nearby = get_nearby_places(row.out_latitude, row.out_longitude)
    out_place = out_nearby[0]["name"] if out_nearby else "Unknown"

    text = (
        f"In: {in_time} ({in_place})\n"
        f"Out: {out_time} ({out_place})"
    )
    return text, hours