var customized_footer = 0;

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
        console.log("Called Page");
        try {
            if ($('.form-footer').parent()[0].className=='row layout-main') {
                $('.pull-right.scroll-to-top').remove();
                $('.form-footer').remove();
            }
        } catch (err) {
            console.log(err);
        }
        //$('#comments-button').hide();
});


$('div').on('DOMNodeInserted', '.form-footer', function (e) {
    if (e.target.className == 'form-footer' && customized_footer!=1) {
        if ($('.form-footer').parent().length == 1 && $('.form-footer').parent()[0].className != 'row layout-main') {
            console.log("Called Inserted");
            customized_footer = 1;
            $('div').find('.form-footer').detach().appendTo($('.row.layout-main'))
            $('div').find('.pull-right.scroll-to-top').detach().appendTo($('.row.layout-main'))
            $('div').find('.form-footer').hide();
        } 
        $('#comments-button').show();
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
