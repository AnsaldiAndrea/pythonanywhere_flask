function buyVolume(id, volume, week) {
   var row = $(this).parent().closest("tr");
   $.ajax({
       type: "POST",
       url: $SCRIPT_ROOT + "user/collection/" + id + "/" + volume,
       contentType: "application/json;charset=UTF-8",
       success: function (data2) {
           var body = row.parent();
           row.remove();
           if(body.children().length<2) {
                var table = body.parent();
                var panel = table.parent();
                table.remove();
                panel.text("Empty")
           }
           calculate_price("#price_"+week, "#sum_"+week);
       },
       error: function () {
            alert("A problem occurred while processing the request.")
       }
   })
}

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
    calculate_price($("#price_prev"),$("#sum_prev"));
    calculate_price($("#price_this"),$("#sum_this"));
    calculate_price($("#price_next"),$("#sum_next"));
    calculate_price($("#price_future"),$("#sum_future"));
}
$(function() {
    calculate_all()
});