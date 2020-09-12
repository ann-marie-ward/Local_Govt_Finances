
import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Group

import dash_html_components as html
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import pandas as pd
import pathlib
import pickle
import colorlover
import dash_leaflet as dl
import dash_leaflet.express as dlx

from app import app
import data_utilities as du


pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 10)


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("./data").resolve()


with open(DATA_PATH.joinpath("df_lat_lng.pickle"), "rb") as handle:
    df_lat_lng = pickle.load(handle)



# Local  Expenditures and Revenue df
def get_df_exp_rev(ST):
    """ loads the df_exp and df_rev files by state and adds Cat and Descr columns"""
    filename = "".join(["exp_rev_", ST, ".pickle"])
    with open(DATA_PATH.joinpath(filename), "rb") as handle:
        local_df_exp, local_df_rev = pickle.load(handle)

    local_df_exp = pd.merge(local_df_exp, du.df_cat_desc, how="left", on="Line")
    local_df_rev = pd.merge(local_df_rev, du.df_cat_desc, how="left", on="Line")


    ### TODO move add lat long to data prep?
    # local_df_exp = pd.merge(local_df_exp, df_lat_lng, how='left', left_on=['County name', 'ID name'],  right_on =['county_name', 'city'])
    # local_df_exp['lat'] = local_df_exp['lat'].fillna(0)
    #
    # local_df_rev = pd.merge(local_df_rev, df_lat_lng, how='left', left_on=['County name', 'ID name'],
    #                        right_on=['county_name', 'city'])
    # local_df_rev['lat'] = local_df_rev['lat'].fillna(0)

    ### TODO move rename to data prep
    # this makes "ID code" the "id" for the dash datatable functions
    local_df_exp = local_df_exp.rename(columns={"ID code": "id"})
    local_df_rev = local_df_rev.rename(columns={"ID code": "id"})
    return local_df_exp, local_df_rev


# initialize Local


rev = {}
exp = {}
for STATE in du.abbr_state_noUS:
    exp[STATE], rev[STATE] = get_df_exp_rev(STATE)
init_local_df_exp = exp[du.INIT_ST]
init_local_df_rev = rev[du.INIT_ST]



# initialize State
# Update this when new data is added:




# Local level
def year_filter(dff, year):
    """ renames columns so selected year doesn't have the year extension ie Amount_2017 """
    return dff.rename(
        columns={
            du.get_col("Amount", year): "Amount",
            du.get_col("Per Capita", year): "Per Capita",
            du.get_col("Per Student", year): "Per Student",
        }
    )


#leaflet map: Create geojson.

geojson = dl.GeoJSON( id="geojson", format="geobuf",
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    cluster=True,  # when true, data are clustered
                    clusterToLayer=dlx.scatter.cluster_to_layer,  # how to draw clusters
                    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
                    options= # how to draw points
                             dict(onEachFeature="window.dash_props.module.on_each_feature"), #popup in callback
                    superClusterOptions=dict(radius=150),  # adjust cluster size
                    hideout={}
                     )
local_map =  dl.Map([dl.TileLayer(url="https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png"),
                          geojson], zoom=6, center=(33.5, -86.8), id="leaflet")




#############  Local Table    ################################################


#############  Optional columns to show it the table

local_columns = [
    {"id": "id", "name": [' ', "id"], "type": "text"},
    {"id": "ST", "name": [" ", "State"], "type": "text"},
    {"id": "County name", "name": [" ", "County"], "type": "text"},
    {"id": "ID name", "name": [" ", "Name"], "type": "text"},
    {"id": "Category", "name": [" ", "Category"], "type": "text"},
    {"id": "Description", "name": [" ", "Sub Category"], "type": "text"},
    {
        "id": "Amount",
        "name": [" ", "Total Amount",],
        "type": "numeric",
        "format": FormatTemplate.money(0),
    },
]

percapita_columns = [
    {
        "id": "Per Capita",
        "name": [" ", "Per Capita"],
        "type": "numeric",
        "format": FormatTemplate.money(0),
    },
    {
        "id": "Population",
        "name": [" ", "Population"],
        "type": "numeric",
        "format": Format(group=Group.yes),
    },
    {
        "id": "sparkline_Per Capita",
        "name": ["Per Capita", "2014-2017"],
        "type": "text",
    },
]

perstudent_columns = [
    {
        "id": "Per Student",
        "name": [" ", "Per Student"],
        "type": "numeric",
        "format": FormatTemplate.money(0),
    },
    {
        "id": "Enrollment",
        "name": [" ", "School Enrollment"],
        "type": "numeric",
        "format": Format(group=Group.yes),
    },
    {
        "id": "sparkline_Per Student",
        "name": ["Per Student", "2014-2017"],
        "type": "text",
    },
]

local_datatable = html.Div(
    [
        dash_table.DataTable(
            id="local_table",
            columns=local_columns + percapita_columns,
            merge_duplicate_headers=True,
            # data=init_local_df_exp.to_dict("records"),
            # filter_action='native',
            sort_action="native",
            export_format="xlsx",
            export_headers="display",
            row_selectable ='single',
            # row_deletable = True,
            is_focused=False,
            cell_selectable=False,
            page_size=50,
            style_table={
                "overflowY": "scroll",
                "border": "thin lightgrey solid",
                "height": "425px",
            },
            style_header={"font-size": "16px"},
            style_cell={
                "textAlign": "left",
                "font-family": "arial",
                "font-size": "14px",
            },
            style_cell_conditional=[
                {"if": {"column_id": c}, "textAlign": "right"}
                for c in [
                    "Per Capita",
                    "Per Student",
                    "Amount",
                    "Population",
                    "Enrollment",
                ]
            ],
            style_data_conditional=[
                {
                    "if": {"column_id": c},
                    "width": 100,
                    "font-family": "Sparks-Bar-Extrawide",
                    "padding-right": "15px",
                    "padding-left": "15px",
                }
                for c in ["sparkline_Per Capita", "sparkline_Per Student"]
            ],
        )
    ],
    className="mb-5",
)



#####################   Header Cards and Markdown #############################
first_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("", className="card-title"),
            html.P(""),

        ], style={'height': '75px'}
    )
)


#####################################  callbacks ###########################################



#######  Local only updates:

####### Update counties when state changes
@app.callback([Output("local_county_dropdown", "options"), ], [Input("state", "value")])
def update_counties(state):
    if state == "USA":
        state = du.INIT_STATE
    options = [{"label": "All Counties", "value": "all"}] + [
        {"label": c, "value": c}
        for c in exp[du.state_abbr[state]]["County name"]
            .sort_values()
            .dropna()
            .unique()
    ]
    return [options]



####### Update local names when county and type changes
@app.callback(
    Output("local_name_dropdown", "options"),
    [
        Input("state", "value"),
        Input("local_county_dropdown", "value"),
        Input("local_type", "value"),
    ],
)
def update_counties(
    state, county, local_type,
):

    if state == "USA":
        state = "Alabama"

    dff = exp[du.state_abbr[state]].copy()

    if local_type and (local_type != "all"):
        if local_type == 'c':
            dff = dff[dff["Gov Type"].str.contains('2', na=False) | dff["Gov Type"].str.contains('3', na=False)]
        else:
            dff = dff[dff["Gov Type"].str.contains(local_type, na=False)]
    if county and (county != "all"):
        dff = dff[dff["County name"] == county]

    return [{"label": "All Cities", "value": "all"}] + [
        {"label": name, "value": name}
        for name in dff["ID name"].sort_values().dropna().unique()
    ]


##############  Update Layout results


#####  Update local table
@app.callback(
    [
        Output("local_table", "data"),
        Output("local_table", "columns"),
        Output("local_title", "children"),
        Output("collapse", "is_open"),

    ],
    [
        Input("store_exp_or_rev", "data"),
        Input("year", "value"),
        Input("category_dropdown", "value"),
        Input("subcategory_dropdown", "value"),
        Input("state", "value"),
        Input("local_type", "value"),
        Input("local_county_dropdown", "value"),
        Input("local_name_dropdown", "value"),
    ],
    # prevent_initial_call=True,
)
def update_local_table(exp_or_rev, year, cat, subcat, state, type, county, name):

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if state == "USA":
        state = "Alabama"
    if year < int(min(du.LOCAL_YEARS)):
        year = int(du.LOCAL_YEARS)

    title = " ".join([str(year), state, exp_or_rev])
    update_title = title

    df_table = (
        rev[du.state_abbr[state]]
        if exp_or_rev == "Revenue"
        else exp[du.state_abbr[state]]
    )

    # filter  table
    if type and (type != "all"):
        if type == 'c':
            df_table = df_table[df_table["Gov Type"].str.contains('2', na=False) | df_table["Gov Type"].str.contains('3', na=False)].copy()
        else:
            df_table = df_table[df_table["Gov Type"].str.contains(type, na=False)]
        update_title = " ".join([title, " --> ", du.code_type[type]])
    if cat and (cat != "all"):
        df_table = df_table[df_table["Category"] == cat]
        title = " ".join([update_title, "-->", cat])
    if subcat and (subcat != "all"):
        df_table = df_table[df_table["Description"] == subcat]
        title = " ".join([title, "-->", subcat])
    if county and (county != "all"):
        df_table = df_table[df_table["County name"] == county]
        update_title = " ".join([title, county, " county"])
    if name and (name != "all"):
        df_table = df_table[df_table["ID name"] == name]

    # subtotal table
    main_columns = ["ST", "id", "County name", "ID name", "Gov Type"]
    if subcat:
        df_table = (
            df_table.groupby(main_columns + ["Category", "Description"])
            .sum()
            .reset_index()
        )
    elif cat:
        df_table = df_table.groupby(main_columns + ["Category"]).sum().reset_index()
    else:
        df_table = df_table.groupby(main_columns).sum().reset_index()

    # remove empty cols
    df_table = df_table.loc[:, (df_table != 0).any(axis=0)]

    if df_table.empty:
        return [], [], [], True

    # school district columns
    if (df_table["Gov Type"] == "5").all():
        columns = local_columns + perstudent_columns
        df_table["sparkline_Per Student"] = du.make_sparkline(
            df_table, "Per Student", du.LOCAL_YEARS
        )
        df_table = year_filter(df_table, str(year))
        df_table["Enrollment"] = df_table["Amount"] / df_table["Per Student"]
        update_title = " ".join([update_title, du.code_type["5"]])

    # special districts columns
    elif (df_table["Gov Type"] == "4").all():
        columns = local_columns
        df_table = year_filter(df_table, str(year))
        update_title = " ".join([update_title, du.code_type["4"]])
    else:
        # LOCAL columns
        columns = local_columns + percapita_columns
        df_table["sparkline_Per Capita"] = du.make_sparkline(
            df_table, "Per Capita", du.LOCAL_YEARS
        )
        df_table = year_filter(df_table, str(year))
        df_table["Population"] = df_table["Amount"] / df_table["Per Capita"]

    return df_table.to_dict("records"), columns, update_title, False



@app.callback(
    Output("local_map", "children"),
    [Input("tabs", "active_tab")],
    [State("local_map", "children")],
    prevent_initial_call=True,
)
def render_map(at, children):
    # Don't render until active_tab is leaflet, and render only the first time
    print('im in the map render  callback')
    if not at or at != "local_tab" or children:
        raise PreventUpdate
    # Render map here.
    print('render')
    return local_map


# update Local styles and bar chart and map:
@app.callback(
    [
        Output("local_table", "style_data_conditional"),
        Output("local_bar_charts_container", "children"),
        Output("local_legend", "children"),
        Output("geojson", "hideout"),
        Output("geojson", "data"),
        Output('leaflet','viewport'),

    ],
    [
        Input("tabs", "active_tab"),
        Input("local_table", "derived_virtual_data"),
        Input("local_table", "derived_viewport_row_ids"),
        Input("local_table", "derived_virtual_selected_row_ids"),
    ],
    [
        State('local_table', "data"),
        State("local_map", "children")
    ],
   # prevent_initial_call=True,
)
def update_local_table(at, data, viewport_ids, selected_row_id, data_state, local_map):
    #TODO don't pass entire map.  just need to see if it exists

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]


    dff = pd.DataFrame(data)
    if (not at) or (at != "local_tab") or (local_map is None) or dff.empty:
        raise PreventUpdate
    else:
        if "Per Capita" in dff:
            color_column = "Per Capita"
        elif "Per Student" in dff:
            color_column = "Per Student"
        else:
            color_column = "Amount"

        (styles, legend, df_color, max_y) = du.discrete_background_color_bins(
            dff, columns=[color_column]
        )

        styles = styles + [
            {
                "if": {"column_id": c},
                "width": 100,
                "font-family": "Sparks-Bar-Extrawide",
                "font-size": "18px",
                "padding-right": "15px",
                "padding-left": "15px",
            }
            for c in ["sparkline_Per Capita", "sparkline_Per Student"]
        ]

        bar_charts = []
        if (not df_color.empty) and (len(dff['id'].unique()) > 1):
            dff[color_column + "_color"] = df_color
            dff = dff[dff["id"].isin(viewport_ids)]
            bar_charts = du.make_bar_charts(dff, color_column, "ID name", clip=max_y)


        # update map
        dff_state = pd.DataFrame(data_state)
        dff_lat_lng = df_lat_lng[df_lat_lng['state_id'] == dff_state['ST'].iat[0]]

        dff_state['name'] = dff_state['ID name'].str[:-4]
        dff_state = pd.merge(dff_state, dff_lat_lng, how='left', left_on=['County name', 'name'],
                            right_on=['county_name', 'city'])
        dff_state = dff_state.dropna()
        dicts = dff_state.to_dict('row')

        for item in dicts:
            item["popup"] = "${:.0f} per capita    {}".format(item[color_column], item['name'])
            item["tooltip"] = item["name"]  # bind popup
        geojson_data = dlx.dicts_to_geojson(dicts, lon="lng")  # convert to geojson
        geobuf = dlx.geojson_to_geobuf(geojson_data)  # convert to geobuf

        colors = colorlover.scales[str(5)]["seq"]["Blues"]
        hideout = dict(colorscale=colors, color_prop=color_column, popup_prop='name', min=0, max=max_y,
                       circle_options= dict(radius = 10))

        if selected_row_id and selected_row_id != []:

            selected_row = dff_state[dff_state['id'].isin(selected_row_id)]

            lat = selected_row.iloc[0]['lat']
            lng = selected_row.iloc[0]['lng']

            hideout = dict(colorscale=colors, color_prop=color_column, popup_prop='name', min=0, max=max_y,
                           open=selected_row_id[0],
                           circle_options=dict(radius=10))
            return styles, bar_charts, legend, hideout, geobuf,  {'zoom':12, 'center':[lat, lng]}

        else:
            return styles, bar_charts, legend, hideout, geobuf, {}
