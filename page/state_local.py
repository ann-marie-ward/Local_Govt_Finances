# see this example for correctly sizing map in tab  http://jsfiddle.net/ve2huzxw/52/
# county shape files by fips and leaflet:  https://stackoverflow.com/questions/58152812/how-do-i-map-county-level-data-as-a-heatmap-using-fips-codes-interactively-in


import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Group

import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly_express as px

import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import pathlib
import pickle
import colorlover
import json
import dash_leaflet as dl
import dash_leaflet.express as dlx

from app import app, navbar, footer


import data_utilities as du

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 10)


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()


with open(DATA_PATH.joinpath("df_exp.pickle"), "rb") as handle:
    df_exp = pickle.load(handle)

with open(DATA_PATH.joinpath("df_rev.pickle"), "rb") as handle:
    df_rev = pickle.load(handle)

with open(DATA_PATH.joinpath("df_lat_lng.pickle"), "rb") as handle:
    df_lat_lng = pickle.load(handle)



# Local  Expenditures and Revenue df
def get_df_exp_rev(ST):
    """ loads the df_exp and df_rev files by state and adds Cat and Descr columns"""
    filename = "".join(["exp_rev_", ST, ".pickle"])
    with open(DATA_PATH.joinpath(filename), "rb") as handle:
        city_df_exp, city_df_rev = pickle.load(handle)

    city_df_exp = pd.merge(city_df_exp, du.df_cat_desc, how="left", on="Line")
    city_df_rev = pd.merge(city_df_rev, du.df_cat_desc, how="left", on="Line")


    ### TODO move add lat long to data prep?
    # city_df_exp = pd.merge(city_df_exp, df_lat_lng, how='left', left_on=['County name', 'ID name'],  right_on =['county_name', 'city'])
    # city_df_exp['lat'] = city_df_exp['lat'].fillna(0)
    #
    # city_df_rev = pd.merge(city_df_rev, df_lat_lng, how='left', left_on=['County name', 'ID name'],
    #                        right_on=['county_name', 'city'])
    # city_df_rev['lat'] = city_df_rev['lat'].fillna(0)

    ### TODO move rename to data prep
    # this makes "ID code" the "id" for the dash datatable functions
    city_df_exp = city_df_exp.rename(columns={"ID code": "id"})
    city_df_rev = city_df_rev.rename(columns={"ID code": "id"})
    return city_df_exp, city_df_rev


# initialize Local
init_STATE = "AL"
rev = {}
exp = {}
for STATE in du.abbr_state_noUS:
    exp[STATE], rev[STATE] = get_df_exp_rev(STATE)

init_city_df_exp = exp[init_STATE]
init_city_df_rev = rev[init_STATE]


# initialize State
# Update this when new data is added:
YEARS = [str(year) for year in range(2012, 2018)]
CITY_YEARS = [str(year) for year in range(2014, 2018)]
START_YR = "2017"

init_cat = "Public Safety"
init_subcat = "Police Protection"
init_state_subcats = df_exp[df_exp["Category"] == "Public Safety"][
    "Description"
].unique()


def get_col(col_name, year):
    """ Helps select column from df_exp and df_rev.  
        returns  'Amount_2017' from input args ('Amount', 2017)
    """
    return "".join([col_name, "_", year])


# State level  TODO combine with local level
def table_yr(dff, year):
    """ renames columns to display selected year in table """
    return dff.rename(
        columns={
            get_col("Amount", year): "Amount",
            get_col("Per Capita", year): "Per Capita",
            get_col("Population", year): "Population",
        }
    )


# Local level  TODO combine with state
def year_filter(dff, year):
    """ renames columns so selected year doesn't have the year extension ie Amount_2017 """
    return dff.rename(
        columns={
            get_col("Amount", year): "Amount",
            get_col("Per Capita", year): "Per Capita",
            get_col("Per Student", year): "Per Student",
        }
    )


#####################  Read Population by State  ##############################


def read_census_pop():
    """ Returns a df of stat population based on census data:
        https://www.census.gov/data/tables/time-series/demo/popest/2010s-state-total.html
    """

    df = pd.read_excel(
        DATA_PATH.joinpath("nst-est2019-01.xlsx"), skiprows=1, header=2, nrows=56
    )
    # remove the regions (states only) and rename state col
    df_state_pop = df.tail(51).reindex()  # states+DC
    df_state_pop = df_state_pop.rename(columns={"Unnamed: 0": "State"})
    ## for some strange reason, the States had a "." at the start
    df_state_pop["State"] = df_state_pop["State"].str.replace(".", "")
    return df_state_pop


df_pop = read_census_pop()


######################    Figures   ###########################################


def make_sunburst(df, path, values, title):
    if len(path) > 2:
        hover = "<b>%{label} </b><br> %{percentRoot:,.1%} </br> %{value:$,.0f} </br>"
    else:
        hover = "<b>%{label} </b><br> %{percentRoot:,.1%} </br> "

    fig = px.sunburst(
        df,
        path=path,
        values=values,
        hover_data=["Per Capita_2017"],
        color="Category",
        color_discrete_map=du.sunburst_colors,
    )
    fig.update_traces(
        go.Sunburst(hovertemplate=hover), insidetextorientation="radial",
    )
    fig.update_layout(
        title_text=title,
        title_x=0.5,
        title_xanchor="center",
        title_yanchor="top",
        margin=go.layout.Margin(b=10, t=30, l=10, r=10),
        clickmode="event+select",
    )

    return fig


def make_choropleth(dff, title, state, year):
    dff = (
        dff.groupby(["ST", "State"])
        .sum()
        .reset_index()
        .sort_values(get_col("Per Capita", year), ascending=False)
    )
    top3 = (
        dff.head(3)
        .astype({get_col("Per Capita", year): "int"})[
            ["ST", get_col("Per Capita", year)]
        ]
        .to_string(index=False, header=False)
        .replace("\n", "<br>")
    )
    bot3 = (
        dff.tail(3)
        .astype({get_col("Per Capita", year): "int"})[
            ["ST", get_col("Per Capita", year)]
        ]
        .to_string(index=False, header=False)
        .replace("\n", "<br>")
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=dff["ST"],  # Spatial coordinates
            z=dff[get_col("Per Capita", year)].astype(int),  # Data to be color-coded
            name="Per Capita",
            text=dff["State"],
            locationmode="USA-states",  # set of locations match entries in `locations`
            colorscale="amp",
            autocolorscale=False,
            colorbar_title="USD",
        )
    )

    # highlights selected state borders
    if state != "USA":
        selected_state = dff[dff.ST == du.state_abbr[state]]
        fig.add_trace(
            go.Choropleth(
                locationmode="USA-states",
                z=selected_state[get_col("Per Capita", year)].astype(int),
                locations=[du.state_abbr[state]],
                colorscale=[[0, "rgba(0, 0, 0, 0)"], [1, "rgba(0, 0, 0, 0)"]],
                marker_line_color="#8f97f8",
                marker_line_width=4,
                showscale=False,
                text=[state],
                hovertemplate="%{z:$,.0f} %{text} <extra></extra>",
            )
        )

    fig.update_traces(go.Choropleth(hovertemplate="%{z:$,.0f} %{text} <extra></extra>"))

    fig.update_layout(
        title_text=title,
        title_x=0.5,
        title_xanchor="center",
        title_yanchor="top",
        title_y=1,
        font=dict(size=14),
        geo_scope="usa",  # limite map scope to USA
        margin=go.layout.Margin(b=75, t=20, l=10, r=10),
        yaxis=go.layout.YAxis(tickprefix="$", fixedrange=True),
        xaxis=go.layout.XAxis(fixedrange=True),
        #  paper_bgcolor="#eeeeee",
        annotations=[
            dict(
                x=1,
                y=0.95,
                showarrow=False,
                text="Top 3: <br>" + top3,
                xref="paper",
                yref="paper",
            ),
            dict(
                x=1,
                y=0.05,
                showarrow=False,
                text="Bottom 3: <br>" + bot3,
                xref="paper",
                yref="paper",
            ),
        ],
    )
    return fig


########### Bar chart
def make_bar_charts(dff, yaxis_col, xaxis_col, default_color="#446e9b", clip="no"):

    color_column = yaxis_col + "_color"
    color = dff[color_column] if color_column in dff else default_color
    range = [] if clip == "no" else [0, clip]
    

    return [
        dcc.Graph(
            # id=y_col + "-bar",
            config={"displayModeBar": False},
            figure={
                "data": [
                    {
                        "x": dff[xaxis_col],
                        "y": dff[yaxis_col],
                        "type": "bar",
                         "hovertemplate": " $%{y:,.0f}<extra></extra>",

                        "marker": {"color": color},
                    }
                ],
                "layout": {
                    "xaxis": {"automargin": True, "tickangle": -40, "fixedrange": True},
                    "yaxis": {
                        "automargin": True,
                       
                        "title": {"text": yaxis_col},
                        "range": range,
                        "fixedrange": True,
                    },
                     'barmode' : 'relative',
                     'hovermode': 'closest',
                    "height": 375,
                    "margin": {"t": 10, "l": 10, "r": 10, "b": 200},
                },
            },
        )
    ]


#####################  figure and data summary div components ################


def make_stats_table(population, dff_exp, selected, year):
    per_capita = dff_exp[get_col("Per Capita", year)].astype(float).sum() / selected
    total_exp = dff_exp[get_col("Amount", year)].astype(float).sum()

    row1 = html.Tr(
        [
            html.Td(
                "{:0,.0f} {}".format(population, "Population"), className="text-center"
            ),
        ]
    )
    row2 = html.Tr(
        [
            html.Td(
                "${:0,.0f} {}".format(per_capita, "Per Capita All Categories"),
                className="text-center",
            ),
        ]
    )
    table_body = [html.Tbody([row2, row1])]

    return dbc.Table(
        table_body,
        bordered=False,
        className="table table-sm table-light",
        style={"font-size": "12px"},
    )


state_sunburst = html.Div(
    [
        dcc.Graph(
            id="sunburst_state",
            figure=make_sunburst(
                df_exp,
                ["USA", "Category"],
                get_col("Amount", START_YR),
                START_YR + " Selected",
            ),
            style={"height": "200px"},
            config={"displayModeBar": False},
        ),
        html.Div(
            id="state_stats",
            children=make_stats_table(
                df_pop[int(START_YR)].astype(float).sum(), df_exp, 51, START_YR
            ),
        ),
    ],
)


USA_sunburst = html.Div(
    [
        dcc.Graph(           
            figure=make_sunburst(
                df_exp,
                ["USA", "Category"],
                get_col("Amount", START_YR),
                START_YR + " USA ",
            ),
            style={"height": "200px"},
            config={"displayModeBar": False},
        ),
        html.Div(          
            children=make_stats_table(
                df_pop[int(START_YR)].astype(float).sum(), df_exp, 51, START_YR
            ),
        ),
    ],
)

mystate_sunburst = html.Div(
    [
        dcc.Graph(
            id="sunburst_mystate",
            figure=make_sunburst(
                df_exp[df_exp["State"] == "Arizona"],
                ["State", "Category"],
                get_col("Amount", START_YR),
                START_YR + " My State",
            ),
            style={"height": "200px"},
            config={"displayModeBar": False},
        ),
        html.Div(
            id="mystate_stats",
            children=make_stats_table(
                int(df_pop.loc[df_pop["State"] == "Arizona", int(START_YR)]),
                df_exp[df_exp["State"] == "Arizona"],
                1,
                START_YR,
            ),
        ),
    ],
)

category_sunburst = html.Div(
    [
        # html.Div(id='sunburst_title', children= START_YR + ' Expentures - All States'),
        dcc.Graph(
            id="sunburst_cat",
            figure=make_sunburst(
                df_exp,
                ["Category", "Description", "State/Local"],
                get_col("Amount", START_YR),
                " ",
            ),
            style={"height": "700px"},
            config={"displayModeBar": False},
        )
    ]
)

map = html.Div(
    [
        dcc.Graph(
            id="map",
            figure=make_choropleth(
                df_exp, str(START_YR) + " Per Capita Expenditures", "Alabama", START_YR,
            ),
            config={
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": [
                    "zoom2d",
                    "hoverCompareCartesian",
                    "hoverClosestCartesian",
                    "toggleSpikelines",
                    "lasso2d",
                    "select2d",
                ],
            },
        )
    ],
    className="mt-2 mb-2",
    style={"height": "370px"},
)

#leaflet map: Create geojson.

geojson = dl.GeoJSON( id="geojson", format="geobuf",
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    cluster=True,  # when true, data are clustered
                    clusterToLayer=dlx.scatter.cluster_to_layer,  # how to draw clusters
                    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
                    options=dict(pointToLayer=dlx.scatter.point_to_layer),  # how to draw points
                    superClusterOptions=dict(radius=150),  # adjust cluster size
                 #   hideout=dict(colorscale=csc_map[default_csc], color_prop=color_prop, **minmax)
                     )



####################### Dash Tables  ##########################################


def make_sparkline(dff, spark_col, spark_yrs):
    """ Makes df column with data formatted for sparkline figure.

    args:
        dff (df)         -dataframe of census data (expenditures or revenue) all years
        spark_col (str) -name of column for sparkline series (ie "Amount" or "Per Capita")
        spark_yrs [str] - years as a list of strings in to be included in sparkline figure
    Returns:
        df    Column of data formatted like: '8534{0,57,46,66,59,100}9226'
              numbers between { } are normalized between 0 and 100
    """

    # select columns for sparkline df
    spark_cols = ["".join([spark_col, "_", str(year)]) for year in spark_yrs]

    for col in spark_cols:
        if col not in dff.columns.tolist():
            dff[col] = 0

    df_spark = dff[spark_cols].copy()

    # normalize between 0 and 100  ( (x-x.min)/ (x.max-x.min)*100
    min = df_spark.min(axis=1)
    max = df_spark.max(axis=1)
    df_spark = (
        df_spark[spark_cols].sub(min, axis="index").div((max - min), axis="index") * 100
    )

    df_spark.fillna(0, inplace=True)

    # putting it all together:
    df_spark["spark"] = df_spark.astype(int).astype(str).agg(",".join, axis=1)
    df_spark["start"] = dff[spark_cols[0]].astype(int).astype(str)
    df_spark["{"] = "{"
    df_spark["}"] = "}"
    df_spark["end"] = dff[spark_cols[-1]].astype(int).astype(str)
    df_spark["sparkline"] = df_spark[["start", "{", "spark", "}", "end"]].agg(
        "".join, axis=1
    )
    return df_spark["sparkline"]


def discrete_background_color_bins(df, n_bins=5, columns="all"):

    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == "all":
        if "id" in df:
            df_numeric_columns = df.select_dtypes("number").drop(["id"], axis=1)
        else:
            df_numeric_columns = df.select_dtypes("number")
    else:
        df_numeric_columns = df[columns]

    # removes outliers
    x = df_numeric_columns.copy()
    x = x[x < x.quantile(0.99)]

    df_max = x.max().max()
    df_min = x.min().min()

    ranges = [((df_max - df_min) * i) + df_min for i in bounds]

    styles = []
    legend = []
    colors = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]["seq"]["Blues"][i - 1]
        color = "white" if i > len(bounds) / 2.0 else "inherit"
        colors.append(backgroundColor)
        for column in df_numeric_columns:
            styles.append(
                {
                    "if": {
                        "filter_query": (
                            "{{{column}}} >= {min_bound}"
                            + (
                                " && {{{column}}} < {max_bound}"
                                if (i < len(bounds) - 1)
                                else ""
                            )
                        ).format(
                            column=column, min_bound=min_bound, max_bound=max_bound
                        ),
                        "column_id": column,
                    },
                    "backgroundColor": backgroundColor,
                    "color": color,
                }
            )
        legend.append(
            html.Div(
                style={"display": "inline-block", "width": "60px", "float": "right"},
                children=[
                    html.Div(
                        style={
                            "backgroundColor": backgroundColor,
                            "borderLeft": "1px rgb(50, 50, 50) solid",
                            "height": "10px",
                        }
                    ),
                    html.Small(round(min_bound, 0), style={"paddingLeft": "2px"}),
                ],
            )
        )

    for column in df_numeric_columns:
        try:
            dff = df_numeric_columns[column].copy()
            df_numeric_columns.loc[:, column + "_color"] = pd.cut(
                dff, bins=ranges, labels=colors, duplicates="drop"
            )
        except:
            return [], [], pd.DataFrame(), 0

    return (
        styles,
        html.Div(legend, style={"padding": "5px 0 5px 0"}),
        df_numeric_columns.filter(like="_color"),
        df_max,
    )


# State table
def make_table(dff):

    dff = dff.groupby(["State"]).sum().reset_index()
    dff["sparkline"] = make_sparkline(dff, "Per Capita", YEARS)
    dff = table_yr(dff, START_YR)

    return html.Div(
        [
            dash_table.DataTable(
                id="table",
                columns=[
                    {"id": "State", "name": [" ", "State"], "type": "text"},
                    {"id": "Category", "name": [" ", "Category"], "type": "text"},
                    {
                        "id": "Description",
                        "name": [" ", "Sub Category"],
                        "type": "text",
                    },
                    #   {"id": "State/Local", "name": [' ', "State or Local" ] , "type": "text"},
                    {
                        "id": "Amount",
                        "name": [" ", "Total Amount",],
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                    {
                        "id": "Per Capita",
                        "name": [" ", "Per Capita"],
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                    {
                        "id": "sparkline",
                        "name": ["Per Capita", "2012-2017"],
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                ],
                merge_duplicate_headers=True,
                data=dff.to_dict("records"),
                # filter_action='native',
                sort_action="native",
                # sort_mode="multi", default is "single"
                export_format="xlsx",
                export_headers="display",
                is_focused=False,
                cell_selectable=False,
                style_table={
                    "overflowY": "scroll",
                    "border": "thin lightgrey solid",
                    "maxHeight": "425px",
                },
                style_cell={
                    "textAlign": "left",
                    "font-family": "arial",
                    "font-size": "14px",
                },
                style_cell_conditional=[
                    {"if": {"column_id": c}, "textAlign": "right"}
                    for c in ["Per Capita", "Amount"]
                ],
                style_data_conditional=[
                    {
                        "if": {"column_id": "sparkline"},
                        "width": 100,
                        "font-family": "Sparks-Bar-Extrawide",
                        "font-size": "18px",
                        "padding-right": "15px",
                        "padding-left": "15px",
                    },
                ],
            )
        ],
        #  className="mb-2",
    )


#############  Local Table    ################################################


#############  Optional columns to show it the table

city_columns = [
   # {"id": "id", "name": [' ', "id"], "type": "text"},
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

city_datatable = html.Div(
    [
        dash_table.DataTable(
            id="city_table",
            columns=city_columns + percapita_columns,
            merge_duplicate_headers=True,
            # data=init_city_df_exp.to_dict("records"),
            # filter_action='native',
            sort_action="native",
            export_format="xlsx",
            export_headers="display",
            #  row_selectable ='multi',
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


########### buttons, dropdowns, check boxes, sliders  ########################

exp_rev_button_group = dbc.ButtonGroup(
    [
        dbc.Button("Spending", id="expenditures"),
        dbc.Button("Revenue", id="revenue", className="mt-1"),
    ],
    vertical=True,
    className="m-1 btn-sm btn-block",
)

state_local_button_group = dbc.ButtonGroup(
    [
        dbc.Button("State Govts", id="state_button"),
        dbc.Button("Local Govts", id="local_button", className="ml-1"),
    ],
    # vertical=True,
    className="m-1 mt-3 btn-sm btn-block",
)

all_states_button = html.Div(
    [
        dbc.Button(
            "Show all States",
            id="all_states",
            n_clicks=0,
            color="info",
            #  outline=True,
            className="btn-lg",
        )
    ],
    #  className="mb-5",
)


year_slider = html.Div(
    [
        #  html.Div('Select Year:', style={'font-weight':'bold'}),
        dcc.Slider(
            id="year",
            min=int(min(YEARS)),
            max=int(max(YEARS)),
            step=1,
            # marks={int(year) : year for year in YEARS },
            marks={
                int(year): {"label": year, "style": {"writing-mode": "vertical-rl"}}
                for year in YEARS
            },
            value=int(START_YR),
            included=False,
            className="mt-3  px-4 mb-5",
        )
    ]
)


state_dropdown = html.Div(
    [
        html.Div("Select State or All:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="state",
            options=[{"label": "All States", "value": "USA"}]
            + [{"label": state, "value": state} for state in df_pop["State"]],
            value="USA",
            clearable=False,
            className="mt-2",
        ),
    ],
    className="px-2",
)

mystate_dropdown = html.Div(
    [
        dcc.Dropdown(
            id="mystate",
            options=[{"label": state, "value": state} for state in df_pop["State"]],
            value="Arizona",
            clearable=False,
        )
    ],
    className="mt-3",
)

category_dropdown = html.Div(
    [
        html.Div("Select a Category:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="category_dropdown",
            options=[{"label": "All Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in df_exp["Category"].unique()],
            #  placeholder="Select a category",
            value="Public Safety",
        ),
    ],
    className="px-2 mt-3",
)

sub_category_dropdown = html.Div(
    [
        html.Div("Select a Sub Category:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="subcategory_dropdown",
            options=[{"label": "All Sub Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in init_state_subcats],
            # placeholder="Select a sub category",
            style={"font-size": "90%"},
            value="Police Protection",
        ),
    ],
    className="px-2 mt-3",
)

state_local_dropdown = html.Div(
    [
        html.Div("Select state/local:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="state_local_dropdown",
            options=[{"label": "Both State & Local", "value": "all"}]
            + [
                {"label": "State", "value": "State"},
                {"label": "Local", "value": "Local"},
            ],
            #  placeholder="Select State or Local",
        ),
    ],
    className="px-2 mt-3",
    style={"display": "none"},
)


#############   Local only buttons

type_dropdown = html.Div(
    [
        html.Div(
            "Select a Type: ie city, county gov, school district...", style={"font-weight": "bold"}
        ),
        dcc.Dropdown(
            id="city_type",
            options=[
                {"label": "All local government types", "value": "all"},
                {"label": "County Govts", "value": "1"},
                {"label": "Cities and Towns", "value": "c"},
                {"label": "Cities only", "value": "2"},
                {"label": "Towns only", "value": "3"},
                {"label": "School Districts", "value": "5"},
                {"label": "Special Districts", "value": "4"},
            ],
            value="c",
        ),
    ],
    className="px-2 mt-3",
)

county_dropdown = html.Div(
    [
        html.Div("Select a County:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="city_county_dropdown",
            options=[{"label": "All Counties", "value": "all"}]
            + [
                {"label": c, "value": c}
                for c in init_city_df_exp["County name"].dropna().unique()
            ],
             placeholder="Enter a name",
        ),
    ],
    className="px-2",
)

city_dropdown = html.Div(
    [
        html.Div("Select a Name:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="city_name_dropdown",
            options=[{"label": "All ", "value": "all"}]
            + [
                {"label": c, "value": c}
                for c in init_city_df_exp["ID name"].dropna().unique()
            ],
            placeholder="Enter a name",
        ),
    ],
    className="px-2",
)

clear_button = html.Div(
    [
        dbc.Button(
            "Clear selections",
            id="clear",
            n_clicks=0,
            color="light",
            className="mt-1 btn-sm",
        )
    ]
)

collapse = html.Div(
    [
        dbc.Button(id="collapse-button", style={"display": "none"}),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(
                    "To see data, try clearing some selections",
                    className="border border-warning font-weight-bold text-warning",
                )
            ),
            id="collapse",
        ),
    ],
    style={"width": "400px"},
)

#############   Tabs




tabs = html.Div(
    dbc.Tabs(
        [
            dbc.Tab(
                [
                    #html.Div( dl.Map([dl.TileLayer(url="https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png"), geojson]),
                    #          style={'height':'370px',"position": "relative"}),
                    
                    map,
                    make_table(df_exp),
                    all_states_button,
                    html.Div(id="bar_charts_container"),
                ],
                 tab_id="state_table_tab",
              #  label="States",
                labelClassName="d-none",
            ),
            dbc.Tab(
                [                    
                    html.H3(id="city_title", className="bg-white text-center border"),
                    html.Div( dl.Map([dl.TileLayer(url="https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png"), geojson]),
                              style={'height':'370px',"position": "relative"}),

                    html.Div(id="city_legend"),
                    city_datatable,
                    collapse,
                    html.Div(id="city_bar_charts_container"),
                ],
                tab_id="city_table_tab",
                labelClassName="d-none",
            ),
        ],
        id="tabs",
        active_tab="state_table_tab",
    ),
    style={"minHeight": "800px"},
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



intro = html.Div(
    dcc.Markdown(
        """
        This data is from the US Census. [link]  The most current
        data is from 2017, but it's a good starting place to learn
        more about state and local government finances.  
        
        Here you can see n overveiw of the broad spending categories and compare 
        differences  between states.  
        
        Select the "Local Govts" button to see local governments such as city, county, 
        school districts and special districts
                                        
        """
    )
)


########################    Layout     ###########################

layout = dbc.Container(
    [
        html.Div(navbar),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(first_card, width=12),
                        # dbc.Col(
                        #  second_card, width=6),
                    ],
                    className="m-5",
                )
            ]
        ),
        #####################   main dashboard layout #########################
        dcc.Store(id="store_exp_or_rev", data="Expenditures"),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(  # controls
                            [
                                html.Div(
                                    [
                                        exp_rev_button_group,
                                        year_slider,
                                        state_dropdown,
                                        category_dropdown,
                                        sub_category_dropdown,
                                        state_local_dropdown,
                                        state_local_button_group,
                                    ],
                                    className=" mb-1 border bg-white",
                                    style={"height": "525px"},
                                ),
                                html.Div(
                                    [county_dropdown, type_dropdown, city_dropdown,],
                                    className="mt-2, pb-4 bg-white",
                                    style={"display": "none"},
                                    id="city_controls",
                                ),
                                html.Div(clear_button, className="ml-1",),
                            ],
                            width={"size": 2, "order": 1},
                            className="mt-5 pt-4 ",
                        ),
                        dbc.Col(  # map and table stacked
                            [html.Div(tabs)],
                            width={"size": 8, "order": 2},
                            className="bg-white mt-3 mb-3",
                        ),

                        dbc.Col(  # stacked sunbursts
                            html.Div(
                                [mystate_dropdown, mystate_sunburst, state_sunburst, USA_sunburst],
                            ),
                            width={"size": 2, "order": "last"},
                            className="bg-primary",
                        ),
                    ],
                    className="bg-primary",
                ),
            ]
        ),
        # html.Div( dl.Map([dl.TileLayer(), geojson], zoom=6, center=(33.5, -86.8))
        #           ,style={'height':'370px',"position": "relative"}),



        ########################  large sunburst  ######################
        dbc.Row(
            [
                dbc.Col(  # large sunburst
                    category_sunburst,
                    width={"size": 8, "offset": 2, "order": "last"},
                    className="border ",
                )
            ],
            className="bg-white mt-5",
        ),

        ###########################   footer #########################
        html.Div(  # footer
            [dbc.Row(dbc.Col(html.Div(footer, className="border-top mt-5"))),]
        ),
    ],
    fluid=True,
)


#######################    Callbacks     #############################

###### Update control panel  ########################################

####### update revenue or expenses
@app.callback(
    [
        Output("store_exp_or_rev", "data"),
        Output("category_dropdown", "options"),
        Output("category_dropdown", "value"),
        Output("state_local_dropdown", "value"),
        Output("city_name_dropdown", "value"),
        Output("city_county_dropdown", "value"),
        Output("city_type", "value"),
    ],
    [
        Input("expenditures", "n_clicks"),
        Input("revenue", "n_clicks"),
        Input("clear", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def update_exp_or_rev(exp, rev, clear_click):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # better ui for local if it defaults to city (type 3)?
    if clear_click and (input_id == "clear"):
        return dash.no_update, dash.no_update, None, None, None, None, "2"

    dff = df_rev if input_id == "revenue" else df_exp

    options = [{"label": "All Categories", "value": "all"}] + [
        {"label": c, "value": c} for c in dff["Category"].unique()
    ]

    return (
        "Revenue" if input_id == "revenue" else "Expenditures",
        options,
        None,
        None,
        None,
        None,
        "2",
    )


#####  update state dropdown
@app.callback(
    [Output("state", "value"), Output("city_table", "page_current"),],
    [
        Input("map", "clickData"),
        Input("clear", "n_clicks"),
        Input("tabs", "active_tab"),
        Input("all_states", "n_clicks"),
        Input("category_dropdown", "value"),
        Input("subcategory_dropdown", "value"),
        Input("city_county_dropdown", "value"),
        Input("city_type", "value"),
        Input("city_name_dropdown", "value"),
    ],
    [State("state", "value")],
)
def update_state_dropdown(
    clickData, clear_click, at, all_states, _, __, ___, _x, __x, state
    ):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == "clear":
        state = "USA" if at in ["state_table_tab", "state_bar_tab"] else "Alabama"
    if (
        (input_id == "tabs")
        and (state == "USA")
        and (at in ["city_table_tab", "city_bar_tab"])
    ):
        state = "Alabama"
    if input_id == "all_states":
        state = "USA"

    if input_id == "map":
        if clickData is None:
            raise PreventUpdate
        else:
            click_state = clickData["points"][0]["location"]
            state = du.abbr_state[click_state]

    return state, 0


##### updates sub category dropdown
@app.callback(
    [
        Output("subcategory_dropdown", "options"),
        Output("subcategory_dropdown", "value"),
    ],
    [
        Input("category_dropdown", "value"),
        Input("store_exp_or_rev", "data"),
        Input("clear", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def update_sub_category_dropdown(cat, exp_or_rev, clear_click):

    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    if (cat is None) or (cat == "all"):

        options = [{"label": "All Sub Categories", "value": "all"}] + [
            {"label": s, "value": s}
            for s in dff["Description"].sort_values().dropna().unique()
        ]
    else:
        subcats = dff[dff["Category"] == cat]
        options = [{"label": "All Sub Categories", "value": "all"}] + [
            {"label": s, "value": s}
            for s in subcats["Description"].sort_values().dropna().unique()
        ]

    return options, None


#######  Local only updates:

####### Update counties when state changes
@app.callback([Output("city_county_dropdown", "options"),], [Input("state", "value")])
def update_counties(state):

    if state == "USA":
        state = "Alabama"
    options = [{"label": "All Counties", "value": "all"}] + [
        {"label": c, "value": c}
        for c in exp[du.state_abbr[state]]["County name"]
        .sort_values()
        .dropna()
        .unique()
    ]

    return [options]


####### Update city names when county and type changes
@app.callback(
    Output("city_name_dropdown", "options"),
    [
        Input("state", "value"),
        Input("city_county_dropdown", "value"),
        Input("city_type", "value"),
    ],
)
def update_counties(
    state, county, type,
):

    if state == "USA":
        state = "Alabama"

    dff = exp[du.state_abbr[state]].copy()

    if type and (type != "all"):
        if type == 'c':           
            dff = dff[dff["Gov Type"].str.contains('2', na=False) | dff["Gov Type"].str.contains('3', na=False)]
        else:
            dff = dff[dff["Gov Type"].str.contains(type, na=False)]
    if county and (county != "all"):
        dff = dff[dff["County name"] == county]

    return [{"label": "All Cities", "value": "all"}] + [
        {"label": name, "value": name}
        for name in dff["ID name"].sort_values().dropna().unique()
    ]


#######  Update Sunburst Figures  #############################################


#### updates State overview sunburst and stats.
@app.callback(
    [Output("sunburst_state", "figure"), Output("state_stats", "children")],
    [
        Input("state", "value"),
        Input("year", "value"),
        Input("store_exp_or_rev", "data"),
    ],
    prevent_initial_call=True,
)
def update_selected_state(selected_state, year, exp_or_rev):

    year = str(year)
    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    if selected_state == "USA":
        path = ["USA", "Category"]
        population = df_pop[int(year)].astype(float).sum()
        title = year + " Selected: USA"
        selected = 51  # TODO allow for multiple selected states
    else:
        dff = dff[dff["State"] == selected_state]
        path = ["State", "Category"]
        population = int(df_pop.loc[df_pop["State"] == selected_state, int(year)])
        title = year + " Selected State"
        selected = 1

    return (
        make_sunburst(dff, path, get_col("Amount", year), title),
        make_stats_table(population, dff, selected, year),
    )


#### updates my state overview sunburst and stats.
@app.callback(
    [Output("sunburst_mystate", "figure"), Output("mystate_stats", "children")],
    [
        Input("mystate", "value"),
        Input("year", "value"),
        Input("store_exp_or_rev", "data"),
    ],
    prevent_initial_call=True,
)
def update_mystate(mystate, year, exp_or_rev):
    year = str(year)

    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    selected = 1  # TODO allow for multiple selected states
    dff = dff[dff["State"] == mystate]
    population = int(df_pop.loc[df_pop["State"] == mystate, int(year)])
    title = year + " My State"

    return (
        make_sunburst(dff, ["State", "Category"], get_col("Amount", year), title),
        make_stats_table(population, dff, selected, year),
    )


######  Switch Tabs, hide/show local controls  updateyear#######################
@app.callback(
    [
        Output("city_controls", "style"),
        Output("year", "min"),
        Output("tabs", "active_tab"),
    ],
    [Input("state_button", "n_clicks"), Input("local_button", "n_clicks")],
)
def switch_tab(state, local):
    # note - switching tabs also updates state in diff callback

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == "local_button":
        return {"display": "block"}, int(min(CITY_YEARS)), "city_table_tab"
    else:
        return {"display": "none"}, int(min(YEARS)), "state_table_tab"


#######  update State map and table  ##################################################\
@app.callback(
    [
        Output("map", "figure"),
        Output("table", "data"),
        Output("sunburst_cat", "figure"),
        Output("bar_charts_container", "children"),
        Output("all_states", "className"),
    ],
    [
        Input("store_exp_or_rev", "modified_timestamp"),
        Input("year", "value"),
        Input("state", "value"),
        Input("category_dropdown", "value"),
        Input("subcategory_dropdown", "value"),
        Input("state_local_dropdown", "value"),
        Input("table", "derived_viewport_data"),
    ],
    [State("store_exp_or_rev", "data")],
    #  prevent_initial_call=True,
)
def update_map(
    __, year, state, cat, subcat, local, viewport, exp_or_rev,
):

    dff_map = df_rev if exp_or_rev == "Revenue" else df_exp
    dff_table = dff_sunburst = dff_map.copy()
    title = " ".join([str(year), exp_or_rev, "Per Capita by State"])
    map_title = title
    sunburst_title = " ".join(["All States ", str(year), exp_or_rev, "Per Capita "])

    all_state_btn = "d-none"
    # filter
    if state != "USA":
        dff_table = (
            dff_table[dff_table["State"] == state]
            if state
            else dff_table[dff_table["State"] == "Alabama"]
        )
        dff_sunburst = dff_table.copy()
        sunburst_title = " ".join([str(year), exp_or_rev, state])
        all_state_btn = ""

    if cat and (cat != "all"):
        dff_table = dff_table[dff_table["Category"] == cat]
        dff_map = dff_map[dff_map["Category"] == cat]
        map_title = " ".join([title, ": ", cat])

    if subcat and (subcat != "all"):
        dff_table = dff_table[dff_table["Description"] == subcat]
        dff_map = dff_map[dff_map["Description"] == subcat]
        map_title = " ".join([title, ": ", subcat])

    # subtotal
    if local:
        dff_table = (
            dff_table.groupby(["State", "Category", "Description", "State/Local"])
            .sum()
            .reset_index()
        )

    elif subcat:
        dff_table = (
            dff_table.groupby(["State", "Category", "Description"]).sum().reset_index()
        )

    elif cat:
        dff_table = dff_table.groupby(["State", "Category"]).sum().reset_index()

    else:
        dff_table = dff_table.groupby(["State"]).sum().reset_index()

    dff_table["sparkline"] = make_sparkline(dff_table, "Per Capita", YEARS)
    dff_table = table_yr(dff_table, str(year))

    # update sunburst
    figure = make_sunburst(
        dff_sunburst,
        ["Category", "Description", "State/Local"],
        get_col("Amount", str(year)),
        sunburst_title,
    )

    bar_charts = []
    if (len(dff_table['State'].unique()) > 1):
         bar_charts = make_bar_charts(pd.DataFrame(viewport), "Per Capita", "State")



    if dff_map.empty:
        return [], [], [], [], all_state_btn

    return (
        make_choropleth(dff_map, map_title, state, str(year)),
        dff_table.to_dict("records"),
        figure,
        bar_charts,
        all_state_btn,
    )


#####################################   UPDATE LOCAL  #####################################


#####  Update city table
@app.callback(
    [
        Output("city_table", "data"),
        Output("city_table", "columns"),
        Output("city_title", "children"),
        Output("collapse", "is_open"),

    ],
    [
        Input("store_exp_or_rev", "data"),
        Input("year", "value"),
        Input("category_dropdown", "value"),
        Input("subcategory_dropdown", "value"),
        Input("state", "value"),
        Input("city_type", "value"),
        Input("city_county_dropdown", "value"),
        Input("city_name_dropdown", "value"),
    ],
    # prevent_initial_call=True,
)
def update_city_table(exp_or_rev, year, cat, subcat, state, type, county, name):

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if state == "USA":
        state = "Alabama"
    if year < 2014:
        year = 2014

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
        columns = city_columns + perstudent_columns
        df_table["sparkline_Per Student"] = make_sparkline(
            df_table, "Per Student", CITY_YEARS
        )
        df_table = year_filter(df_table, str(year))
        df_table["Enrollment"] = df_table["Amount"] / df_table["Per Student"]
        update_title = " ".join([update_title, du.code_type["5"]])

    # special districts columns
    elif (df_table["Gov Type"] == "4").all():
        columns = city_columns
        df_table = year_filter(df_table, str(year))
        update_title = " ".join([update_title, du.code_type["4"]])
    else:
        # city columns
        columns = city_columns + percapita_columns
        df_table["sparkline_Per Capita"] = make_sparkline(
            df_table, "Per Capita", CITY_YEARS
        )
        df_table = year_filter(df_table, str(year))
        df_table["Population"] = df_table["Amount"] / df_table["Per Capita"]

    return df_table.to_dict("records"), columns, update_title, False




# update Local styles and bar chart:

@app.callback(
    [
        Output("city_table", "style_data_conditional"),
        Output("city_bar_charts_container", "children"),
        Output("city_legend", "children"),
        Output("geojson", "hideout"),
        Output("geojson", "data"),
    ],
    [
        Input("city_table", "derived_virtual_data"),
        Input("city_table", "derived_viewport_row_ids"),
    ],
    [
        State('city_table', "data")
    ]
)
def update_city_table(data, viewport_ids, data_state):

    dff = pd.DataFrame(data)
    if dff.empty:
        raise PreventUpdate
    else:
        if "Per Capita" in dff:
            color_column = "Per Capita"
        elif "Per Student" in dff:
            color_column = "Per Student"
        else:
            color_column = "Amount"

        (styles, legend, df_color, max_y) = discrete_background_color_bins(
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
            bar_charts = make_bar_charts(dff, color_column, "ID name", clip=max_y)



        # update map
        dff_state = pd.DataFrame(data_state)
        dff_lat_lng = df_lat_lng[df_lat_lng['state_id'] == dff_state['ST'].iat[0]]

        dff_state['name'] = dff_state['ID name'].str[:-4]
        dff_state = pd.merge(dff_state, dff_lat_lng, how='left', left_on=['County name', 'name'],
                            right_on=['county_name', 'city'])
        dff_state = dff_state.dropna()

        dicts = dff_state.to_dict('rows')


        for item in dicts:
            item["tooltip"] = "${:.0f} per capita    {}".format(item[color_column], item['name'])
            item["popup"] = item["name"]  # bind popup
        geojson = dlx.dicts_to_geojson(dicts, lon="lng")  # convert to geojson
        geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf

        colors = colorlover.scales[str(5)]["seq"]["Blues"]
        hideout = dict(colorscale=colors, color_prop=color_column, popup_prop='name', min=0, max=max_y,
                       circle_options= dict(radius = 10))

        #circle_options: {fillOpacity: 1, stroke: false, radius: 5}};

        return styles, bar_charts, legend, hideout, geobuf


if __name__ == "__main__":
    app.run_server(debug=True)
