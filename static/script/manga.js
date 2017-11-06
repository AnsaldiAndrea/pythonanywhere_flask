$(function() {
    $("a#interested").click(function() {
        var manga_id = $(this).attr("name");
        var action = $(this).attr("data-action");
        var button = $(this);
        var parent = $(this).parent().parent();
        var icon = $(":first-child", this);
        $.ajax({
            type : "POST",
            url : $SCRIPT_ROOT + "/manga/" + manga_id + "/" + action,
            contentType: 'application/json;charset=UTF-8',
            success: function(response) {
                var response_dict = JSON.parse(response);
                if(response_dict.success){
                    if(action==="delete"){
                      parent.removeClass("info");
                      button.removeClass("btn-primary");
                      button.addClass("btn-default");
                      button.attr("data-action", "add");
                      icon.removeClass('glyphicon-star');
                      icon.addClass("glyphicon-star-empty");
                    } else {
                      parent.addClass("info");
                      button.removeClass("btn-default");
                      button.addClass("btn-primary");
                      button.attr("data-action","delete");
                      icon.removeClass('glyphicon-star-empty');
                      icon.addClass("glyphicon-star");
                    }
                } else {
                    console.log(response_dict.error)
                }
            },
            error: function(error){
                console.log(error);
            }
        })
    });
});

$(function() {
    $("#search").on("keyup", function() {
        var value = $(this).val();
        console.log(value);
        $("table tr").each(function(index) {
            if (index !== 0) {
                var id = $(this).find("td:first").text();
                if (id.toLowerCase().indexOf(value.toLowerCase()) !== 0) {
                    $(this).hide();
                }
                else {
                    $(this).show();
                }
            }
        });
    });
});