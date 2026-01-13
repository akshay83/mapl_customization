import frappe
import base64
import math
from frappe.utils.file_manager import save_file
from frappe.utils import now_datetime
from erpnext.hr.doctype.attendance.attendance import Attendance
from frappe.utils import flt
from datetime import timedelta

class CustomAttendance(Attendance):
    def validate_duplicate_record(self):
        pass

# Haversine formula to calculate distance in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(flt(lat1))
    phi2 = math.radians(flt(lat2))
    delta_phi = math.radians(flt(lat2) - flt(lat1))
    delta_lambda = math.radians(flt(lon2) - flt(lon1))

    a = math.sin(delta_phi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c  # distance in meters

def get_nearby_places(emp_lat, emp_lon):
    nearby = []
    branches = get_branches()

    for branch in branches:
        distance = haversine(
            emp_lat,
            emp_lon,
            branch["latitude"],
            branch["longitude"]
        )

        if distance <= branch["radius_to_measure"]:
            nearby.append({
                "name": branch["branch"],
                "distance_m": distance,
                "allowed_radius": branch["radius_to_measure"]
            })

    # Sort by nearest branch
    nearby.sort(key=lambda x: x["distance_m"])
    return nearby

@frappe.whitelist()
def get_branches():
    """
    Fetch all branches with geo configuration
    """
    return frappe.db.sql("""
        SELECT
            name AS branch,
            latitude,
            longitude,
            radius_to_measure
        FROM `tabBranch`
        WHERE (latitude IS NOT NULL AND latitude<>0)
          AND (longitude IS NOT NULL AND longitude<>0)
          AND (radius_to_measure IS NOT NULL AND radius_to_measure<>0)
    """, as_dict=True)

@frappe.whitelist()
def get_employee_coordinates_with_location(employee_code, from_date, to_date):
    from mapl_customization.customizations_for_mapl.report.mobile_attendance_report.mobile_attendance_report import execute
    return execute(filters={
        "from_date":from_date,
        "to_date":to_date,
        "include_images":False,
        "employee":employee_code
    })[1]

@frappe.whitelist()
def get_employee_coordinates(employee_code, from_date=None, to_date=None):
    query = """
            WITH first_in AS (
                SELECT *
                FROM (
                    SELECT
                        attn.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY attn.employee, attn.attendance_date
                            ORDER BY attn.in_time ASC
                        ) AS rn
                    FROM `tabAttendance` attn
                    WHERE attn.docstatus = 1
                    {date_range}
                    AND attn.employee = '{employee_code}'
                ) t
                WHERE rn = 1
            ),
            last_out AS (
                SELECT *
                FROM (
                    SELECT
                        attn.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY attn.employee, attn.attendance_date
                            ORDER BY attn.out_time DESC
                        ) AS rn
                    FROM `tabAttendance` attn
                    WHERE attn.docstatus = 1
                    {date_range}
                    AND attn.employee = '{employee_code}'
                ) t
                WHERE rn = 1
            )

            SELECT
                attn.employee,
                emp.employee_name,
                attn.attendance_date,
                'IN' AS point_type,
                attn.latitude,
                attn.longitude,
                cast(attn.in_time as time) AS point_time
            FROM first_in attn
            JOIN `tabEmployee` emp ON emp.name = attn.employee
            WHERE attn.latitude IS NOT NULL AND attn.longitude IS NOT NULL

            UNION ALL

            SELECT
                attn.employee,
                emp.employee_name,
                attn.attendance_date,
                'OUT' AS point_type,
                attn.latitude,
                attn.longitude,
                cast(attn.out_time as time) AS point_time
            FROM last_out attn
            JOIN `tabEmployee` emp ON emp.name = attn.employee
            WHERE attn.latitude IS NOT NULL AND attn.longitude IS NOT NULL

            ORDER BY attendance_date ASC, point_type ASC;
            """

    query = query.format(**{
                "date_range": "AND attn.attendance_date BETWEEN '{0}' AND '{1}'".format(from_date, to_date) if (from_date and to_date) else "",
                "employee_code": employee_code
            })		        
    #--DEBUG--print (query)
    return_value = None
    try:
        return_value = frappe.db.sql(query, as_dict=1)#[0].geolocation_geojson
    except Exception as e:
        pass
    return return_value

@frappe.whitelist(allow_guest=True)
def get_employee_descriptors():
    """Return registered employee face descriptors"""
    employees = frappe.get_all("Employee", filters={"status":"Active"}, fields=["name", "face_descriptor", "employee_name"])
    # face_descriptor should be stored as list of 128 floats
    result = []
    for e in employees:
        if e.face_descriptor:
            result.append({
                "employee_name": e.employee_name,
                "employee_id": e.name,
                "descriptor": e.face_descriptor
            })
    return result

@frappe.whitelist(allow_guest=True)
def post_attendance(employee, latitude, longitude, image_data=None):
    last = frappe.db.get_list(
        "Attendance",
        filters = {"employee":employee},
        order_by = "creation desc",
        pluck = "creation",
        page_length=1,
        ignore_permissions=True
    )

    if last and now_datetime() - last[0] < timedelta(minutes=15):        
        frappe.throw("Attendance already marked in the last 15 minutes.")    

    """Save daily attendance with photo & GPS"""
    # Create Attendance record
    attendance = frappe.new_doc("Attendance")
    attendance.employee = employee
    attendance.status = "Present"
    attendance.attendance_date=now_datetime().date()
    attendance.in_time=now_datetime()
    attendance.out_time=now_datetime()
    attendance.latitude=flt(latitude,9)
    attendance.longitude=flt(longitude,9)
    attendance.image_data=image_data
    attendance.save(ignore_permissions=True)
    attendance.submit()
    frappe.db.commit()
    return attendance.name


@frappe.whitelist(allow_guest=True)
def update_face_descriptor(employee, registration_code, descriptor, image_data=None):
    """
    Update the face_descriptor field for an employee.
    
    Args:
        employee (str): Employee name or ID.
        descriptor (list): List of 128 float numbers (face descriptor).
    """
    if not employee or not descriptor:
        frappe.throw("Employee and descriptor are required")
    
    if not registration_code:
        frappe.throw("Registration code is required")

    if isinstance(descriptor, str):
        import json
        descriptor = json.loads(descriptor)        
    
    # Ensure descriptor is a list of floats
    if not isinstance(descriptor, list) or len(descriptor) != 128:
        frappe.throw("Descriptor must be a list of 128 numbers")

    # Convert all values to float to be safe
    descriptor = [float(x) for x in descriptor]

    # Serialize to JSON string
    descriptor_json = json.dumps(descriptor)    

    # Fetch employee ignoring permissions
    emp = frappe.get_doc("Employee", employee.upper())
    if not emp.registration_code:
        frappe.throw("Registration not Allowed")

    if str(emp.registration_code) != str(registration_code):
        frappe.throw("Registration code Does Not Match!")
    
    emp.face_descriptor = descriptor_json
    emp.registration_code = None
    emp.face_detector_image = image_data

    # Save ignoring permissions
    emp.save(ignore_permissions=True)
    frappe.db.commit()    

    return {"status": "success", "message": f"Face descriptor updated for {employee}"}