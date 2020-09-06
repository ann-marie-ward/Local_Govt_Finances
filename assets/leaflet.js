window.dash_props = Object.assign({}, window.dash_props, {  
    module: {  
        point_to_layer: function(feature, latlng, context) {  
            return L.circleMarker(latlng)  
        }  
    }  
});