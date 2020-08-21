import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_table.FormatTemplate as FormatTemplate
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


# Update this when new data is added:
YEARS = [str(year) for year in range(2012, 2018)]
START_YR = "2017"

init_cat = 'Public Safety'
init_subcat = 'Police protection'
init_state_subcats = df_exp[df_exp['Category'] == 'Public Safety']['Description'].unique()



def get_col(col_name, year):
    """ Helps select column from df_exp and df_rev.  
        returns  'Amount_2017' from input args ('Amount', 2017)
    """
    return "".join([col_name, "_", year])


def table_yr(dff, year):
    """ renames columns to display selected year in table """
    return dff.rename(
        columns={
            get_col("Amount", year): "Amount",
            get_col("Per Capita", year): "Per Capita",
            get_col("Population", year): "Population",
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

    fig = px.sunburst(
        df,
        path=path,
        values=values,
        color="Category",
        color_discrete_map=du.sunburst_colors       
    )
    fig.update_traces(
        go.Sunburst(           
            hovertemplate="<b>%{label} </b> $%{value:,.0f}"
        ),
        insidetextorientation="radial",
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
        dff.groupby(["ST"])
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
            text=dff["ST"],
            locationmode="USA-states",  # set of locations match entries in `locations`
            colorscale="amp",
            autocolorscale=False,
            colorbar_title="USD",
        )
    )
    fig.update_traces(go.Choropleth(hovertemplate="%{z:$,.0f} %{text}"))

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
                name="Per Capita",
            )
        )
    fig.update_layout(
        title_text=title,
        title_x=0.5,
        title_xanchor="center",
        title_yanchor="top",
        title_y=1,
        font=dict(size=14),
        geo_scope="usa",  # limite map scope to USA
        margin=go.layout.Margin(b=10, t=20, l=10, r=1),
        yaxis=go.layout.YAxis(tickprefix="$", fixedrange=True),
        xaxis=go.layout.XAxis(fixedrange=True),
        paper_bgcolor="#eeeeee",        
        annotations=[
            dict(
                x=1,
                y=1,
                showarrow=False,
                text="Top 3: <br>" + top3,
                xref="paper",
                yref="paper",
            ),
            dict(
                x=1,
                y=0,
                showarrow=False,
                text="Bottom 3: <br>" + bot3,
                xref="paper",
                yref="paper",
            ),
        ],
    )
    return fig


#####################  figure and data summary div components ################

def make_stats_table(population, dff_exp, selected, year):
    per_capita = dff_exp[get_col("Per Capita", year)].astype(float).sum() / selected
    total_exp = dff_exp[get_col("Amount", year)].astype(float).sum()

    row1 = html.Tr(
        [
            html.Td("{:0,.0f}".format(population), style={"text-align": "right"}),
            html.Td("Population"),
        ]
    )
    row2 = html.Tr(
        [
            html.Td("${:0,.0f}".format(per_capita), style={"text-align": "right"}),
            html.Td("Per Capita"),
        ]
    )
    # row3 = html.Tr([html.Td("${:0,.0f}".format(total_exp)), html.Td("Total")])
    table_body = [html.Tbody([row2, row1])]

    return dbc.Table(
        table_body,
        bordered=False,
        className="table table-sm table-light",
        style={"font-size": "12px"},
    )


usa_sunburst = html.Div(
    [
        html.Div(
            dcc.Graph(
                id="sunburst_usa",
                figure=make_sunburst(
                    df_exp,
                    ["USA", "Category"],
                    get_col("Amount", START_YR),
                    START_YR + " USA",
                ),
                style={"height": "225px"},
                config={"displayModeBar": False},
            )
        ),
        html.Div(
            id="usa_stats",
            children=make_stats_table(
                df_pop[int(START_YR)].astype(float).sum(), df_exp, 51, START_YR
            ),
        ),
    ],
)

state_sunburst = html.Div(
    [
        dcc.Graph(
            id="sunburst_state",
            figure=make_sunburst(
                df_exp[df_exp["State"] == "Alabama"],
                ["State", "Category"],
                get_col("Amount", START_YR),
                START_YR + " by State",
            ),
            style={"height": "225px"},
            config={"displayModeBar": False},
        ),
        html.Div(
            id="state_stats",
            children=make_stats_table(
                int(df_pop.loc[df_pop["State"] == "Alabama", int(START_YR)]),
                df_exp[df_exp["State"] == "Alabama"],
                1,
                START_YR,
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
            style={"height": "225px"},
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
            
        )
    ],
    className="mt-2", style={"height": "425px"},
)


########### Bar chart    #####################################################

def make_bar_charts(dff):
    return   [
            dcc.Graph(
            id=column + '-bar',
            figure={
                'data': [
                    {
                        'x': dff['State'],
                        'y': dff[column],
                        'type': 'bar',
                        # 'marker': {'color': colors},
                    }
                ],
                'layout': {
                    'xaxis': {'automargin': True},
                    'yaxis': {
                        'automargin': True,
                        'title': {'text': column}
                    },
                    'height': 250,
                    'margin': {'t': 10, 'l': 10, 'r': 10},
                },
            },
        )
        for column in ['Amount', 'Per Capita', 'Population'] if column in dff
    ]    
   






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


def make_table(dff):

    dff = dff.groupby(["State"]).sum().reset_index()
    dff["sparkline"] = make_sparkline(dff, "Per Capita", YEARS)
    dff = table_yr(dff, START_YR)

    return html.Div(
        [
            dash_table.DataTable(
                id="table",
                columns=[
                    {"id": "State", "name": [' ', "State"], "type": "text"},
                    {"id": "Category", "name": [' ', "Category" ], "type": "text"},
                    {"id": "Description", "name": [' ', "Sub Category" ], "type": "text"},
                    {"id": "State/Local", "name": [' ', "State or Local" ] , "type": "text"},
                    {
                        "id": "Amount",
                        "name": ['in Thousands $',"Total Amount", ],
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                    {
                        "id": "Per Capita",
                        "name": [' ', "Per Capita"],
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
                sort_mode="multi",
                export_format="xlsx",
                export_headers="display",
                is_focused=False,
                cell_selectable=False,
                style_table={
                    "overflowY": "scroll",
                    "border": "thin lightgrey solid",
                    "maxHeight": "450px",
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
                ]
            )
        ],       
    )


########### buttons, dropdowns, check boxes, sliders  ########################

exp_rev_button_group = dbc.ButtonGroup(
    [
        dbc.Button("Expenditures", id="expenditures"),
        dbc.Button("Revenue", id="revenue"),
    ],      
    vertical=True,
    className="m-1 btn-sm btn-block",
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
            className="mt-3  px-2 mb-5",
        )
    ]
)


state_dropdown = html.Div(
    [
        html.Div('Select State or All:', style={'font-weight':'bold'}),
        dcc.Dropdown(
            id="state",
            options=[{"label": "All States", "value": "USA"}]
            + [{"label": state, "value": state} for state in df_pop["State"]],
            value="USA",
            clearable=False,
            className="mt-2",
        )
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
            placeholder="Select a category",
            value='Public Safety',
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
            placeholder="Select a sub category",
            style={"font-size": "90%"},
            value='Police protection',
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
            placeholder="Select State or Local",
        ),
    ],
    className="px-2 mt-3",
)


clear_button = html.Div(
    [
        dbc.Button('Clear all Filters', id='clear',
                  n_clicks=0, color="light", className="mt-4 btn-sm")
        
    ]
)


#####################   Header Cards and Markdown #############################
first_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Card title", className="card-title"),
            html.P("This card will have content some day"),
            #   dbc.Button("Go somewhere", color="primary"),
        ]
    )
)

second_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Card title", className="card-title"),
            html.P("This card also has some text content and not much else,"),
            dbc.Button("Go somewhere", color="primary"),
        ]
    )
)


intro = html.Div(
    dcc.Markdown(
        """
        This data is from the US Census. [link]  The most current
        data is from 2017, but it's a good starting place to learn
        more about state and local government finances.  Here you can see
        an overveiw of the broad spending categories and compare differences
        between states.  Click on the category in the chart and see the map
        for more details.                                 
        """
    )
)


########################  Main Layout     ###########################

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
                                    [exp_rev_button_group]
                                    + [state_dropdown]
                                    + [year_slider],
                                    className=" mb-5 border bg-white",
                                    style={"height": "375px"},
                                ),
                                html.Div(
                                    [category_dropdown]
                                    + [sub_category_dropdown]
                                    + [state_local_dropdown],
                                    className="mt-3  pt-2 border bg-white",
                                    style={"height": "375px"},
                                ),
                                html.Div(
                                    clear_button,
                                    className="mt=5 ml-1",
                                        )
                            ],
                            width={"size": 2, "order": 1},
                            className="mt-5 ",
                        ),
                        dbc.Col(  # map and table stacked
                            [map] + [make_table(df_exp)],
                            width={"size": 8, "order": 2},
                            className="bg-light mt-3 mb-3",
                        ),
                        dbc.Col(  # stacked sunbursts
                            html.Div(
                                [mystate_dropdown]
                                + [mystate_sunburst]
                                + [state_sunburst]
                                + [usa_sunburst],                              
                            ),
                            width={"size": 2, "order": "last"},
                            className="bg-primary",
                        ),
                    ],
                    className="bg-primary",
                  #  no_gutters=True,

                ),
            ]
        ),
            ########################  bar charts #######################
        html.Div(
            [
                dbc.Row(
                    dbc.Col(html.H5(id="bar_title", className="bg-white text-center"),
                             width={"size": 10, "offset": 2, "order": 2},
                             ),
                    className="bg-primary pt-5 pr-5"
                    ),
                 

                dbc.Row(
                    [
                        dbc.Col(html.Div(id='bar_charts_container'),                            
                                width={"size": 10, "offset": 2, "order": 2},
                             
                        )
                    ], className="bg-primary pr-5 pb-5"                  
                )                    
            ], className="bg-white"
        ),
        ########################  large sunurst  ######################
        dbc.Row(
            [
                dbc.Col(  # large sunburst
                    category_sunburst,
                    width={"size": 8, "offset": 2, "order": "last"},
                    className="border ",
                           
                )
            ],
                className="bg-white m-1",
        ),
        ###########################   footer #########################
        html.Div(  # footer
            [dbc.Row(dbc.Col(html.Div(footer, className="border-top mt-5 small"))),]
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
    ],
    [
        Input("expenditures", "n_clicks"), 
        Input("revenue", "n_clicks"),
        Input('clear', "n_clicks")
    ],
    prevent_initial_call=True,
)
def update_exp_or_rev(exp, rev, clear_click):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if clear_click and (input_id == 'clear'):
        return dash.no_update, dash.no_update, None, None

    dff = df_rev if input_id == "revenue" else df_exp

    options = [{"label": "All Categories", "value": "all"}] + [
        {"label": c, "value": c} for c in dff["Category"].unique()
    ]

    return "Revenue" if input_id == "revenue" else "Expenditures", options, None, None


#####  update state dropdown with map click
@app.callback(Output("state", "value"),               
        [
            Input("map", "clickData"),
            Input('clear', "n_clicks")
        ]
)
def update_state_dropdown(clickData, clear_click):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == 'clear':
        return 'USA'

    if clickData is None:
        raise PreventUpdate
    else:
        click_state = clickData["points"][0]["location"]
        return du.abbr_state[click_state]


##### updates sub category dropdown
@app.callback(
    [
        Output("subcategory_dropdown", "options"),
        Output("subcategory_dropdown", "value"),
    ],
    [Input("category_dropdown", "value"), Input("store_exp_or_rev", "data"), Input('clear', "n_clicks")],
    prevent_initial_call=True,
)
def update_sub_category_dropdown(cat, exp_or_rev, clear_click):

    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    if (cat is None) or (cat == "all"):

        options = [{"label": "All Sub Categories", "value": "all"}] + [
            {"label": s, "value": s} for s in dff["Description"].unique()
        ]
    else:
        subcats = dff[dff["Category"] == cat]
        options = [{"label": "All Sub Categories", "value": "all"}] + [
            {"label": s, "value": s} for s in subcats["Description"].unique()
        ]

    return options, None


#######  Update Sunburst Figures  #############################################


######## updates USA overview sunburst and stats
@app.callback(
    [Output("sunburst_usa", "figure"), Output("usa_stats", "children")],
    [Input("year", "value"), Input("store_exp_or_rev", "data")],
    prevent_initial_call=True,
)
def update_usa(year, exp_or_rev):
    year = str(year)
    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    figure = make_sunburst(
        dff, ["USA", "Category"], get_col("Amount", year), year + " USA"
    )
    stats = make_stats_table(df_pop[int(year)].astype(float).sum(), dff, 51, year)
    return figure, stats


#### updates State overview sunburst and stats.
@app.callback(
    [Output("sunburst_state", "figure"), Output("state_stats", "children")],
    [
        Input("state", "value"),
        Input("year", "value"),
        Input("store_exp_or_rev", "data"),
    ],prevent_initial_call=True,
)
def update_selected_state(selected_state, year, exp_or_rev):

    year = str(year)
    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    if selected_state == "USA":
        selected_state = "Alabama"  # default

    selected = 1  # TODO allow for multiple selected states
    dff = dff[dff["State"] == selected_state]
    population = int(df_pop.loc[df_pop["State"] == selected_state, int(year)])
    title = year + " Selected State"

    return (
        make_sunburst(dff, ["State", "Category"], get_col("Amount", year), title),
        make_stats_table(population, dff, selected, year),
    )


#### updates my state overview sunburst and stats.
@app.callback(
    [Output("sunburst_mystate", "figure"), Output("mystate_stats", "children")],
    [
        Input("mystate", "value"),
        Input("year", "value"),
        Input("store_exp_or_rev", "data"),
    ],prevent_initial_call=True,
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

#@app.callback(
#   Output('table', "style_data_conditional"),
#   [ Input("table", "active_cell")]
#)
#def update_row_color(active):
#    style= style_data_conditional.copy()
#    if active:        
#        style.append(
#                {   "if": {"row_index": active['row']}, 
#                    'backgroundColor': 'rgba(150, 180, 225, 0.2)',
#                    'border': '1px solid blue'
#                },            
#        )
#        return style


#######  update map and table  ##################################################\
@app.callback(
    [
        Output("map", "figure"),
        Output("table", "data"),
        Output("sunburst_cat", "figure"),
        Output("bar_charts_container", "children"),
        Output("bar_title", "children"),
       
    ],
    [
        Input("store_exp_or_rev", "modified_timestamp"),
        Input("year", "value"),
        Input("state", "value"),
        Input("category_dropdown", "value"),
        Input("subcategory_dropdown", "value"),
        Input("state_local_dropdown", "value"),
        Input('table', "derived_viewport_data" )
       
    ],
    [State("store_exp_or_rev", "data")],
  #  prevent_initial_call=True,
)
def update_map(__, year, state, cat, subcat, local, viewport, exp_or_rev, ):

    dff_map = df_rev if exp_or_rev == "Revenue" else df_exp
    dff_table = dff_sunburst = dff_map.copy()
    update_title = " ".join([str(year), exp_or_rev, "Per Capita by State"])
    sunburst_title = " ".join([str(year), exp_or_rev, "Per Capita All States"])

   
    
   

    # filter
    if state != "USA":
        dff_table = (
            dff_table[dff_table["State"] == state]
            if state
            else dff_table[dff_table["State"] == "Alabama"]
        )
        dff_sunburst = dff_table.copy()
        sunburst_title = " ".join([str(year), exp_or_rev, state])

    if cat and (cat != "all"):
        dff_table = dff_table[dff_table["Category"] == cat]
        dff_map = dff_map[dff_map["Category"] == cat]
        update_title = " ".join([str(year), exp_or_rev, cat])

    if subcat and (subcat != "all"):
        dff_table = dff_table[dff_table["Description"] == subcat]
        dff_map = dff_map[dff_map["Description"] == subcat]
        update_title = " ".join([str(year), exp_or_rev, subcat])

    if local and (local != "all"):
        dff_table = dff_table[dff_table["State/Local"] == local]
        dff_map = dff_map[dff_map["State/Local"] == local]
        update_title = " ".join([update_title, "and", local, "gvmt only"])

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

       
    return (
        make_choropleth(dff_map, update_title, state, str(year)),
        dff_table.to_dict("records"),
        figure,
        make_bar_charts(pd.DataFrame(viewport)),
        update_title
    )


if __name__ == "__main__":
    app.run_server(debug=True)
