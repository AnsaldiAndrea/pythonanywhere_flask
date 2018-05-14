$(function() {
    $("a.bookmark").click(function() {
        var tr = $(this).parent().closest("tr");
        var button = tr.find("a");
        var icon = tr.find("span");
        var manga_id = tr.attr("id");
        console.log(manga_id);
        var bookmarked = ($(this).attr("data-bookmark") === "true");
        var tp = "POST";
        if(bookmarked) tp = "DELETE";
        $.ajax({
            type : tp,
            url : $SCRIPT_ROOT + "/user/manga/" + manga_id,
            contentType: 'application/json;charset=UTF-8',
            success: function() {
                if(bookmarked){
                    tr.removeClass("active");
                    button.attr("data-bookmark", "false");
                    icon.removeClass('glyphicon-star');
                    icon.addClass("glyphicon-star-empty");
                } else {
                    tr.addClass("active");
                    button.attr("data-bookmark", "true");
                    icon.removeClass('glyphicon-star-empty');
                    icon.addClass("glyphicon-star");
                }
            },
            error: function(error){
                alert(error)
            }
        })
    })
});

$(function() {
    $("#search").on("keyup", function() {
        var value = $(this).val();
        console.log(value);
        $("table tr").each(function(index) {
            if (index !== 0) {
                var title = $(this).find(".title").text();
                if (title.toLowerCase().indexOf(value.toLowerCase()) !== 0) {
                    $(this).hide();
                }
                else {
                    $(this).show();
                }
            }
        });
    });
});