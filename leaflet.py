##
##
## @app.callback(
##     [
##         Output('leaflet_map', 'zoom'),
##         Output('leaflet_map', 'center'),
##     ],
##     [
##         Input('city_table', 'selected_row_ids')
##     ],
##     [
##         State("city_table", "derived_virtual_data"),
##     ]
## )
## def zoom_map_on_table_click(selected_rows, data):
##     dff = pd.DataFrame(data)
##     if dff.empty or not selected_rows:
##         raise PreventUpdate
##     if selected_rows:
##         return 1, (47.6, 122.3)
##     else:
##         return dash.no_update
##


## import dash
## import dash_leaflet as dl
##
## app = dash.Dash()
## app.layout = dl.Map(dl.TileLayer(), style={'width': '1000px', 'height': '500px'})
##
## if __name__ == '__main__':
##    app.run_server()


#################  Map click events

##import dash
##import dash_html_components as html
##import dash_leaflet as dl

##from dash.dependencies import Input, Output

##app = dash.Dash(prevent_initial_callbacks=True)
##app.layout = html.Div([
##    dl.Map([dl.TileLayer(), dl.LayerGroup(id="layer")],
##           id="map", style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}),
##])


##@app.callback(Output("layer", "children"), [Input("map", "click_lat_lng")])
##def map_click(click_lat_lng):
##    return [dl.Marker(position=click_lat_lng, children=dl.Tooltip("({:.3f}, {:.3f})".format(*click_lat_lng)))]


##if __name__ == '__main__':
##    app.run_server()
########################################


## ############  App Drawing polygons
##
## import dash
## import dash_core_components as dcc
## import dash_html_components as html
## import dash_leaflet as dl
##
## from dash.dependencies import Input, Output, State, ALL
##
## app = dash.Dash(prevent_initial_callbacks=True)
## app.layout = html.Div([
##    dl.Map([dl.TileLayer(), dl.LayerGroup(id="drawing"), dl.LayerGroup([], id="polygons")],
##           id="map", style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}),
##    dcc.Store(id="store", data=[])
## ])
##
##
## @app.callback([Output("store", "data"), Output("drawing", "children"), Output("polygons", "children")],
##              [Input("map", "click_lat_lng"), Input({'role': 'marker', 'index': ALL}, "n_clicks")],
##              [State("store", "data"), State("polygons", "children")])
## def map_click(click_lat_lng, n_clicks, data, polygons):
##    trigger = dash.callback_context.triggered[0]["prop_id"]
##    # The map was clicked, add a new point.
##    if trigger.split(".")[1] == "click_lat_lng":
##        data.append(click_lat_lng)
##        markers = [dl.CircleMarker(center=pos, id={'role': 'marker', 'index': i}) for i, pos in enumerate(data)]
##        polyline = dl.Polyline(positions=data)
##        drawing = markers + [polyline]
##    # A marker was clicked, close the polygon and reset drawing.
##    else:
##        polygons.append(dl.Polygon(positions=data))
##        data, drawing = [], []
##    return data, drawing, polygons
##
##
## if __name__ == '__main__':
##    app.run_server()

####################  GeoJson

##import dash
##import dash_html_components as html
##import dash_leaflet as dl
##import dash_leaflet.express as dlx

##from dash.dependencies import Output, Input

### Generate some in-memory data.
##bermuda = dlx.dicts_to_geojson([dict(lat=32.299507, lon=-64.790337)])
##biosfera = dlx.geojson_to_geobuf(dlx.dicts_to_geojson([dict(lat=29.015, lon=-118.271)]))
### Create example app.
##app = dash.Dash()
##app.layout = html.Div([
##    dl.Map(center=[39, -98], zoom=4, children=[
##        dl.TileLayer(),
##        dl.GeoJSON(data=bermuda),  # in-memory geojson (slowest option)
##        dl.GeoJSON(data=biosfera, format="geobuf"),  # in-memory geobuf (smaller payload than geojson)
##        dl.GeoJSON(url="/assets/us-state-capitals.json", id="capitals"),  # geojson resource (faster than in-memory)
##        dl.GeoJSON(url="/assets/us-states.pbf", format="geobuf", id="states",
##                   hoverStyle=dict(weight=5, color='#666', dashArray='')),  # geobuf resource (fastest option)
##    ], style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}, id="map"),
##    html.Div(id="state"), html.Div(id="capital")
##])


##@app.callback(Output("capital", "children"), [Input("capitals", "click_feature")])
##def capital_click(feature):
##    if feature is not None:
##        return f"You clicked {feature['properties']['name']}"


##@app.callback(Output("state", "children"), [Input("states", "hover_feature")])
##def state_hover(feature):
##    if feature is not None:
##        return f"{feature['properties']['name']}"


##if __name__ == '__main__':
##    app.run_server()


##    ############# test js app             Results - WORKS!
## import random
## import dash
## import dash_html_components as html
## import dash_leaflet as dl
## import dash_leaflet.express as dlx
##
## # Create some markers.
## points = [dict(lat=55.5 + random.random(), lon=9.5 + random.random(), value=random.random()) for i in range(100)]
##
## data = dlx.dicts_to_geojson(points)
## # Create geojson.
## geojson = dl.GeoJSON(data=data, options=dict(pointToLayer="window.dash_props.module.point_to_layer"))
##
## print(geojson)
## # Create the app.
## app = dash.Dash()
## app.layout = html.Div([
##    dl.Map([dl.TileLayer(), geojson], center=(56, 10), zoom=8, style={'height': '50vh'}),
## ])
##
## if __name__ == '__main__':
##    app.run_server(debug=True)

##
## #
##    #############  python function          can't find file
##
## import random
## import dash
## import dash_html_components as html
## import dash_leaflet as dl
## import prop_funcs as pf  # module containing the point_to_layer function
##
##
##
## import dash_leaflet.express as dlx
##
## from dash_transcrypt import inject_js, module_to_props
##
##
##
## # Create some markers.
## points = [dict(lat=55.5 + random.random(), lon=9.5 + random.random(), value=random.random()) for i in range(100)]
## data = dlx.dicts_to_geojson(points)
## # Create geojson.
## js = module_to_props(pf)
## geojson = dl.GeoJSON(data=data, options=dict(pointToLayer=pf.point_to_layer))
## # Create the app.
## app = dash.Dash()
## app.layout = html.Div([
##    dl.Map([dl.TileLayer(), geojson], center=(56, 10), zoom=8, style={'height': '50vh'}),
## ])
## inject_js(app, js)
##
## if __name__ == '__main__':
##     app.run_server()


##
## import random
## import dash
## import dash_html_components as html
## import dash_leaflet as dl
## import dash_leaflet.express as dlx
##
## # Create some markers.
## points = [dict(lat=55.5 + random.random(), lon=9.5 + random.random(), value=random.random()) for i in range(100)]
## data = dlx.dicts_to_geojson(points)
## # Create geojson.
## geojson = dl.GeoJSON(data=data, options=dict(pointToLayer="window.dash_props.module.point_to_layer"))
## # Create the app.
## app = dash.Dash()
## app.layout = html.Div([
##     dl.Map([dl.TileLayer(), geojson], center=(56, 10), zoom=8, style={'height': '50vh'}),
## ])
##
## if __name__ == '__main__':
##     app.run_server()


# import json
# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# import dash_leaflet as dl
# import dash_leaflet.express as dlx
# import pandas as pd
# import numpy as np
# import pathlib

# from dash.dependencies import Output, Input
# from dash_leaflet.express import scatter
# from dash_transcrypt import inject_js, module_to_props


# PATH = pathlib.Path(__file__).parent
# DATA_PATH = PATH.joinpath("./assets").resolve()

## region Data


# df = pd.read_excel(
#       DATA_PATH.joinpath('uscities.xlsx'))
# print(df)
# color_prop = 'population'


# def get_data(state):
#   df_state = df[df["state_id"] == state]  # pick one state
#   df_state = df_state[['lat', 'lng', 'city', 'population', 'density']]  # drop irrelevant columns
#   df_state = df_state[df_state[color_prop] > 0]  # drop abandoned cities
#   df_state[color_prop] = np.log(df_state[color_prop])  # take log as the values varies A LOT
#   geojson = dlx.dicts_to_geojson(df_state.to_dict('rows'), lon="lng")  # convert to geojson
#   geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geojson
#   print(geobuf)
#   return geobuf


# def get_minmax(state):
#   df_state = df[df["state_id"] == state]  # pick one state
#   return dict(min=0, max=np.log(df_state[color_prop].max()))


## Setup a few color scales.
# csc_map = {"Rainbow": ['red', 'yellow', 'green', 'blue', 'purple'],
#          "Hot": ['yellow', 'red', 'black'],
#          "Viridis": "Viridis"}
# csc_options = [dict(label=key, value=json.dumps(csc_map[key])) for key in csc_map]
# default_csc = "Rainbow"
# dd_csc = dcc.Dropdown(options=csc_options, value=json.dumps(csc_map[default_csc]), id="dd_csc", clearable=False)
## Setup state options.
# states = df["state_id"].unique()
# state_names = [df[df["state_id"] == state]["state_name"].iloc[0] for state in states]
# state_options = [dict(label=state_names[i], value=state) for i, state in enumerate(states)]
# default_state = "CA"
# dd_state = dcc.Dropdown(options=state_options, value=default_state, id="dd_state", clearable=False)

## endregion

# minmax = get_minmax(default_state)
## Create geojson.
# js = module_to_props(scatter)
# geojson = dl.GeoJSON(data=get_data(default_state), id="geojson", format="geobuf",
#                    zoomToBounds=True,  # when true, zooms to bounds when data changes
#                    cluster=True,  # when true, data are clustered
#                    clusterToLayer=scatter.cluster_to_layer,  # how to draw clusters
#                    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
#                    options=dict(
#                        pointToLayer=scatter.point_to_layer,  # how to draw points
#                        onEachFeature=scatter.bind_popup  # bind a popup to each feature
#                    ),
#                    superClusterOptions=dict(radius=150),  # adjust cluster size
#                    hideout=dict(
#                        colorscale=csc_map[default_csc],  # what colorscale to use
#                        color_prop=color_prop,  # the property used to determine the color
#                        popup_prop='city',  # the property shown in the popup
#                        **minmax)
#                    )
## Create a colorbar.
# colorbar = dl.Colorbar(colorscale=csc_map[default_csc], id="colorbar", width=20, height=150, **minmax)
## Create the app.
# chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # for dash_leaflet.geojson.scatter
# app = dash.Dash(external_scripts=[chroma], prevent_initial_callbacks=True)
# app.layout = html.Div([
#   dl.Map([dl.TileLayer(), geojson, colorbar]), html.Div([dd_state, dd_csc],
#            style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"})
# ], style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block", "position": "relative"})
# inject_js(app, js)


# @app.callback([Output("geojson", "hideout"), Output("geojson", "data"), Output("colorbar", "colorscale"),
#              Output("colorbar", "min"), Output("colorbar", "max")],
#             [Input("dd_csc", "value"), Input("dd_state", "value")])
# def update(csc, state):
#   csc, data, mm = json.loads(csc), get_data(state), get_minmax(state)
#   hideout = dict(colorscale=csc, color_prop=color_prop, popup_prop='city', **mm)
#   return hideout, data, csc, mm["min"], mm["max"]


# if __name__ == '__main__':
#   app.run_server()

## import json
## import dash
## import dash_core_components as dcc
## import dash_html_components as html
## import dash_leaflet as dl
## import dash_leaflet.express as dlx
## import pandas as pd
## import numpy as np
## import pathlib
##
##
## from dash.dependencies import Output, Input
##
##
## from urllib.request import urlopen
##
## with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
##     counties = json.load(response)
##
## print(counties)
##
## # region Data
##
## PATH = pathlib.Path(__file__).parent
## DATA_PATH = PATH.joinpath("./assets").resolve()
## df = pd.read_excel(
##        DATA_PATH.joinpath('uscities.xlsx'))
## print(df)
##
## #df = pd.read_csv("assets/uscities.csv")  # data from https://simplemaps.com/data/us-cities
## color_prop = 'population'
##
##
## def get_data(state):
##    df_state = df[df["state_id"] == state]  # pick one state
##    df_state = df_state[['lat', 'lng', 'city', 'population', 'density']]  # drop irrelevant columns
##    df_state = df_state[df_state[color_prop] > 0]  # drop abandoned cities
##    df_state[color_prop] = np.log(df_state[color_prop])  # take log as the values varies A LOT
##    dicts = df_state.to_dict('rows')
##    for item in dicts:
##        item["tooltip"] = "{:.1f}".format(item[color_prop])  # bind tooltip
##        item["popup"] = item["city"]  # bind popup
##    geojson = dlx.dicts_to_geojson(dicts, lon="lng")  # convert to geojson
##    geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf
##    return geobuf
##
##
## def get_minmax(state):
##    df_state = df[df["state_id"] == state]  # pick one state
##    return dict(min=0, max=np.log(df_state[color_prop].max()))
##
##
## # Setup a few color scales.
## csc_map = {"Rainbow": ['red', 'yellow', 'green', 'blue', 'purple'],
##           "Hot": ['yellow', 'red', 'black'],
##           "Viridis": "Viridis"}
## csc_options = [dict(label=key, value=json.dumps(csc_map[key])) for key in csc_map]
## default_csc = "Rainbow"
## dd_csc = dcc.Dropdown(options=csc_options, value=json.dumps(csc_map[default_csc]), id="dd_csc", clearable=False)
## # Setup state options.
## states = df["state_id"].unique()
## state_names = [df[df["state_id"] == state]["state_name"].iloc[0] for state in states]
## state_options = [dict(label=state_names[i], value=state) for i, state in enumerate(states)]
## default_state = "CA"
## dd_state = dcc.Dropdown(options=state_options, value=default_state, id="dd_state", clearable=False)
##
## # endregion
##
## minmax = get_minmax(default_state)
## # Create geojson.
## geojson = dl.GeoJSON( id="geojson", format="geobuf",
##                     zoomToBounds=True,  # when true, zooms to bounds when data changes
##                     cluster=True,  # when true, data are clustered
##                     clusterToLayer=dlx.scatter.cluster_to_layer,  # how to draw clusters
##                     zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
##                     options=dict(pointToLayer=dlx.scatter.point_to_layer),  # how to draw points
##                     superClusterOptions=dict(radius=150),  # adjust cluster size
##                  #   hideout=dict(colorscale=csc_map[default_csc], color_prop=color_prop, **minmax)
##                      )
##
## # Create a colorbar.
## colorbar = dl.Colorbar(colorscale=csc_map[default_csc], id="colorbar", width=20, height=150, **minmax)
## # Create the app.
## #chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
## # app = dash.Dash(external_scripts=[chroma], prevent_initial_callbacks=True)
## app = dash.Dash( prevent_initial_callbacks=True)
## app.layout = html.Div([
##    dl.Map([dl.TileLayer(), geojson, colorbar]), html.Div([dd_state, dd_csc],
##                                                          style={"position": "relative", "bottom": "80px",
##                                                                 "left": "10px", "z-index": "1000",
##                                                                 "width": "200px"})
## ], style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block", "position": "relative"})
##
##
## @app.callback(
##     [
##         Output("geojson", "hideout"),
##         Output("geojson", "data"),
##         Output("colorbar", "colorscale"),
##         Output("colorbar", "min"),
##         Output("colorbar", "max")
##     ],
##     [Input("dd_csc", "value"), Input("dd_state", "value")])
## def update(csc, state):
##    csc, data, mm = json.loads(csc), get_data(state), get_minmax(state)
##    hideout = dict(colorscale=csc, color_prop=color_prop, popup_prop='city', **mm)
##    return data, csc, mm["min"], mm["max"]
##
##
## if __name__ == '__main__':
##    app.run_server()


import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_leaflet.express as dlx
import pandas as pd
import numpy as np
import plotly.graph_objects as go


from dash.dependencies import Output, Input

# region Data


import pathlib

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data_prep_city").resolve()
df = pd.read_excel(DATA_PATH.joinpath("uscities.xlsx"))


# df = pd.read_csv("assets/uscities.csv")  # data from https://simplemaps.com/data/us-cities
color_prop = "population"


def get_data(state):
    df_state = df[df["state_id"] == state]  # pick one state
    df_state = df_state[
        ["lat", "lng", "city", "population", "density"]
    ]  # drop irrelevant columns
    df_state = df_state[df_state[color_prop] > 0]  # drop abandoned cities
    df_state[color_prop] = np.log(
        df_state[color_prop]
    )  # take log as the values varies A LOT
    dicts = df_state.to_dict("rows")
    for item in dicts:
        item["tooltip"] = "{:.1f}".format(item[color_prop])  # bind tooltip
        item["popup"] = item["city"]  # bind popup
    geojson = dlx.dicts_to_geojson(dicts, lon="lng")  # convert to geojson
    geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf
    return geobuf


def get_minmax(state):
    df_state = df[df["state_id"] == state]  # pick one state
    return dict(min=0, max=np.log(df_state[color_prop].max()))


# Setup a few color scales.
csc_map = {
    "Rainbow": ["red", "yellow", "green", "blue", "purple"],
    "Hot": ["yellow", "red", "black"],
    "Viridis": "Viridis",
}
csc_options = [dict(label=key, value=json.dumps(csc_map[key])) for key in csc_map]
default_csc = "Rainbow"
dd_csc = dcc.Dropdown(
    options=csc_options,
    value=json.dumps(csc_map[default_csc]),
    id="dd_csc",
    clearable=False,
)
# Setup state options.
states = df["state_id"].unique()
state_names = [df[df["state_id"] == state]["state_name"].iloc[0] for state in states]
state_options = [
    dict(label=state_names[i], value=state) for i, state in enumerate(states)
]
default_state = "CA"
dd_state = dcc.Dropdown(
    options=state_options, value=default_state, id="dd_state", clearable=False
)

# endregion

minmax = get_minmax(default_state)
# Create geojson.
geojson = dl.GeoJSON(
    data=get_data(default_state),
    id="geojson",
    format="geobuf",
    zoomToBounds=True,  # when true, zooms to bounds when data changes
    cluster=True,  # when true, data are clustered
    clusterToLayer=dlx.scatter.cluster_to_layer,  # how to draw clusters
    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
    options=dict(pointToLayer=dlx.scatter.point_to_layer),  # how to draw points
    superClusterOptions=dict(radius=150),  # adjust cluster size
    hideout=dict(colorscale=csc_map[default_csc], color_prop=color_prop, **minmax),
)
# Create a colorbar.
colorbar = dl.Colorbar(
    colorscale=csc_map[default_csc], id="colorbar", width=20, height=150, **minmax
)
# Create the app.
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
app = dash.Dash(external_scripts=[chroma], prevent_initial_callbacks=True)


###  Make choropleth map


def make_choropleth():
    dfc = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/2011_us_ag_exports.csv"
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=dfc["code"],  # Spatial coordinates
            z=dfc["total exports"].astype(float),  # Data to be color-coded
            locationmode="USA-states",  # set of locations match entries in `locations`
            colorscale="Reds",
            colorbar_title="Millions USD",
        )
    )

    fig.update_layout(
        title_text="2011 US Agriculture Exports by State",
        geo_scope="usa",  # limite map scope to USA
    )
    return fig


tab1_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("This is tab 1!", className="card-text"),
            dbc.Button("Click here", color="success"),
        ]
    ),
    className="mt-3",
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("This is tab 2!", className="card-text"),
            dbc.Button("Don't click here", color="danger"),
            html.Div(
                [
                    dl.Map([dl.TileLayer(), geojson, colorbar]),
                    html.Div(
                        [dd_state, dd_csc],
                        style={
                            "position": "relative",
                            "bottom": "80px",
                            "left": "10px",
                            "z-index": "1000",
                            "width": "200px",
                        },
                    ),
                ],
                style={
                    "width": "100%",
                    "height": "50vh",
                    "margin": "auto",
                    "display": "block",
                    "position": "relative",
                },
            ),
        ]
    ),
    className="mt-3",
)


tabs = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label="Tab 1"),
        dbc.Tab(tab2_content, label="Tab 2"),
        dbc.Tab("This tab's content is never seen", label="Tab 3", disabled=True),
    ]
)


app.layout = dbc.Container(tabs)


# app.layout = dbc.Container(
#    dbc.Tabs(
#            [
#                dbc.Tab(
#                    dcc.Graph(id='choropleth', figure=make_choropleth()),
#                    tab_id="plotly",
#                    label="plotly",
#                ),
#                dbc.Tab(
#                    html.Div([
#                        dl.Map([dl.TileLayer(), geojson, colorbar]),
#                        html.Div([dd_state, dd_csc],
#                        style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"})
#                    ], style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block", "position": "relative"}),
#                    tab_id="leaflet",
#                    label="leaflet",
#                ),
#            ],
#            id="tabs",
#            active_tab="leaflet",
#        ),
#    className="p-5",
# )


@app.callback(
    [
        Output("geojson", "hideout"),
        Output("geojson", "data"),
        Output("colorbar", "colorscale"),
        Output("colorbar", "min"),
        Output("colorbar", "max"),
    ],
    [Input("dd_csc", "value"), Input("dd_state", "value")],
)
def update(csc, state):
    csc, data, mm = json.loads(csc), get_data(state), get_minmax(state)
    hideout = dict(colorscale=csc, color_prop=color_prop, popup_prop="city", **mm)
    return hideout, data, csc, mm["min"], mm["max"]


if __name__ == "__main__":
    app.run_server(debug=True)
