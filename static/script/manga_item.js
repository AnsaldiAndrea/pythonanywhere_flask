$(function () {
    $("a.buy").click(function() {
        var is_in_library = ($(this).attr("data-buy")==="true");
        var id = $(this).attr("id");
        var button = $(this);
        var parent = $(this).parent().parent();
        $.ajax({
            type : is_in_library?"DELETE":"POST",
            url : $SCRIPT_ROOT + "/user/collection/" + id,
            contentType: 'application/json;charset=UTF-8',
            success: function(response){
                console.log(response);
                if(!is_in_library){
                    button.attr("data-buy","true");
                    parent.addClass("info")
                } else {
                    button.attr("data-buy","false");
                    parent.removeClass("info")
                }
            },
            error: function(error){
                console.log(error);
            }
        });
    })
});