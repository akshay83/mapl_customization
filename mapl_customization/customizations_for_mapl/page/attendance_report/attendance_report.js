frappe.pages['attendance-report'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Attendance Report Viewer',
        single_column: true
    });

    const $wrap = $('<div class="report-viewer"></div>').appendTo(page.body);

    // ---------------- FILTERS ----------------
    const from_date = page.add_field({
        fieldtype: 'Date',
        label: 'From',
        default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        reqd: 1
    });

    const to_date = page.add_field({
        fieldtype: 'Date',
        label: 'To',
        default: frappe.datetime.get_today(),
        reqd: 1
    });

    const employee = page.add_field({
        fieldtype: 'Link',
        label: 'Employee',
        options: 'Employee',
        change() { load_data(); }
    });

    const branch = page.add_field({
        fieldtype: 'Link',
        label: 'Branch',
        options: 'Branch',
        change() { load_data(); }
    });

    page.set_primary_action('Refresh', load_data);

    const $tableContainer = $('<div class="table-area"></div>').appendTo($wrap);
    const $legend = $('<div class="legend-panel"></div>').appendTo($wrap);

    const WORKING_HOURS = 7.5;

    // ---------------- LOAD DATA ----------------
    function load_data() {
        if (!from_date.get_value() || !to_date.get_value()) return;

        frappe.call({
            method: 'frappe.desk.query_report.run',
            args: {
                report_name: 'Monthly Compact Mobile Attendance',
                filters: {
                    from_date: from_date.get_value(),
                    to_date: to_date.get_value(),
                    employee: employee.get_value(),
                    branch: branch.get_value()
                }
            },
            callback: function (r) {
                render_table(r.message);
                render_legend();
            }
        });
    }

    // ---------------- HELPERS ----------------
    function shortenPlace(place) {
        if (!place) return 'UN';
        if (place.includes('Dewas')) return 'DN';
        if (place.includes('Geeta')) return 'GB';
        if (place.includes('Aranya')) return 'AN';
        if (place.includes('Vijay')) return 'VN';
        if (place.includes('Kanadia')) return 'KR';
        if (place === 'Unknown') return 'UN';
        return place.substring(0, 2).toUpperCase();
    }

    function getHours(inTime, outTime) {
        if (!inTime || !outTime) return 0;
        const i = moment(inTime, 'HH:mm:ss');
        const o = moment(outTime, 'HH:mm:ss');
        if (!o.isAfter(i)) return 0;
        return o.diff(i, 'minutes') / 60;
    }

    // ---------------- RENDER TABLE ----------------
    function render_table(report) {
        $tableContainer.empty();
        if (!report || !report.result || !report.result.length) {
            $tableContainer.html('<p>No data found</p>');
            return;
        }

        let columns = report.columns;
        const data = report.result;

        // -------- SHORT LABELS & merge summary columns --------
        let summaryAdded = false;
        columns.forEach(col => {
            if (["present_days","half_days","absent_days","total_hours"].includes(col.fieldname)) {
                if (!summaryAdded) {
                    col.label = "Summary";
                    col.fieldname = "monthly_summary";
                    summaryAdded = true;
                } else {
                    col.label = "";
                    col.fieldname = ""; 
                }
            } else {
                col.label = col.label
                    .replace('Employee Base Branch', 'Branch')
                    .replace('Employee Name', 'Name')
					.replace('Employee', 'Emp');
            }
        });

        const $table = $('<table></table>');

        // -------- HEADER --------
        const $thead = $('<thead><tr></tr></thead>');
        columns.forEach(col => {
            if (col.label) $thead.find('tr').append(`<th>${col.label}</th>`);
        });
        $table.append($thead);

        // -------- BODY --------
        const $tbody = $('<tbody></tbody>');
        let currentBranch = '';

        data.forEach(row => {

            // -------- BRANCH HEADER ROW --------
            if (row.employee_branch !== currentBranch) {
                currentBranch = row.employee_branch;
                $tbody.append(`<tr class="branch-row"><td colspan="${columns.length-3}" class="branch-header">${currentBranch}</td></tr>`);
            }

            const $tr = $('<tr></tr>');

            columns.forEach(col => {
                if (!col.fieldname) return; // skip hidden columns

                let val = row[col.fieldname] || '';
                let cellClass = '';

                // -------- Merged Summary --------
                if (col.fieldname === "monthly_summary") {
                    val = `P:${row.present_days || 0} | H:${row.half_days || 0} | A:${row.absent_days || 0} | TH:${Math.round(row.total_hours || 0)}`;
                }

                // -------- Daily Attendance Formatting --------
                else if (typeof val === 'string' && val.includes('In:') && val.includes('Out:')) {

                    const inMatch = val.match(/In:\s*(\S+)\s*\((.*?)\)/);
                    const outMatch = val.match(/Out:\s*(\S+)\s*\((.*?)\)/);

                    if (inMatch && outMatch) {
                        const inTime = inMatch[1].split(':').slice(0,2).join(':');
                        const outTime = outMatch[1].split(':').slice(0,2).join(':');
                        const inPlaceRaw = inMatch[2];
                        const outPlaceRaw = outMatch[2];
                        const inPlace = shortenPlace(inPlaceRaw);
                        const outPlace = shortenPlace(outPlaceRaw);
                        const hrs = getHours(inMatch[1], outMatch[1]);
                        const badLoc = inPlaceRaw === 'Unknown' || outPlaceRaw === 'Unknown';

                        if (hrs === 0) cellClass = 'att-single';
                        else if (hrs >= WORKING_HOURS) cellClass = badLoc ? 'att-gps' : 'att-full';
                        else cellClass = 'att-partial';

                        val = `<div><b>${inTime}-${outTime}</b><br>${inPlace}→${outPlace}<br><small>${hrs.toFixed(1)}h</small></div>`;
                    }
                }

                // -------- Absent Compact --------
                if (val === 'Absent') val = 'A';

                // Empty cell
                if (!val || val === '-') val = '';

                $tr.append(`<td class="${cellClass}">${val}</td>`);
            });

            $tbody.append($tr);
        });

        $table.append($tbody);
        $tableContainer.append($table);
    }

    // ---------------- LEGEND ----------------
    function render_legend() {
        $legend.empty();
        const legendHtml = `
            <strong>Legend:</strong>
            <span class="att-full"> Full Day ≥ ${WORKING_HOURS}h </span>
            <span class="att-partial"> Partial Day < ${WORKING_HOURS}h </span>
            <span class="att-gps"> GPS Issue </span>
            <span class="att-single"> Single Punch / 0h </span>
            <span> A = Absent </span>
        `;
        $legend.html(legendHtml);
    }

    // ---------------- STYLES ----------------
    $('<style>').text(`
        .report-viewer .table-area { margin-top: 10px; max-height: 500px; overflow: auto; }
        .report-viewer table { font-size: 11px; border-collapse: collapse; width: 100%; }
        .report-viewer th, .report-viewer td { border: 1px solid #ccc; padding: 3px; text-align: center; word-wrap: break-word; }
        .report-viewer th { position: static !important; top: 0; background: #f4f6f8; font-size: 10px; }
        .report-viewer td { min-width: 50px; max-width: 100px; }
        .branch-header { background:#f1f1f1; font-weight:bold; text-align:left; padding-left:5px; }
        /* -------- COLORS -------- */
        .att-full { background:#d4edda; }
        .att-partial { background:#ffe8a1; }
        .att-gps { background:#fff3cd; }
        .att-single { background:#cce5ff; }
        /* -------- LEGEND -------- */
        .legend-panel { margin-top: 10px; font-size: 12px; }
        .legend-panel span { display: inline-block; padding: 2px 6px; margin-right: 5px; border-radius: 3px; }
        /* -------- PRINT -------- */
        @media print {
            body * { visibility: hidden !important; }
            .report-viewer, .report-viewer * { visibility: visible !important; }
            .report-viewer { position: absolute; top: 0; left: 0; width: 100%; }
            .report-viewer .table-area { max-height: none !important; overflow: visible !important; }
            .report-viewer table { width: 100% !important; table-layout: fixed; font-size: 8px !important; }
            .report-viewer th, .report-viewer td { border:1px solid #000 !important; padding:2px !important; font-size: 8px !important; }
            thead { display: table-header-group; }
            tr { page-break-inside: avoid; }
            @page { size:A4 landscape; margin:5mm; }
        }
    `).appendTo($wrap);

    load_data();
};