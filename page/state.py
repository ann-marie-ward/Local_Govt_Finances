# see this example for correctly sizing map in tab  http://jsfiddle.net/ve2huzxw/52/
# county shape files by fips and leaflet:  https://stackoverflow.com/questions/58152812/how-do-i-map-county-level-data-as-a-heatmap-using-fips-codes-interactively-in


import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly_express as px

import pandas as pd
import pathlib
import pickle


from app import app, navbar, footer
import data_utilities as du
import control_panel as cp
import local


pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 10)

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()

with open(DATA_PATH.joinpath("df_exp.pickle"), "rb") as handle:
    df_exp = pickle.load(handle)

with open(DATA_PATH.joinpath("df_rev.pickle"), "rb") as handle:
    df_rev = pickle.load(handle)


############  This init section is is both state.py and local.py

# State level
def table_yr(dff, year):
    """ renames columns to display selected year in table """
    return dff.rename(
        columns={
            du.get_col("Amount", year): "Amount",
            du.get_col("Per Capita", year): "Per Capita",
            du.get_col("Population", year): "Population",
        }
    )


#####################  Read Population by State  ##############################


def read_census_pop():
    """Returns a df of stat population based on census data:
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
        go.Sunburst(hovertemplate=hover),
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
        dff.groupby(["ST", "State"])
        .sum()
        .reset_index()
        .sort_values(du.get_col("Per Capita", year), ascending=False)
    )
    top3 = (
        dff.head(3)
        .astype({du.get_col("Per Capita", year): "int"})[
            ["ST", du.get_col("Per Capita", year)]
        ]
        .to_string(index=False, header=False)
        .replace("\n", "<br>")
    )
    bot3 = (
        dff.tail(3)
        .astype({du.get_col("Per Capita", year): "int"})[
            ["ST", du.get_col("Per Capita", year)]
        ]
        .to_string(index=False, header=False)
        .replace("\n", "<br>")
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=dff["ST"],  # Spatial coordinates
            z=dff[du.get_col("Per Capita", year)].astype(int),  # Data to be color-coded
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
                z=selected_state[du.get_col("Per Capita", year)].astype(int),
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


#####################  figure and data summary div components ################


choropleth_map = html.Div(
    [
        dcc.Graph(
            id="map",
            figure=make_choropleth(
                df_exp,
                str(du.START_YR) + " Per Capita Expenditures",
                "Alabama",
                du.START_YR,
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


def make_stats_table(population, dff_exp, selected, year):
    per_capita = dff_exp[du.get_col("Per Capita", year)].astype(float).sum() / selected
    total_exp = dff_exp[du.get_col("Amount", year)].astype(float).sum()

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
                du.get_col("Amount", du.START_YR),
                du.START_YR + " Selected",
            ),
            style={"height": "200px"},
            config={"displayModeBar": False},
        ),
        html.Div(
            id="state_stats",
            children=make_stats_table(
                df_pop[int(du.START_YR)].astype(float).sum(), df_exp, 51, du.START_YR
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
                du.get_col("Amount", du.START_YR),
                du.START_YR + " USA ",
            ),
            style={"height": "200px"},
            config={"displayModeBar": False},
        ),
        html.Div(
            children=make_stats_table(
                df_pop[int(du.START_YR)].astype(float).sum(), df_exp, 51, du.START_YR
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
                du.get_col("Amount", du.START_YR),
                du.START_YR + " My State",
            ),
            style={"height": "200px"},
            config={"displayModeBar": False},
        ),
        html.Div(
            id="mystate_stats",
            children=make_stats_table(
                int(df_pop.loc[df_pop["State"] == "Arizona", int(du.START_YR)]),
                df_exp[df_exp["State"] == "Arizona"],
                1,
                du.START_YR,
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
                du.get_col("Amount", du.START_YR),
                " ",
            ),
            style={"height": "700px"},
            config={"displayModeBar": False},
        )
    ]
)


####################### Dash Tables  ##########################################

# State table
def make_table(dff):
    dff = dff.groupby(["State"]).sum().reset_index()
    dff["sparkline"] = du.make_sparkline(dff, "Per Capita", du.YEARS)
    dff = table_yr(dff, du.START_YR)

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
                        "name": [
                            " ",
                            "Total Amount",
                        ],
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


#############   Tabs

state_tab_content = html.Div(
    [
        choropleth_map,
        make_table(df_exp),
        cp.all_states_button,
        html.Div(id="state_bar_charts_container"),
    ]
)

local_tab_content = html.Div(
    [
        html.H3(id="local_title", className="bg-white text-center border"),
        html.Div(id="local_map", style={"height": "370px"}),
        html.Div(id="local_legend"),
        local.local_datatable,
        cp.warning_msg_collapse,
        html.Div(id="local_bar_charts_container"),
    ]
)

tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(state_tab_content, tab_id="state_tab", labelClassName="d-none"),
                dbc.Tab(local_tab_content, tab_id="local_tab", labelClassName="d-none"),
            ],
            id="tabs",
            active_tab="state_tab",
        ),
    ]
)


#####################   Header Cards and Markdown #############################
first_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("", className="card-title"),
            html.P(""),
        ],
        style={"height": "75px"},
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
        html.Div(dbc.Row(dbc.Col(first_card, width=12), className="m-5")),
        #####################   main dashboard layout #########################
        dcc.Store(id="store_exp_or_rev", data="Expenditures"),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            cp.controls_group,
                            width={"size": 2, "order": 1},
                            className="mt-5 pt-4 ",
                        ),
                        dbc.Col(  # map and table stacked tabs between local and state
                            [html.Div(tabs)],
                            width={"size": 8, "order": 2},
                            className="bg-white mt-3 mb-3",
                        ),
                        dbc.Col(  # stacked sunbursts
                            html.Div(
                                [
                                    cp.mystate_dropdown,
                                    mystate_sunburst,
                                    state_sunburst,
                                    USA_sunburst,
                                ],
                            ),
                            width={"size": 2, "order": "last"},
                            className="bg-primary",
                        ),
                    ],
                    className="bg-primary",
                ),
            ]
        ),
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
        html.Div(id='test1'),
        ###########################   footer #########################
        html.Div(  # footer
            [
                dbc.Row(dbc.Col(html.Div(footer, className="border-top mt-5"))),
            ]
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
        Output("local_name_dropdown", "value"),
        Output("local_county_dropdown", "value"),
        Output("local_type", "value"),
        Output("local_table", "selected_rows"),
    ],
    [
        Input("expenditures", "n_clicks"),
        Input("revenue", "n_clicks"),
        Input("clear", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def update_exp_or_rev1(exp, rev, clear):
    print("here")
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print("revexp", input_id)
    if input_id == "clear":
        return dash.no_update, dash.no_update, None, None, None, None, "c", []

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
        "c",
    )


#####  update state dropdown
@app.callback(
    [
        Output("state", "value"),
        Output("local_table", "page_current"),
    ],
    [
        Input("map", "clickData"),
        Input("clear", "n_clicks"),
        Input("tabs", "active_tab"),
        Input("all_states", "n_clicks"),
        Input("category_dropdown", "value"),
        Input("subcategory_dropdown", "value"),
        Input("local_county_dropdown", "value"),
        Input("local_type", "value"),
        Input("local_name_dropdown", "value"),
    ],
    [State("state", "value")],
)
def update_state_dropdown(
    clickData, clear_click, at, all_states, _, __, ___, _x, __x, state
):

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == "clear":
        state = "USA" if at == "state_tab" else du.INIT_STATE
    if (input_id == "tabs") and (state == "USA") and (at == "local_tab"):
        state = du.INIT_STATE
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
        make_sunburst(dff, path, du.get_col("Amount", year), title),
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
        make_sunburst(dff, ["State", "Category"], du.get_col("Amount", year), title),
        make_stats_table(population, dff, selected, year),
    )


######  Switch Tabs, hide/show local controls  updateyear#######################
@app.callback(
    [
        Output("local_controls", "style"),
        Output("year", "min"),
        Output("tabs", "active_tab"),
    ],
    [Input("state_button", "n_clicks"), Input("local_button", "n_clicks")],
)
def switch_pages(_, __):
    # note - switching tabs also updates state in diff callback

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == "local_button":
        return {"display": "block"}, int(min(du.LOCAL_YEARS)), "local_tab"
    else:
        return {"display": "none"}, int(min(du.YEARS)), "state_tab"


#######  update State map and table  ##################################################\
@app.callback(
    [
        Output("map", "figure"),
        Output("table", "data"),
        Output("sunburst_cat", "figure"),
        Output("state_bar_charts_container", "children"),
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
    __,
    year,
    state,
    cat,
    subcat,
    local,
    viewport,
    exp_or_rev,
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

    dff_table["sparkline"] = du.make_sparkline(dff_table, "Per Capita", du.YEARS)
    dff_table = table_yr(dff_table, str(year))

    # update sunburst
    figure = make_sunburst(
        dff_sunburst,
        ["Category", "Description", "State/Local"],
        du.get_col("Amount", str(year)),
        sunburst_title,
    )

    bar_charts = []
    if len(dff_table["State"].unique()) > 1:
        bar_charts = du.make_bar_charts(pd.DataFrame(viewport), "Per Capita", "State")

    if dff_map.empty:
        return [], [], [], [], all_state_btn

    return (
        make_choropleth(dff_map, map_title, state, str(year)),
        dff_table.to_dict("records"),
        figure,
        bar_charts,
        all_state_btn,
    )
