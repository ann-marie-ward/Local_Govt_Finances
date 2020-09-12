window.dash_props = Object.assign({}, window.dash_props, {  
    module: {  
        point_to_layer: function(feature, latlng, context) {  
            return L.circleMarker(latlng)  
        }  
    }
});

window.dash_props = Object.assign({}, window.dash_props, {
    module: {
        on_each_feature: function (feature, layer, context) {
            // Add popup.
            if (feature.properties.popup) {
                const el = layer.bindPopup(feature.properties.popup).openPopup()
                // Check if feature id is matching the id for which the popup should be open.
                if(context.props.hideout && feature.properties.id === context.props.hideout.open){
                    const {map} = context.props.leaflet;  // get the map object
                    map.addLayer(el);  // add layer (otherwise we can't open the popup)
                    el.openPopup();  // open the popup
                }
            }
            // Add tooltip.
            if (feature.properties.tooltip) {
                layer.bindTooltip(feature.properties.tooltip)
            }
        }
    }
});
