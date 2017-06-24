frappe.provide('frappe.pages');
frappe.provide('frappe');

$(document).ready(function() {
  if (screen.width >= 961) {
    var navbar = $('div').find('.navbar-header');

    var collapse_button = '<button id="side-bar-menu" type="button" class="btn btn-default collapsible-button" onclick="doSideBar()"> \
                             <i class="octicon octicon-three-bars"></i> \
                         </button>';

    navbar.prepend(collapse_button);
    $('#side-bar-menu').hide();
  }
});

$(document).on("page-change", function() {
  if (screen.width >= 961) {
    if (frappe.get_route_str() == '') {
             $('#side-bar-menu').hide();
    } else {
             $('#side-bar-menu').show();
    }
  }
});


doSideBar = function() {
    var sidebar = $('div').find('.col-md-2.layout-side-section');
    if (sidebar.is(":visible")) { 
        sb_width = sidebar.css('width');
        sidebar.hide();
    }
    else {
        sidebar.show();
    }
}

$(document).click(function(e){
  if (screen.width >= 961) {
    if (e.target.id == 'side-bar-menu') {
        return;
    }
    if( $(e.target).closest('.col-md-2.layout-side-section').length > 0 ) {
        return;
    }
    $('div').find('.col-md-2.layout-side-section').hide();
  }
});

