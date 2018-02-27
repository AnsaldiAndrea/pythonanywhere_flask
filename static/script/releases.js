$(function () {
    $("a#buy").click(function() {
       var id = $(this).attr("data-id");
       var volume = $(this).attr("data-volume");
       var week = $(this).attr("data-week");
       var row = $(this).closest("tr");
       $.ajax({
           type: "POST",
           url: $SCRIPT_ROOT + "user/collection/" + id + "/" + volume,
           contentType: "application/json;charset=UTF-8",
           success: function () {
               var body = row.parent();
               row.remove();
               if(body.find("tr").length<2) {
                    var table = body.parent();
                    var panel = table.parent();
                    table.remove();
                    panel.text("Empty");
               }
               calculate_price($("[data-price='price_"+week+"']"),$("#sum_"+week+""));
           },
           error: function (response) {
                alert(response);
           }
       })
    })
});

function calculate_price(source,destination) {
    var sum=0;
    source.each(function() {
        var value = parseFloat($(this).text());
        if(!isNaN(value)) {
            sum += value;
        }
    });
    destination.text(sum.toFixed(2) + " €");
}

function calculate_all() {
    calculate_price($("[data-price='price_prev']"),$("#sum_prev"));
    calculate_price($("[data-price='price_this']"),$("#sum_this"));
    calculate_price($("[data-price='price_next']"),$("#sum_next"));
    calculate_price($("[data-price='price_future']"),$("#sum_future"));
}
$(function() {
    calculate_all()
});