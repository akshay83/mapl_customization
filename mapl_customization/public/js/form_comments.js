var customized_footer = 0;
var visited_documents = [];

$(document).ready(function() {
        console.log("Called Ready");
        //$('div').find('.pull-right.scroll-to-top').remove();
        var collapse_button = '<button id="comments-button" type="button" class="btn btn-default collapsible-button" onclick="doComments()"> \
                                 <i class="octicon octicon-comment"></i> \
                             </button>';
        $('.hidden-xs.hidden-sm').find('.nav.navbar-nav.navbar-right').append(collapse_button);
        $('#comments-button').hide();
});

$(document).on("page-change", function() {
        customized_footer = 0;
        console.log("Called Page, Route:"+frappe.get_route_str());
        current_form = frappe.get_route()[1];
        if (frappe.get_route()[0] == 'Form' && $.inArray(current_form, visited_documents) == -1) {
            try {
                if ($('.form-footer').parent()[0].className=='row layout-main') {
                    console.log("Removed Button:"+$('.pull-right.scroll-to-top').remove().length);
                    $('.form-footer').remove();
                }
            } catch (err) {
                console.log(err);
            } finally {
                visited_documents.push(current_form);
            }
        }
        if (frappe.get_route()[0] != 'Form')  {
            $('#comments-button').hide();
        } else {
            $('#comments-button').show();
        }
        console.log('Button Length:'+$('.pull-right.scroll-to-top').length);
});


$('div').on('DOMNodeInserted', '.form-footer', function (e) {
    if (e.target.className == 'form-footer' && customized_footer!=1) {
            console.log("Trying to Insert");
        if ($('.form-footer').parent().length == 1 && $('.form-footer').parent()[0].className != 'row layout-main') {
            customized_footer = 1;
            $('.form-footer').appendTo($('.row.layout-main'))
            console.log('Current Buttons:'+$('.pull-right.scroll-to-top').length);
            $('.pull-right.scroll-to-top').appendTo($('.row.layout-main'))
            $('div').find('.form-footer').hide();
        }
    }
});

doComments = function() {
    var comments = $('div').find('.form-footer');
    if (comments.is(":visible")) { 
        comments.hide();
    }
    else {
        comments.show();
    }
}

$(document).click(function(e){

    // Check if click was triggered on or within #menu_content
    // console.log(e.target.id);
    if (e.target.id == 'comments-button') {
        return;
    }
    if( $(e.target).closest('.form-footer').length > 0 ) {
        return;
    }
    $('div').find('.form-footer').hide();

});
