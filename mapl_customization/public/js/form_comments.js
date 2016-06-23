var customized_footer = 0;

$(document).ready(function() {
        customized_footer = 0;
        console.log("Called Ready");
});

$('div').on('DOMNodeInserted', '.form-footer', function (e) {
    if (e.target.className == 'form-footer' && customized_footer!=1) {
        console.log('Hello Comments:'+e.target.className);
        var collapse_button = '<button id="comments-button" type="button" class="btn btn-default collapsible-button" onclick="doComments()"> \
                                 <i class="octicon octicon-comment"></i> \
                             </button>';
        customized_footer = 1;
        $('.hidden-xs.hidden-sm').find('.nav.navbar-nav.navbar-right').append(collapse_button);
        $('div').find('.form-footer').insertBefore($('div').find('.col-md-10.layout-main-section-wrapper'))
        $('div').find('.pull-right.scroll-to-top').insertAfter($('div').find('.col-md-10.layout-main-section-wrapper'))
        $('div').find('.form-footer').hide();
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

