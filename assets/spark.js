Tabulator.prototype.extendModule("format", "formatters", {
    spark:function(cell, formatterParams){
       var value = cell.getValue();
        if(value.indexOf("o") > 0){
            return "<span style='color:red; font-weight:bold;'>" + value + "</span>";
        }else{
            return "<span style='color:red; font-weight:bold;'>" + value + "</span>";
        }
})




