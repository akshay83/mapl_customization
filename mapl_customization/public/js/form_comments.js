
$(document).ready(function() {
  if (screen.width >= 961) {
        //console.log("Called Ready");
        var collapse_button = '<button id="comments-button" type="button" class="btn btn-default collapsible-button" onclick="doComments()"> \
                                 <i class="octicon octicon-comment"></i> \
                             </button>';
        $('.nav.navbar-nav.navbar-right').append(collapse_button);
        $('#comments-button').hide();
  }
});

$(document).on("page-change", function() {
  if (screen.width >= 961) {
        if (frappe.get_route()[0] != 'Form')  {
            $('#comments-button').hide();
        } else {
            $('#comments-button').show();
        }
  }
});


doComments = function() {
    var comments = $('div').find('.after-save');
    if (comments.is(":visible")) { 
        comments.hide();
    }
    else {
        comments.show();
    }
}

$(document).click(function(e){
  if (screen.width >= 961) {
    // Check if click was triggered on or within #menu_content
    // console.log(e.target.id);
    if (e.target.id == 'comments-button') {
        return;
    }
    if( $(e.target).closest('.after-save').length > 0 ) {
        return;
    }
    $('div').find('.after-save').hide();
  }
});
