frappe.listview_settings["Customer"] = {
    onload: function (listview) {
        listview.custom_last_filter = null;
        //--DEBUG--console.log("Customer Listview");
        let refresh_button = {
            fieldname: "phone_search_button",
            fieldtype: "Button",
            click: function () {
                listview.refresh();
            },
            icon: "refresh",
            label: ""
        }
        let df = {
            fieldname: "phone_search",
            fieldtype: "Data",
            onchange: function () {
                if (this.value === undefined || this.value == null || this.value == '') {
                    custom_clear_filter_and_refresh(listview);
                    return;
                }
                frappe.call({
                    method: "mapl_customization.customizations_for_mapl.queries.mapl_customer_by_phone_query",
                    args: {
                        doctype: null,
                        searchfield: null,
                        filters: null,
                        txt: this.value,
                        start: 0,
                        page_len: 100
                    },
                    callback: function (r) {
                        if (r && r.message) {
                            let customers_list = custom_build_list(r.message);
                            if (customers_list.length <= 0) {
                                custom_clear_filter_and_refresh(listview);
                                return;
                            }
                            let filter = ['Customer', 'name', 'in', customers_list.join()];
                            if (listview.custom_last_filter == null || filter.toString() !== listview.custom_last_filter.toString()) {
                                listview.filter_area.filter_list.clear_filters();
                                listview.filter_area.filter_list.add_filter(filter[0], filter[1], filter[2], filter[3]);
                                listview.start = 0;
                                listview.custom_last_filter = filter;
                            }
                        } else {
                            custom_clear_filter_and_refresh(listview);
                        }
                        listview.refresh();
                        listview.on_filter_change();
                    }
                });
            }
        }
        if (listview.doctype == "Customer") {
            let control = frappe.ui.form.make_control({ df: df, parent: listview.list_sidebar.sidebar });
            control.refresh();
            $(control.wrapper)
                .attr("title", "Search By No").tooltip({
                    delay: { "show": 600, "hide": 100 },
                    trigger: "hover"
                });
            control.$input.attr("placeholder", "Search By No");
            //control.label_area.setAttribute("hidden",1);
            control.toggle_label(false);
            let refresh_control = frappe.ui.form.make_control({ df: refresh_button, parent: listview.list_sidebar.sidebar });
            refresh_control.refresh();
            refresh_control.toggle_label(false);
        }
    }
}

function custom_clear_filter_and_refresh(listview) {
    listview.filter_area.filter_list.clear_filters();
    listview.custom_last_filter = null;
    listview.refresh();
    listview.on_filter_change();
}

function custom_remove_from_filter(from_filters, val) {
    let idx = from_filters.indexOf(val);
    if (idx !== -1) {
        from_filters.splice(idx, 1);
    }
}

function custom_build_list(customer_list) {
    let build_list = [];
    for (let i = 0; i < customer_list.length; i++) {
        build_list.push(customer_list[i][0]);
    }
    return build_list;
}