frappe.pages['attendance-location'].on_page_load = function(wrapper) {
		let page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Track Employee Location',
			single_column: true
		});

		let geo_dialog = new frappe.ui.Dialog({
			title: 'Select Location',
			fields: [
				{
					fieldtype: 'Geolocation',
					fieldname: 'map'
				}
			],
			on_page_show: function() {
				$(".modal.fade.show").hide();		
				$(".modal-backdrop.fade.show").hide();
				$(".page-form.row").css({"z-index":"20","position":"relative"});
			}
		});		
		// Add fields
		let from_date_field = page.add_field({
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		});

		let to_date_field = page.add_field({
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		});

		let employee_code_field = page.add_field({
			label: 'Employee Code',
			fieldtype: 'Link',
			fieldname: 'employee_code',
			options: "Employee"
		});
	
		let employee_name_field = page.add_field({
			label: 'Employee Name',
			fieldtype: 'Data',
			fieldname: 'employee_name',
			read_only: 1
		});	

		page.fields_dict.employee_code.df.onchange = function () { get_location_data(page, geo_dialog); }
		page.fields_dict.from_date.df.onchange = function () { get_location_data(page, geo_dialog); }
		page.fields_dict.to_date.df.onchange = function () { get_location_data(page, geo_dialog); }
		//--DEBUG--console.log(page);

		let map_container = $('<div></div>').css({
			width: '100%',
			height: '400px',
			marginTop: '15px', // space below fields
			position: 'relative', // ensure normal stacking
			zIndex: 10
		}).appendTo(page.body);
	
		// Attach dialog wrapper to the container on the page
		$(geo_dialog.wrapper).appendTo(map_container);
	
		// Hide dialog header for a clean embedded look
		geo_dialog.header.hide();
		geo_dialog.$wrapper.css({ border: 'none', boxShadow: 'none', position: 'relative', zIndex: 10 });

		// Show the dialog to render the map
		geo_dialog.show();	
};

function showCoordinates(employee, from_date, to_date, geo_map) {
		  const geojson = {
			type: "FeatureCollection",
			features: [
			  {
				type: "Feature",
				properties: {},
				geometry: {
				  type: "Point",
				  coordinates: [72.854548, 19.096511]
				}
			  }
			]
		  };	  
		  frappe.call({
			method:
			  "mapl_customization.customizations_for_mapl.employee_gps_attendance.get_employee_coordinates",
			args: {
			  employee_code: employee,
			  from_date: from_date,
			  to_date: to_date
			},
			callback: (r) => {
				//-DEBUG--console.log(r);				
				if (r.message && r.message.length) {
					build_geojson(r.message, geo_map);
				} else {
					clear_map(geo_map);
				}
			},
			error: (err) => {
			  console.error(err);
			},
		  });
}

let geojsonLayer;  // global or page-level variable
function clear_map(geo_map_control) {
    // Remove existing layer if any
    if (geojsonLayer) {
        geo_map_control.map.removeLayer(geojsonLayer);
    }
}

function build_geojson(message, geo_map_control) {
    let map = geo_map_control.map;
	clear_map(geo_map_control);

    let features = message.map(d => ({
        type: "Feature",
        properties: {
            employee: d.employee,
            employee_name: d.employee_name,
            date: d.attendance_date,
            type: d.point_type,
            color: d.point_type === "IN" ? "#24a159" : "#400f0a",
			time: d.point_time
        },
        geometry: {
            type: "Point",
            coordinates: [d.longitude, d.latitude]
        }
    }));

    let geojson = { type: "FeatureCollection", features };

    geojsonLayer = L.geoJSON(geojson, {
        pointToLayer: function(feature, latlng) {
            return L.circleMarker(latlng, {
                radius: 8,
                fillColor: feature.properties.color,
                color: "#000",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            });
        },
        onEachFeature: function(feature, layer) {
			//-DEBUG--console.log(feature.properties);
			//-DEBUG--console.log(`Time ${feature.properties.time}`);
            layer.bindPopup(
                `Employee: ${feature.properties.employee_name}<br>` +
                `Date: ${frappe.datetime.str_to_user(feature.properties.date)}<br>` +
                `Type: ${feature.properties.type}<br>`+
				`Time: ${feature.properties.time}`
            );
        }
    }).addTo(map);

    // Fit map to show all markers
    if (features.length) {
        let bounds = geojsonLayer.getBounds();
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

function get_location_data(page, geo_dialog) {
	//-DEBUG--console.log(page);
	let employee = page.fields_dict.employee_code.get_value();
	if(!employee) {
		page.fields_dict.employee_name.set_value('');
		return;
	}
	frappe.db.get_value("Employee", employee, "employee_name", function(value) {					
		page.fields_dict.employee_name.set_value(value["employee_name"]);
		showCoordinates(employee, page.fields_dict.from_date.get_value(), page.fields_dict.to_date.get_value(), geo_dialog.fields_dict.map);
	});
}	


/*
	  const geojson = {
		type: "FeatureCollection",
		features: [
		  {
			type: "Feature",
			properties: {},
			geometry: {
			  type: "Point",
			  coordinates: [72.854548, 19.096511]
			}
		  }
		]
	  };  
	  frm.set_value("location", JSON.stringify(geojson));

*/