
#import dash
#import dash_leaflet as dl

#app = dash.Dash()
#app.layout = dl.Map(dl.TileLayer(), style={'width': '1000px', 'height': '500px'})

#if __name__ == '__main__':
#    app.run_server()   





























import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import pandas as pd
import numpy as np
import pathlib

from dash.dependencies import Output, Input
from dash_leaflet.geojson import scatter
from dash_transcrypt import inject_js, module_to_props


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()

# region Data


#df = pd.read_csv("uscities.csv")

#with open(DATA_PATH.joinpath("df_exp.pickle"), "rb") as handle:
#    df_exp = pickle.load(handle)

df = pd.read_csv("uscities.csv")

#df = pd.read_excel("stateuscities.csv")  # data from https://simplemaps.com/data/us-cities
color_prop = 'population'


def get_data(state):
    df_state = df[df["state_id"] == state]  # pick one state
    df_state = df_state[['lat', 'lng', 'city', 'population', 'density']]  # drop irrelevant columns
    df_state = df_state[df_state[color_prop] > 0]  # drop abandoned cities
    df_state[color_prop] = np.log(df_state[color_prop])  # take log as the values varies A LOT
    geojson = dlx.dicts_to_geojson(df_state.to_dict('rows'), lon="lng")  # convert to geojson
    geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geojson
    return geobuf


def get_minmax(state):
    df_state = df[df["state_id"] == state]  # pick one state
    return dict(min=0, max=np.log(df_state[color_prop].max()))


# Setup a few color scales.
csc_map = {"Rainbow": ['red', 'yellow', 'green', 'blue', 'purple'],
           "Hot": ['yellow', 'red', 'black'],
           "Viridis": "Viridis"}
csc_options = [dict(label=key, value=json.dumps(csc_map[key])) for key in csc_map]
default_csc = "Rainbow"
dd_csc = dcc.Dropdown(options=csc_options, value=json.dumps(csc_map[default_csc]), id="dd_csc", clearable=False)
# Setup state options.
states = df["state_id"].unique()
state_names = [df[df["state_id"] == state]["state_name"].iloc[0] for state in states]
state_options = [dict(label=state_names[i], value=state) for i, state in enumerate(states)]
default_state = "CA"
dd_state = dcc.Dropdown(options=state_options, value=default_state, id="dd_state", clearable=False)

# endregion

minmax = get_minmax(default_state)
# Create geojson.
js = module_to_props(scatter)
geojson = dl.GeoJSON(data=get_data(default_state), id="geojson", format="geobuf",
                     zoomToBounds=True,  # when true, zooms to bounds when data changes
                     cluster=True,  # when true, data are clustered
                     clusterToLayer=scatter.cluster_to_layer,  # how to draw clusters
                     zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
                     options=dict(
                         pointToLayer=scatter.point_to_layer,  # how to draw points
                         onEachFeature=scatter.bind_popup  # bind a popup to each feature
                     ),
                     superClusterOptions=dict(radius=150),  # adjust cluster size
                     hideout=dict(
                         colorscale=csc_map[default_csc],  # what colorscale to use
                         color_prop=color_prop,  # the property used to determine the color
                         popup_prop='city',  # the property shown in the popup
                         **minmax)
                     )
# Create a colorbar.
colorbar = dl.Colorbar(colorscale=csc_map[default_csc], id="colorbar", width=20, height=150, **minmax)
# Create the app.
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # for dash_leaflet.geojson.scatter
app = dash.Dash(external_scripts=[chroma], prevent_initial_callbacks=True)
app.layout = html.Div([
    dl.Map([dl.TileLayer(), geojson, colorbar]), html.Div([dd_state, dd_csc],
             style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"})
], style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block", "position": "relative"})
inject_js(app, js)


@app.callback([Output("geojson", "hideout"), Output("geojson", "data"), Output("colorbar", "colorscale"),
               Output("colorbar", "min"), Output("colorbar", "max")],
              [Input("dd_csc", "value"), Input("dd_state", "value")])
def update(csc, state):
    csc, data, mm = json.loads(csc), get_data(state), get_minmax(state)
    hideout = dict(colorscale=csc, color_prop=color_prop, popup_prop='city', **mm)
    return hideout, data, csc, mm["min"], mm["max"]


if __name__ == '__main__':
    app.run_server()
