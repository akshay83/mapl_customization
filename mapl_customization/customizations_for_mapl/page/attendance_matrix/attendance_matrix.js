frappe.pages['attendance-matrix'].on_page_load = function (wrapper) {

    // ---------------- PAGE ----------------
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Attendance Matrix',
        single_column: true
    });

    const $pageWrap = $('<div class="attendance-matrix-page"></div>')
        .appendTo(page.body);

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
        fieldname: 'employee',
        options: 'Employee',
        filters: { status: "Active" },
        change() { load_data(); }
    });

    const WORKING_HOURS = 7.5;

    // ---------------- CONTAINER ----------------
    const $container = $('<div class="attendance-elements-container"></div>')
        .appendTo($pageWrap);

    // ---------------- SCOPED CSS ----------------
    $('<style>').text(`
        /* ==========================================================
            Attendance Matrix Page Styles
        =========================================================== */
        
        /* ---------- Container ---------- */
        .attendance-elements-container {
            margin-top: 15px;
            overflow: auto;           /* Enable scrolling if table overflows */
            max-height: 450px;        /* Limit height for vertical scroll */
            /* position: sticky; */    /* Not needed for container */
        }
        
        /* ---------- Table Base ---------- */
        .attendance-matrix-page table {
            border-collapse: separate;
            border-spacing: 0;
            table-layout: fixed;      /* Important for fixed widths and sticky columns */
            width: max-content;       /* Table grows horizontally as needed */
            font-size: 12px;
        }
        
        /* ---------- Table Header ---------- */
        .attendance-matrix-page thead th {
            background: #f4f6f8;
            position: sticky;         /* Keep header fixed when scrolling vertically */
            top: 50px;                /* Offset from top (adjust as per filters height) */
            z-index: 2;
            vertical-align: middle;
        }
        
        /* ---------- Table Cells ---------- */
        .attendance-matrix-page th,
        .attendance-matrix-page td {
            border: 1px solid #dee2e6;
            padding: 6px;
            text-align: center;
        }
        
        /* Zebra striping for readability */
        .attendance-matrix-page tbody tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        /* ---------- Attendance Icons ---------- */
        .att-icon {
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
        }
        .att-g { color: #1e7e34; }  /* Full */
        .att-p { color: #5a2ca0; }  /* GPS issue */
        .att-y { color: #d39e00; }  /* Partial */
        .att-b { color: #0d6efd; }  /* Single punch */
        .att-r { color: #c82333; }  /* Absent */
        
        /* ---------- Score Pills ---------- */
        .score-pill {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: #fff;
        }
        .score-good { background:#28a745; }
        .score-mid { background:#f0ad4e; color:#000; }
        .score-low { background:#dc3545; }
        
        /* ---------- Legend ---------- */
        .attendance-legend {
            height:50px;
            padding: 8px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            font-size: 12px;
            position: sticky;       /* Keeps legend visible at top */
            top: 0;
            z-index: 10;
            left: 0;
            width: 100%;
        }
        
        .attendance-legend-abbr {
            display: none;          /* Shown only for print */
        }
        
        /* ---------- Tooltip ---------- */
        .att-tooltip {
            position: absolute;
            background: #212529;
            color: #fff;
            padding: 6px;
            border-radius: 4px;
            font-size: 11px;
            display: none;
            z-index: 9999;
        }
        
        /* ==========================================================
            Sticky Left Columns
            ========================================================== */
        
        /* General sticky left column helper */
        .attendance-matrix-page th.sticky-col {
            position: sticky;
            left: 0;
            z-index: 3;
            background: #fff;
        }
        
        /* S.No Column */
        .attendance-matrix-page th.col-sno,
        .attendance-matrix-page td.col-sno {
            position: sticky;
            left: 0;
            width: 40px;
            min-width: 40px;
            background: #fff;
        }
        
        /* Employee Name Column */
        .attendance-matrix-page th.col-emp,
        .attendance-matrix-page td.col-emp {
            position: sticky;
            left: 40px;             /* After S.No */
            width: 160px;
            min-width: 160px;
            background: #fff;
        }
        
        /* Branch Column */
        .attendance-matrix-page th.col-branch,
        .attendance-matrix-page td.col-branch {
            position: sticky;
            left: 200px;            /* After S.No + Employee */
            width: 120px;
            min-width: 120px;
            background: #fff;
        }
        
        /* ==========================================================
            Print Styles
            ========================================================== */
        @media print {
        
            /* Container adjustments */
            .attendance-elements-container {
                overflow: visible !important;
                max-height: initial !important;
                position: initial !important;
            }
        
            /* Hide everything except attendance table */
            body * { visibility: hidden; }
            .attendance-matrix-page, .attendance-matrix-page * { visibility: visible; }
        
            /* Reset header and legend to static for printing */
            .attendance-legend,
            .attendance-matrix-page thead th {
                position: static !important;
            }
        
            /* Legend adjustments */
            .attendance-legend {
                display: flex !important;
                flex-wrap: nowrap !important;
                justify-content: flex-start;
                align-items: center;
                gap: 2px !important;
                margin-bottom: 2px !important;
                border: 1px solid #000 !important;
                padding: 15px !important;
                background: none !important;
                color: #000 !important;
                font-weight: bold;
                font-size: 12px !important;
                line-height: 1.25em !important;
                overflow: hidden;
                align-items: baseline;
            }
        
            /* Abbreviation legend */
            .attendance-legend-abbr {
                display: block !important;
                font-size: 12px !important;
                padding: 15px !important;
                margin-top: 2px !important;
                border: 1px solid #000 !important;
                background: none !important;
            }
        
            /* Force landscape */
            @page {
                size: landscape;
                margin: 5mm;
            }
        
            /* Table adjustments for printing */
            .attendance-matrix-page table {
                table-layout: auto !important;
                width: 100% !important;
                border-collapse: collapse !important;
                font-size: 9px !important;
            }
        
            /* Cells for print */
            .attendance-matrix-page th,
            .attendance-matrix-page td {
                border: 1px solid #000 !important;
                padding: 1px !important;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: none !important;
                color: #000 !important;
                font-weight: normal;
            }
        
            /* Attendance icons with abbreviations */
            .attendance-matrix-page .att-icon {
                font-size: 12px !important;
                display: block;
                line-height: 1em !important;
            }
            .attendance-matrix-page .att-icon::after {
                content: attr(data-print-abbr);
                font-size: 12px !important;
                padding-top: 15px;
                display: block;
                line-height: 1em;
                margin: 0;
                color: #000;
                text-align: center;
            }
        
            /* Sticky columns adjustments for print */
            .attendance-matrix-page th.col-sno,
            .attendance-matrix-page td.col-sno {
                left: initial !important;
                width: 30px !important;
                min-width: initial !important;
            }
            .attendance-matrix-page th.col-emp,
            .attendance-matrix-page td.col-emp {
                left: initial !important;
                width: 75px !important;
                min-width: initial !important;
                text-wrap: auto;
            }
            .attendance-matrix-page th.col-branch,
            .attendance-matrix-page td.col-branch {
                left: initial !important;
                width: 65px !important;
                min-width: initial !important;
                text-wrap: auto;
            }

            /* Hide everything */
            body * {
                visibility: hidden !important;
            }
        
            /* Show only your attendance page */
            .attendance-matrix-page, 
            .attendance-matrix-page * {
                visibility: visible !important;
            }
        
            /* Optional: adjust positioning to top of page */
            .attendance-matrix-page {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
            }           
        }                
    `).appendTo($pageWrap);

    // ---------------- AUTO LOAD ----------------
    [from_date, to_date].forEach(f => {
        f.df.onchange = () => load_data();
    });

    // ---------------- LOAD DATA ----------------
    function load_data() {
        if (!from_date.get_value() || !to_date.get_value()) return;

        frappe.call({
            method: 'mapl_customization.customizations_for_mapl.employee_gps_attendance.get_employee_coordinates_with_location',
            args: {
                from_date: from_date.get_value(),
                to_date: to_date.get_value(),
                employee_code: employee.get_value() || null
            },
            callback: r => render_table(r.message || [])
        });
    }

    // ---------------- RENDER TABLE ----------------
    function render_table(rows) {

        $container.empty();
        if (!rows.length) {
            $container.html('<p>No attendance data</p>');
            return;
        }

        // ---------- Legend ----------
        $container.append(`
            <div class="attendance-legend">
                <b>Attendance:</b>
                <span class="att-icon att-g">■</span> Full
                <span class="att-icon att-p">▲</span> GPS Issue
                <span class="att-icon att-y">◆</span> Partial
                <span class="att-icon att-b">●</span> Single Punch
                <span class="att-icon att-r">✖</span> Absent
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <b>Score:</b>
                <span class="score-pill score-good">80–100</span>
                <span class="score-pill score-mid">65–79</span>
                <span class="score-pill score-low">&lt;65</span>
            </div>
            <div class="attendance-legend attendance-legend-abbr">
                <b>Abbr:</b>
                F = Full,
                FG = Full (GPS),
                P = Partial,
                S = Single,
                A = Absent
            </div>
        `);

        // ---------- Group data ----------
        const employees = {};
        rows.forEach(r => {
            const k = r.employee || r.employee_code;
            employees[k] ??= { name: r.employee_name, branch: r.branch, days: {} };
            employees[k].days[moment(r.attendance_date).format('YYYY-MM-DD')] = r;
        });

        // ---------- Dates ----------
        const dates = [];
        for (let d = moment(from_date.get_value()); d.isSameOrBefore(to_date.get_value()); d.add(1, 'day')) {
            dates.push(d.format('YYYY-MM-DD'));
        }

        // ---------- Table ----------
        const $table = $('<table></table>');
        const $thead = $(`
                        <thead>
                        <tr>
                            <th class="sticky-col col-sno">S.No</th>
                            <th class="sticky-col col-emp">Employee</th>
                            <th class="sticky-col col-branch">Branch</th>
                            <th>Score</th>
                        </tr>
                        </thead>
        `);

        dates.forEach(d => {
            const m = moment(d);
            $thead.find('tr').append(`
                <th>
                    <div style="font-size:11px">${m.format('DD')}</div>
                    <div style="font-size:9px;color:#6c757d">${m.format('ddd')}</div>
                </th>
            `);
        });
        $thead.find('tr').append('<th>Attendance</br>(F/H/A)</th>');
        $table.append($thead);

        const $tbody = $('<tbody></tbody>');
        const $tooltip = $('<div class="att-tooltip"></div>').appendTo('body');

        Object.values(employees)
            .sort((a, b) =>
                a.branch.localeCompare(b.branch) ||
                a.name.localeCompare(b.name)
            )
            .forEach((emp, i) => {
                const stats = {
                    total: dates.length,
                    absent: 0,
                    present: 0,
                    fullHours: 0,
                    partial: 0,
                    single: 0,
                    gpsCorrect: 0,
                    bothPunches: 0
                };

                const $tr = $('<tr></tr>');
                $tr.append(`<td class="sticky-col col-sno">${i + 1}</td>`);
                $tr.append(`<td class="sticky-col col-emp">${emp.name}</td>`);
                $tr.append(`<td class="sticky-col col-branch">${emp.branch}</td>`);

                dates.forEach(date => {
                    const r = emp.days[date];
                    let sym = '✖', cls = 'att-r', hrs = 0;

                    if (!r) {
                        stats.absent++;
                    } else {
                        const hasIn = !!r.in_time;
                        const hasOut = !!r.out_time;
                        const inLocOk = r.in_place && r.in_place !== 'Unknown';
                        const outLocOk = r.out_place && r.out_place !== 'Unknown';

                        if (hasIn && hasOut) {
                            const i = moment(r.in_time, 'HH:mm:ss');
                            const o = moment(r.out_time, 'HH:mm:ss');
                            const diffMin = o.diff(i, 'minutes');

                            if (o.isAfter(i) && diffMin > 60) {
                                hrs = diffMin / 60;
                                stats.present++;
                                stats.bothPunches++;

                                const badLoc = !inLocOk || !outLocOk;

                                if (hrs >= WORKING_HOURS) {
                                    sym = badLoc ? '▲' : '■';
                                    cls = badLoc ? 'att-p' : 'att-g';
                                    stats.fullHours++;
                                    if (!badLoc) stats.gpsCorrect++;
                                } else {
                                    sym = '◆';
                                    cls = 'att-y';
                                    stats.partial++;
                                }
                            } else {
                                sym = '●';
                                cls = 'att-b';
                                stats.single++;
                                stats.present++;
                            }
                        } else {
                            sym = '●';
                            cls = 'att-b';
                            stats.single++;
                            stats.present++;
                        }
                    }

                    if (r) {
                        r._sym = sym;  // store the symbol for summary calculation
                    }

                    //const $icon = $(`<span class="att-icon ${cls}">${sym}</span>`);
                    const abbr = sym === '■' ? 'F' : sym === '▲' ? 'FG' : sym === '◆' ? 'P' : sym === '●' ? 'S' : 'A';
                    const $icon = $(`
                        <span class="att-icon ${cls}"
                            data-print-abbr="${abbr}">
                            ${sym}
                        </span>
                    `);

                    $icon.on('mouseenter', function () {
                        const o = $(this).offset();

                        $tooltip.html(`
                        <b>${moment(date).format('DD MMM')}</b><br>
                        In: ${r?.in_time || '-'}<br>
                        Out: ${r?.out_time || '-'}<br>
                        Hours: ${hrs.toFixed(2)}<br>
                        In Place: ${r?.in_place || 'Unknown'}<br>
                        Out Place: ${r?.out_place || 'Unknown'}
                    `).css({ display: 'block' });


                        const ttW = $tooltip.outerWidth();
                        const ttH = $tooltip.outerHeight();
                        const winW = $(window).width();

                        let top = o.top - ttH - 6;
                        let left = o.left - ttW / 2 + $(this).outerWidth() / 2;

                        if (top < 0) top = o.top + $(this).outerHeight() + 6;
                        if (left < 6) left = 6;
                        if (left + ttW > winW) left = winW - ttW - 6;

                        $tooltip.css({ top, left });
                    }).on('mouseleave', () => $tooltip.hide());

                    $tr.append($('<td></td>').append($icon));
                });

                // ---------- SCORE CALCULATION ----------
                const workingDays = stats.total - stats.absent;

                const absenceScore = Math.max(0, 40 - Math.max(0, stats.absent - 5) * 8);
                const gpsRatio = stats.present ? stats.gpsCorrect / stats.present : 0;
                const gpsScore = gpsRatio >= 0.95 ? 15 : gpsRatio >= 0.85 ? 12 : gpsRatio >= 0.7 ? 8 : 4;
                const punchRatio = workingDays ? stats.bothPunches / workingDays : 0;
                const punchScore = punchRatio >= 0.95 ? 20 : punchRatio >= 0.85 ? 16 : punchRatio >= 0.7 ? 10 : 5;
                const locScore = gpsRatio >= 0.9 ? 10 : gpsRatio >= 0.75 ? 7 : gpsRatio >= 0.6 ? 4 : 2;
                const hourRatio = workingDays ? stats.fullHours / workingDays : 0;
                const hourScore = hourRatio >= 0.9 ? 15 : hourRatio >= 0.75 ? 12 : hourRatio >= 0.6 ? 8 : 4;

                const score = Math.round(absenceScore + gpsScore + punchScore + locScore + hourScore);
                const scls = score >= 80 ? 'score-good' : score >= 65 ? 'score-mid' : 'score-low';

                //Insert After 3rd Column, starting from 0
                $tr.find('td').eq(2).after(`<td><span class="score-pill ${scls}">${score}</span></td>`);
                $tbody.append($tr);

                // ---------- ATTENDANCE SUMMARY COLUMN ----------
                let fullDays = 0, halfDays = 0, absentDays = 0;

                dates.forEach(date => {
                    const r = emp.days[date];
                    const sym = r ? r._sym : '✖'; // ✅ use stored symbol

                    if (sym === '■' || sym === '▲') fullDays++;
                    else if (sym === '◆' || sym === '●') halfDays++;
                    else absentDays++;
                });

                // Append summary column at the end
                $tr.append(`<td style="font-size:10px; white-space: nowrap;">${fullDays}/${halfDays}/${absentDays}</td>`);

            });

        $table.append($tbody);
        $container.append($table);
    }

    load_data();
};
