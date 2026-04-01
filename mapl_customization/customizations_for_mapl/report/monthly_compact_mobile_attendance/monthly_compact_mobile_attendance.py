# Copyright (c) 2026, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
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
    rows = frappe.db.sql(get_query(filters), as_dict=1)
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
            "fieldname": "half_days",
            "label": "Half Days",
            "fieldtype": "Int",
            "width": 110
        },
        {
            "fieldname": "absent_days",
            "label": "Absent Days",
            "fieldtype": "Int",
            "width": 110
        },
        {
            "fieldname": "total_hours",
            "label": "Total Hours",
            "fieldtype": "Float",
            "width": 110
        }
    ])

    return columns


# ---------------------------
# SQL QUERY
# ---------------------------
def get_query(filters):
    query = """
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
            AND attn.attendance_date BETWEEN '{from_date}' AND '{to_date}'
            {set_branch}
            {set_employee}
        GROUP BY attn.employee, attn.attendance_date
        ORDER BY emp.branch, emp.employee_name, attn.attendance_date
    """

    query = query.format(**{
                "from_date": filters.get("from_date"),
                "to_date": filters.get("to_date"),
                "set_employee": "and attn.employee='{0}'".format(filters.get("employee")) if filters.get("employee") else "",
                "set_branch": "and emp.branch='{0}'".format(filters.get("branch")) if filters.get("branch") else ""
            })

    return query

# ---------------------------
# DATA BUILDER
# ---------------------------
def build_data(rows, filters):
    data = {}
    employee_attendance = {}

    # Get all the attendance data for the selected date range
    for r in rows:
        emp = r.employee
        date_key = r.attendance_date.strftime("%Y_%m_%d")

        # Initialize employee record if not already present
        if emp not in data:
            data[emp] = {
                "employee_code": emp,
                "employee_name": r.employee_name,
                "employee_branch": r.branch,
                "present_days": 0,
                "half_days": 0,
                "absent_days": 0,
                "total_hours": 0.0
            }

        # Day cell
        cell_text, worked_hours = format_day_cell(r)
        data[emp][f"day_{date_key}"] = cell_text

        # Mark attendance data for later reference
        employee_attendance[(emp, date_key)] = worked_hours

        # If there's worked hours, increase present days and total hours
        if worked_hours >= 0:
            data[emp]["present_days"] += 1
            data[emp]["total_hours"] += worked_hours
            # Count Half Days (if hours worked < 7.5)
            if worked_hours < 7.5:
                data[emp]["half_days"] += 1
        else:
            data[emp]["absent_days"] += 1

    # Now we need to mark all absent days for the entire date range (irrespective of attendance)
    for emp in data:
        # Iterate through the date range
        date_range = get_date_range(filters.from_date, filters.to_date)
        
        for d in date_range:
            date_key = d.strftime("%Y_%m_%d")
            
            # If no attendance record exists for this date, mark it as absent
            if (emp, date_key) not in employee_attendance:
                data[emp]["absent_days"] += 1
                data[emp][f"day_{date_key}"] = "Absent"

    return list(data.values())

# ---------------------------
# CELL FORMATTER
# ---------------------------
def format_day_cell(row):
    if not row.min_in_time or not row.max_out_time:
        return "-", -1

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