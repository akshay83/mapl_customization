frappe.provide('frappe.pages');
frappe.provide('frappe');

var sidebar_customized = false;



$(document).ready(function() {
    var navbar = $('div').find('.navbar-header');

    var collapse_button = '<button id="side-bar-menu" type="button" class="btn btn-default collapsible-button" onclick="doSideBar()"> \
                             <i class="octicon octicon-three-bars"></i> \
                         </button>';

    navbar.prepend(collapse_button);
    $('div').on('DOMNodeInserted', '.col-md-2.layout-side-section', function (e) {
            //console.log('Added:'+e.target.className);
            $('.col-md-2.layout-side-section','div').hide();
    });
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

    // Check if click was triggered on or within #menu_content
    // console.log(e.target.id);
    if (e.target.id == 'side-bar-menu') {
        return;
    }
    if( $(e.target).closest('.col-md-2.layout-side-section').length > 0 ) {
        return;
    }
    $('div').find('.col-md-2.layout-side-section').hide();
    // Otherwise
    // trigger your click function
});

