frappe.pages['attendance-location'].on_page_load = function (wrapper) {
	// ---------------- Page ----------------
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Track Employee Location',
		single_column: true
	});

	// ---------------- Filters ----------------
	let from_date = page.add_field({
		fieldname: "from_date",
		label: __("From Date"),
		fieldtype: "Date",
		default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		reqd: 1
	});

	let to_date = page.add_field({
		fieldname: "to_date",
		label: __("To Date"),
		fieldtype: "Date",
		default: frappe.datetime.get_today(),
		reqd: 1
	});

	let emp_code = page.add_field({
		label: 'Employee Code',
		fieldtype: 'Link',
		fieldname: 'employee_code',
		options: "Employee"
	});

	let emp_name = page.add_field({
		label: 'Employee Name',
		fieldtype: 'Data',
		fieldname: 'employee_name',
		read_only: 1
	});

	// ---------------- Layout ----------------
	let flex_container = $('<div style="display:flex; gap:15px; margin-top:15px;"></div>').appendTo(page.body);

	let canvas_wrapper = $('<div style="flex:1; height:500px; min-width:400px;"></div>').appendTo(flex_container);
	let canvas = $('<canvas style="width:100%; height:100%;"></canvas>').appendTo(canvas_wrapper);
	let locationLegend = $('<div id="location-legend" style="margin-top:10px;display:flex;flex-wrap:wrap;gap:15px;"></div>').appendTo(canvas_wrapper);

	let map_container_wrapper = $('<div style="flex:.35;height:500px;"></div>').appendTo(flex_container);
	let map_container = $('<div style="height:500px;"></div>').appendTo(map_container_wrapper);

	let map = L.map(map_container[0]).setView([20, 77], 5);
	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; OpenStreetMap contributors'
	}).addTo(map);
	setTimeout(() => {
		map.invalidateSize();
		if (geojsonLayer) {
			const bounds = geojsonLayer.getBounds();
			if (bounds.isValid()) {
				map.fitBounds(bounds, { padding: [50,50], maxZoom: 15 });
			}
		}
	}, 200);
	

	// ---------------- Point Styles ----------------
	const POINT_STYLES = [
		'circle', 'rect', 'triangle', 'rectRounded', 'star', 'crossRot', 'dash', 'line', 'triangleRot', 'rectRot'
	];  
	const _placeStyleMap = {};
	function getPointStyleFromPlace(place) {
		if (!place) return null;
		if (place && place === 'Unknown') return 'cross'; // ❌ Unknown always gets X/cross
	
		if (!_placeStyleMap[place]) {
			const idx = Object.keys(_placeStyleMap).length % POINT_STYLES.length;
			_placeStyleMap[place] = POINT_STYLES[idx];
		}
		return _placeStyleMap[place];
	}	

	// ---------------- Chart Plugins ----------------
	const absenceLinePlugin = {
		id: 'absenceLine',
		afterDatasetsDraw(chart) {
			const ctx = chart.ctx;
			const xScale = chart.scales.x;
			const yScale = chart.scales['y-left'];
			const ds = chart.data.datasets.find(d => d.label === 'Working Hours');
			if (!ds) return;
	
			ctx.save();
			ctx.setLineDash([5, 5]);
			ctx.strokeStyle = 'rgba(255,0,0,0.6)';
	
			ds.data.forEach((v, i) => {
				if (v == null) {
					const px = xScale.getPixelForTick(i);
					// Only draw vertical dashed line for absence
					ctx.beginPath();
					ctx.moveTo(px, yScale.top);
					ctx.lineTo(px, yScale.bottom);
					ctx.stroke();
				}
			});
	
			ctx.restore();
		}
	};	
	const drawCrossPlugin = {
		id: 'drawCross',
		afterDatasetsDraw(chart) {
			const ctx = chart.ctx;
	
			chart.data.datasets.forEach((dataset, datasetIndex) => {
				if (!dataset.pointStyle) return;
	
				const meta = chart.getDatasetMeta(datasetIndex);
	
				meta.data.forEach((point, index) => {
					const style = Array.isArray(dataset.pointStyle)
						? dataset.pointStyle[index]
						: dataset.pointStyle;
	
					if (style !== 'cross') return; // only draw X for 'cross'
	
					const x = point.x;
					const y = point.y;
					const size = dataset.pointRadius || 8;
	
					ctx.save();
					ctx.beginPath();
					ctx.moveTo(x - size/2, y - size/2);
					ctx.lineTo(x + size/2, y + size/2);
					ctx.moveTo(x - size/2, y + size/2);
					ctx.lineTo(x + size/2, y - size/2);
					ctx.strokeStyle = 'black';
					ctx.lineWidth = 1.5;
					ctx.stroke();
					ctx.restore();
				});
			});
		}
	};	
	const referenceLinePlugin = {
		id: 'referenceLine',
		afterDraw(chart) {
			const yValue = 9.5; // the reference value in hours
			const yScale = chart.scales['y-left']; // Working Hours axis
			const ctx = chart.ctx;
	
			// Convert value to pixel
			const yPixel = yScale.getPixelForValue(yValue);
	
			ctx.save();
			ctx.beginPath();
			ctx.moveTo(chart.chartArea.left, yPixel);
			ctx.lineTo(chart.chartArea.right, yPixel);
			ctx.lineWidth = 2;
			ctx.strokeStyle = 'rgba(0,0,200,0.3)'; // blue line
			ctx.setLineDash([6, 4]); // optional: dashed line
			ctx.stroke();
			ctx.restore();
	
			// Optional: add a label
			//ctx.fillStyle = 'blue';
			//ctx.font = 'bold 12px Arial';
			//ctx.fillText(`${yValue} hrs`, chart.chartArea.right - 40, yPixel - 5);
		}
	};	

	// ---------------- Chart Init ----------------
	frappe.require("/assets/mapl_customization/js/chart.js", () => {
		window.attendanceChartInstance = new Chart(canvas[0], {
			type: 'bar',
			data: { labels: [], datasets: [] },
			options: {
				responsive: true,
				interaction: { mode: 'index', intersect: false },
				plugins: {
					title: {
						display: true,
						text: 'Attendance & Location Pattern',
						font: { size: 18 }
					},
					legend: { position: 'bottom' },
					tooltip: {
						callbacks: {
							label(ctx) {
								const row = window._attendanceByDate[
									moment(ctx.label, 'ddd DD-MM-YYYY').format('YYYY-MM-DD')
								];
								if (!ctx.raw) return `${ctx.dataset.label}: Absent`;

								if (ctx.dataset.label === 'In Time')
									return `In: ${row.in_time} (${row.in_place || 'Unknown'})`;

								if (ctx.dataset.label === 'Out Time')
									return `Out: ${row.out_time} (${row.out_place || 'Unknown'})`;

								if (ctx.dataset.label === 'Working Hours')
									return `Hours: ${ctx.raw.toFixed(2)}`;
							}
						}
					}
				},
				scales: {
					'y-left': {
						type: 'linear',
						position: 'left',
						min: 0,
						max: 12,
						title: { display: true, text: 'Working Hours' },
						ticks: { stepSize: 1, beginAtZero: true }
					},
					'y-right': {
						type: 'linear',
						position: 'right',
						min: 0,
						max: 24,
						grid: { drawOnChartArea: false },
						title: { display: true, text: 'Time (Hours)' },
						ticks: { stepSize: 1, beginAtZero: true }
					}
				}				
			},
			plugins: [absenceLinePlugin,drawCrossPlugin,referenceLinePlugin]
		});
	});

	// ---------------- Filters Change ----------------
	[from_date, to_date, emp_code].forEach(f => {
		f.df.onchange = () => {
			let emp = emp_code.get_value();
			if (!emp) return emp_name.set_value('');

			frappe.db.get_value("Employee", emp, "employee_name", r => emp_name.set_value(r.employee_name));

			frappe.call({
				method: "mapl_customization.customizations_for_mapl.employee_gps_attendance.get_employee_coordinates_with_location",
				args: {
					employee_code: emp,
					from_date: from_date.get_value(),
					to_date: to_date.get_value()
				},
				callback: r => {
					update_map(r.message || []);
					update_chart(r.message || [], from_date.get_value(), to_date.get_value());
				}
			});
		};
	});

	// ---------------- Map ----------------
	let geojsonLayer;
	function update_map(rows) {
		if (geojsonLayer) {
			map.removeLayer(geojsonLayer);
			geojsonLayer = null;
		}

		if (!rows.length) return;

		const features = [];

		rows.forEach(r => {
			const date = moment(r.attendance_date).format('DD-MMM-YYYY');

			if (r.in_lat_long) {
				const [lat, lng] = r.in_lat_long.split(',').map(Number);
				features.push({
					type: "Feature",
					geometry: { type: "Point", coordinates: [lng, lat] },
					properties: {
						type: "IN",
						date,
						time: r.in_time,
						place: r.in_place || 'Unknown'
					}
				});
			}

			if (r.out_lat_long) {
				const [lat, lng] = r.out_lat_long.split(',').map(Number);
				features.push({
					type: "Feature",
					geometry: { type: "Point", coordinates: [lng, lat] },
					properties: {
						type: "OUT",
						date,
						time: r.out_time,
						place: r.out_place || 'Unknown'
					}
				});
			}
		});

		if (!features.length) return;

		geojsonLayer = L.geoJSON(
			{ type: "FeatureCollection", features },
			{
				pointToLayer(f, latlng) {
					return L.circleMarker(latlng, {
						radius: 8,
						fillColor: f.properties.type === 'IN' ? '#2ecc71' : '#e74c3c',
						color: '#000',
						fillOpacity: 0.85
					});
				},
				onEachFeature(f, layer) {
					const p = f.properties;
					layer.bindPopup(`
						<div style="font-size:13px;">
							<strong>${p.type === 'IN' ? 'Check In' : 'Check Out'}</strong><br>
							<b>Date:</b> ${p.date}<br>
							<b>Time:</b> ${p.time || '-'}<br>
							<b>Location:</b> ${p.place}
						</div>
					`);
				}
			}
		).addTo(map);

		setTimeout(() => {
			const bounds = geojsonLayer.getBounds();
			if (bounds.isValid()) {
				map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
			}
		}, 200);
	}

	function update_chart(rows, from_date, to_date) {
		if (!window.attendanceChartInstance) return;
	
		// Clear old styles mapping
		for (let k in _placeStyleMap) delete _placeStyleMap[k];
	
		window._attendanceByDate = {};
		rows.forEach(r => window._attendanceByDate[moment(r.attendance_date).format('YYYY-MM-DD')] = r);
	
		let labels = [], hours = [], inTimes = [], outTimes = [], inPlaces = [], outPlaces = [];
		for (let d = moment(from_date); d.isSameOrBefore(to_date); d.add(1, 'day')) {
			let key = d.format('YYYY-MM-DD'), rec = window._attendanceByDate[key];
			labels.push(d.format('ddd DD-MM-YYYY'));
	
			if (!rec) {
				hours.push(null); inTimes.push(null); outTimes.push(null);
				inPlaces.push(null); outPlaces.push(null);
				continue;
			}
	
			let inM = moment(rec.in_time, 'HH:mm:ss');
			let outM = moment(rec.out_time, 'HH:mm:ss');
	
			hours.push(outM.diff(inM, 'minutes') / 60);
			inTimes.push(inM.hours() + inM.minutes() / 60);
			outTimes.push(outM.hours() + outM.minutes() / 60);
			inPlaces.push(normalizePlace(rec.in_place));
			outPlaces.push(normalizePlace(rec.out_place));
		}
	
		// Update chart
		window.attendanceChartInstance.data = {
			labels,
			datasets: [
				{ label: 'Working Hours', data: hours, type: 'bar', yAxisID: 'y-left' },
				{
					label: 'In Time',
					data: inTimes,
					type: 'line',
					yAxisID: 'y-right',
					showLine: false,
					pointRadius: 8,
					pointHoverRadius: 10,
					pointBorderWidth: 1.5,
					pointStyle: inPlaces.map(p => getPointStyleFromPlace(p)), // cross for unknown
					backgroundColor: inPlaces.map(p => p === 'Unknown' ? 'transparent' : '#2ecc71'),
					borderColor: 'transparent' // line hidden
				},
				{
					label: 'Out Time',
					data: outTimes,
					type: 'line',
					yAxisID: 'y-right',
					showLine: false,
					pointRadius: 8,
					pointHoverRadius: 10,
					pointBorderWidth: 1.5,
					pointStyle: outPlaces.map(p => getPointStyleFromPlace(p)),
					backgroundColor: outPlaces.map(p => p === 'Unknown' ? 'transparent' : '#e74c3c'),
					borderColor: 'transparent'
				}				
			]
		};
	
		// Override cross points with real X on canvas
		window.attendanceChartInstance.options.elements = {
			point: {
				pointStyle: function(ctx) {
					const style = ctx.rawPointStyle || ctx.dataset.pointStyle[ctx.dataIndex];
					if (style === 'cross') {
						const size = ctx.dataset.pointRadius || 8;
						const canvas = ctx.chart.ctx;
						const x = ctx.x;
						const y = ctx.y;
						canvas.beginPath();
						canvas.moveTo(x - size/2, y - size/2);
						canvas.lineTo(x + size/2, y + size/2);
						canvas.moveTo(x - size/2, y + size/2);
						canvas.lineTo(x + size/2, y - size/2);
						canvas.strokeStyle = 'black';
						canvas.lineWidth = 1.5;
						canvas.stroke();
						return null; // skip default drawing
					}
					return style; // other shapes
				}
			}
		};
	
		window.attendanceChartInstance.update();
		renderLocationLegend();
	}	

	// ---------------- Legend ----------------
	function renderLocationLegend() {
		locationLegend.empty();
	
		Object.entries(_placeStyleMap).forEach(([place, style]) => {
			if (!place || place === 'Unknown') return;
			locationLegend.append(`
				<div style="display:flex;align-items:center;gap:6px;">
					<strong>${getSymbol(style)}</strong> ${place}
				</div>
			`);
		});
	
		// Add Unknown if used
		const unknownUsed = Object.values(window._attendanceByDate).some(r =>
			!r || !normalizePlace(r.in_place) || !normalizePlace(r.out_place)
		);
		if (unknownUsed) {
			locationLegend.append(`
				<div style="display:flex;align-items:center;gap:6px;">
					<strong>${getSymbol('cross')}</strong> Unknown
				</div>
			`);
		}
	}
	
	
	// ---------------- Normalize place ----------------
	function normalizePlace(place) {
		if (!place) return 'Unknown';
		return place.replace(/\s*\(.*\)$/, '');
	}

	function getSymbol(style) {
		const map = {
			circle: '●',
			rect: '■',
			triangle: '▲',
			rectRounded: '▢',
			cross: '✖',  // <-- important: cross = ✖
			star: '★',
			crossRot: '✖', // optional
			dash: '▬',
			line: '—',
			triangleRot: '▼',
			rectRot: '◆'
		};
		return map[style] || '✖';
	}
	
};
