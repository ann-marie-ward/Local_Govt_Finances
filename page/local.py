import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate


import plotly.graph_objects as go
import plotly.express as px


import dash_bootstrap_components as dbc
import dash_tabulator
import pandas as pd

import pathlib
import pickle

import data_utilities as du
from app import app, navbar, footer

styles = {
    "pre": {"border": "thin lightgrey solid", "overflowX": "scroll",},
}

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 12)


# Update this when new data is added:
# YEARS = [str(year) for year in range(2012, 2018)]
YEARS = ["2014", "2015", "2016", "2017"]
START_YR = "2017"


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
DATA_PREP_PATH = PATH.joinpath("../data_prep_city").resolve()



# Local  Expenditures and Revenue df
def get_df_exp_rev(ST):
    """ loads the df_exp and df_rev files by state and adds Cat and Descr columns"""
    filename = "".join(["exp_rev_", ST, ".pickle"])
    with open(DATA_PATH.joinpath(filename), "rb") as handle:
        df_exp, df_rev = pickle.load(handle)

    df_exp = pd.merge(df_exp, du.df_cat_desc, how="left", on="Line")
    df_rev = pd.merge(df_rev, du.df_cat_desc, how="left", on="Line")
    return df_exp, df_rev



# initialize
init_ST = "AZ"
init_selected_cities = {
    # "48201702100000": "SEATTLE, WA",
    # "38202600300000": "PORTLAND, OR",
    "03201000200000": "TUCSON, AZ",
}

rev = {}
exp = {}
for st in du.abbr_state_noUS:
    exp[st], rev[st] =  get_df_exp_rev(st)

init_df_exp = exp["AZ"]
init_df_rev = rev["AZ"]


#########  Table helper functions #############################################


def get_col(col_name, year):
    """ Helps select column from df_exp and df_rev. Adds year extension 
        returns  for example: 'Amount_2017' from input args ('Amount', 2017)
    """
    return "".join([col_name, "_", year])


def year_filter(dff, year):
    """ renames columns so selected year doesn't have the year extension ie Amount_2017 """
    return dff.rename(
        columns={
            get_col("Amount", year): "Amount",
            get_col("Per Capita", year): "Per Capita",
            get_col("Per Student", year): "Per Student",
        }
    )


def make_sparkline(dff, spark_col, spark_yrs):
    """ Makes df column with data formatted for sparkline figure.

    args:
        dff (df)         -dataframe (expenditures or revenue) all years
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


#######  Tabulator table ############################################


def df_to_data(dff):
    """ creates data for tabulator from a dataframe """

    # makes the index the first column
    dff["id"] = dff.index

    col = dff.pop("id")
    dff.insert(0, col.name, col)
    return dff.to_dict("records")


display_cities_options = {
    "selectable": True,
    "maxHeight": "600px",
    #  "initialSort": [{"column": "Amount", "dir": "dsc"}],
    #  "layout":"fitColumns "}
    #   "groupBy": "ST"
    #   "layout":"fitDataFill"
    #   "layout":"fitColumns "
}

downloadButtonType = {"css": "btn btn-primary btn-sm", "text": "Export", "type": "xlsx"}

##########  Tabulator columns
city_columns = [
    {
        "formatter": "rowSelection",
        "hozAlign": "center",
        "headerSort": True,
        "width": 20,
        "cellClick": "function(e, cell){ cell.getRow().toggleSelect();}",
    },
    {
        "title": "County",
        "field": "County name",
        "hozAlign": "left",
        "headerFilter": True,
    },
    {
        "title": "City/District",
        "field": "ID name",
        "hozAlign": "left",
        "headerFilter": True,
    },
    {
        "title": "Category",
        "field": "Category",
        "hozAlign": "left",
        "headerFilter": True,
    },
    {
        "title": "Sub Category",
        "field": "Description",
        "hozAlign": "left",
        "headerFilter": True,
    },
    {
        "title": "Amount",
        "field": "Amount",
        "hozAlign": "right",
        "formatter": "money",
        "formatterParams": {"precision": 0},
        # "headerFilter":True
        # "topCalc":"sum",  "topCalcParams":{"precision":0}
    },
]


percapita_columns = [
    {
        "title": "Population",
        "field": "Population",
        "hozAlign": "right",
        "formatter": "money",
        "formatterParams": {"precision": 0},
        # "headerFilter":True
    },
    {
        "title": "Per Capita",
        "field": "Per Capita",
        "hozAlign": "right",
        "formatter": "money",
        "formatterParams": {"precision": 0},
    },
    {
        "title": "Per Capita 2014-2017",
        "field": "sparkline_Per Capita",
        "hozAlign": "left",
        "cssClass": "bar-extrawide",
    },
]

perstudent_columns = [
    {
        "title": "School Enrollment",
        "field": "Enrollment",
        "hozAlign": "right",
        "formatter": "money",
        "formatterParams": {"precision": 0},
        # "topCalc":"sum",  "topCalcParams":{"precision":0}
    },
    {
        "title": "Per Student",
        "field": "Per Student",
        "hozAlign": "right",
        "formatter": "money",
        "formatterParams": {"precision": 0},
    },
    {
        "title": "Per Student 2014-2017",
        "field": "sparkline_Per Student",
        "hozAlign": "left",
        "cssClass": "bar-extrawide",
    },
]

city_tabulator = (
    dash_tabulator.DashTabulator(
        id="city_table",
        columns=city_columns + percapita_columns,
        data=[],
        options=display_cities_options,
        downloadButtonType=downloadButtonType,
    ),
)


##############  City Cards (sunburst + stats table)   #########################


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
        margin=go.layout.Margin(b=10, t=10, l=1, r=1),       
        clickmode="event+select",
    )
    return fig


def make_stats_table(dff, clicked_on):
    row1 = []
    row2 = []
    per_capita = dff["Per Capita"].astype(float).sum()
    per_student = dff["Per Student"].astype(float).sum()
    total_amt = dff["Amount"].astype(float).sum() * 1000
    if clicked_on is None:
        clicked_on = ""

    if per_capita > 0:
        population = total_amt / per_capita
        row1 = html.Tr(
            [
                html.Td("{:0,.0f} Population".format(population), 
                        style={"text-align": "center"}),              
            ]
        )
        row2 = html.Tr(
            [
                html.Td("${:0,.0f} Per Capita {}".format(per_capita, clicked_on),
                       style={"text-align": "center"}),
            
            ]
        )
    elif per_student > 0:
        enrollment = total_amt / per_student
        row1 = html.Tr(
            [
                html.Td("{:0,.0f} School Enrollment".format(enrollment), 
                        style={"text-align": "center"}),
              
            ]
        )
        row2 = html.Tr(
            [
                html.Td("${:0,.0f} Per Student {}".format(per_student, clicked_on), 
                        style={"text-align": "center"}),
               
            ]
        )
    else:
        row2 = html.Tr(
            [
                html.Td("${:0,.0f} Total Amount {}".format(total_amt, clicked_on),
                       style={"text-align": "center"}),               
            ]
        )
    table_body = [html.Tbody([row2, row1])]

    return dbc.Table(
        table_body,
        bordered=False,
        className="table table-sm table-light",
        style={"font-size": "12px"},
    )




########### buttons, dropdowns, check boxes, sliders  #########################


state_dropdown = html.Div(
    [
        html.Div("Select State:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="city_state",
            options=[
                {"label": state, "value": abbr} for state, abbr in du.states_only.items()
            ],
            value="AZ",
            clearable=False,            
        ),
    ],
    className="px-2 mt-3",
)

type_dropdown = html.Div(
    [
        html.Div("Select Local Government Type:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="city_type",
            options=[
                {"label": "County", "value": "county"},
                {"label": "City", "value": "city"},
                {"label": "School District", "value": "school"},
                {"label": "Special District", "value": "special"},
            ],
            value="city",
            clearable=False,            
        ),
    ],
    className="px-2 mt-3",
)

selected_rows = html.Div(
    [
        html.Div(
            "To add a figure, select a row from the table",
            style={"font-weight": "bold"},
        ),
        html.Div(
            [
                dcc.Dropdown(
                    id="selected_cities_dropdown",
                    placeholder="Select cities from the table",
                    options=[
                        {"label": name, "value": code}
                        for code, name in init_selected_cities.items()
                    ],
                    value=list(init_selected_cities),
                    multi=True,
                ),
            ],
            className="overflow-auto",
            style={"height": "300px"},
        ),
    ],
    className="px-2 mt-5 border",
)


exp_rev_button_group = html.Div(
    [
        dbc.ButtonGroup(
            [
                dbc.Button("Expenditures", id="city_expenditures"),
                dbc.Button("Revenue", id="city_revenue"),
            ],
            vertical=True,
            className="m-1 btn-sm btn-block",
        )
    ]
)

year_slider = html.Div(
    [
        dcc.Slider(
            id="city_year",
            min=int(min(YEARS)),
            max=int(max(YEARS)),
            step=1,
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

category_dropdown = html.Div(
    [
        html.Div("Select a Category:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="city_category_dropdown",
            options=[{"label": "All Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in init_df_exp["Category"].unique()],
            placeholder="Select a category",
            #  value="Public Safety",
        ),
    ],
    className="px-2",
)

sub_category_dropdown = html.Div(
    [
        html.Div("Select a Sub Category:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="city_subcategory_dropdown",
            options=[{"label": "All Sub Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in init_df_exp["Description"].unique()],
            placeholder="Select a sub category",           
            #  value="Police protection",
        ),
    ],
    className="px-2 mt-3",
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

dashboard_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Card title", className="card-title"),
            #   html.P("This card will introduce the dashboard someday"),
            #   dbc.Button("Go somewhere", color="primary"),
        ]
    )
)

########################   Layout #############################################

layout = dbc.Container(
    [
        html.Div(navbar),
        html.Div(
            [
                dcc.Store(id="store_selected_cities", data=init_selected_cities),
                dcc.Store(id="store_city_exp_or_rev"),
                dcc.Store(id="store_clicked_on", data=None),
            ]
        ),
        html.Div([dbc.Row([dbc.Col(first_card, width=12),], className="m-5",)]),
        html.Div(
            [
                ##################### city cards ###################################
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(  # controls
                                    html.Div(
                                        [exp_rev_button_group]
                                        + [state_dropdown]
                                        + [type_dropdown]
                                        + [year_slider],
                                        className="mt-1, ml-1 bg-white border",
                                    ),
                                    width={"size": 2, "order": 1},
                                    className="mt-2 mb-5",
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H2(
                                                id="city_cards_title",
                                                children=[],
                                                className="text-white",
                                            ),
                                            html.Div(
                                                id="city_cards_container", children=[],
                                            ),
                                        ]
                                    ),
                                    width={"size": 10, "order": "last"},
                                ),
                            ],
                            className="mt-5",
                        )
                    ]
                ),
                ####################   city table  #########################
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(  # controls
                                    html.Div(
                                        [category_dropdown]
                                        + [sub_category_dropdown]
                                        + [selected_rows],
                                        className=" pt-2 mt=5 ml-1 border bg-white",
                                    ),
                                    width={"size": 2, "order": 1},
                                    className="mt-5 mb-5"
                                ),
                                dbc.Col(
                                    html.Div(
                                        [html.Div(city_tabulator)],                                       
                                    ),
                                    width={"size": 10, "order": 2},
                                    className="mb-5",
                                ),
                            ]
                        ),
                    ]
                ),
            ],
            className="bg-primary",
        ),
        ###########################   footer #########################
        html.Div(  # footer
            [dbc.Row(dbc.Col(html.Div(footer, className="border-top mt-5 small"))),]
        ),
    ],
    fluid=True,
)

#########################  Callbacks ##########################################

##### Update selected cities
@app.callback(
    [
        Output("store_selected_cities", "data"),  # any row ever selected
        Output("selected_cities_dropdown", "options"),  # any row ever selected
        Output("selected_cities_dropdown", "value"),  # current selection
    ],
    [Input("city_table", "rowClicked"),],
    [
        State("store_selected_cities", "data"),
        State("selected_cities_dropdown", "value"),
    ],
)
def update_selected_cities_data(
    tabulator_row, selected_cities_store, selected_cities_val
):
    options = []
    if tabulator_row:
        selected_cities_store[tabulator_row["ID code"]] = tabulator_row["ID name"]

        if selected_cities_val:
            if tabulator_row["ID code"] not in selected_cities_val:
                selected_cities_val.append(tabulator_row["ID code"])
        else:
            selected_cities_val = [tabulator_row["ID code"]]

    if selected_cities_store:
        options = [
            {"label": name, "value": code}
            for code, name in selected_cities_store.items()
        ]
    return selected_cities_store, options, selected_cities_val


######  Update category dropdowns when report changes between rev & exp
@app.callback(
    [
        Output("store_city_exp_or_rev", "data"),
        Output("city_category_dropdown", "options"),
        Output("city_category_dropdown", "value"),
    ],
    [
        Input("city_expenditures", "n_clicks"),
        Input("city_revenue", "n_clicks"),       
    ],
)
def update_exp_or_rev(exp_click, rev_click):

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # update category dropdown options
    categories = du.revenue_cats if input_id == "city_revenue" else du.expenditure_cats
    options = [{"label": "All Categories", "value": "all"}] + [
        {"label": c, "value": c} for c in categories
    ]

    report_type = "Revenue" if input_id == "city_revenue" else "Expenditures"  

    return report_type, options, None


##### updates sub category dropdown
@app.callback(
    [
        Output("city_subcategory_dropdown", "options"),
        Output("city_subcategory_dropdown", "value"),
    ],
    [Input("city_category_dropdown", "value"), Input("store_city_exp_or_rev", "data")],
    prevent_initial_call=True,
)
def update_sub_category_dropdown(cat, exp_or_rev):

    if exp_or_rev == "Expenditures":
        dff = du.df_summary[du.df_summary["Type"] == "E"]
    else:
        dff = du.df_summary[du.df_summary["Type"] == "R"]

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


#####  Update city table
@app.callback(
    [Output("city_table", "data"), Output("city_table", "columns")],
    [
        Input("store_city_exp_or_rev", "data"),
        Input("city_year", "value"),
        Input("city_category_dropdown", "value"),
        Input("city_subcategory_dropdown", "value"),
        Input("store_clicked_on", "data"),
        Input("city_state", "value"),
        Input("city_type", "value"),
        Input("store_selected_cities", "data"),
    ],
)
def update_city_table(
    exp_or_rev, year, cat, subcat, clicked_on, state, type, selected_cities
):
    # filter for type:
    code = (
        ["4"]
        if type == "special"
        else ["5"]
        if type == "school"
        else ["1"]
        if type == "county"
        else ["2", "3"]
    )

    df = rev[state] if exp_or_rev == "Revenue" else exp[state]
    df_table = df[df["Gov Type"].isin(code)].copy()

    # make a df for selected cities that are not in the currently selected state to include in table
    states = [s for s in rev if s != state]
    df_sel_cities = []
    for s in states:
        df = rev[s] if exp_or_rev == "Revenue" else exp[s]
        df_sel_cities.append(df[df["ID code"].isin(selected_cities)])
    if df_sel_cities != []:
        df_sel_cities = pd.concat(df_sel_cities, ignore_index=True)
        df_table = pd.concat([df_sel_cities, df_table], ignore_index=True)

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    categories = list(du.revenue_cats) + list(du.expenditure_cats)
    if input_id == "store_clicked_on" and clicked_on:
        cat = None
        subcat = None
        # category clicked on
        if clicked_on in categories:
            cat = clicked_on
        # if center of chart was clicked on (ie the name) then no cat selected
        elif df_table["ID name"].str.contains(clicked_on).any():
            cat = None
        # subcategory clicked on
        else:
            subcat = clicked_on

    # filter table
    if cat and (cat != "all"):
        df_table = df_table[df_table["Category"] == cat]
    if subcat and (subcat != "all"):
        df_table = df_table[df_table["Description"] == subcat]

    # subtotal table
    main_columns = ["ST", "ID code", "County name", "ID name", "Gov Type"]
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
        return dash.no_update, dash.no_update

    # school district columns
    if (df_table["Gov Type"] == "5").all():
        columns = city_columns + perstudent_columns
        df_table["sparkline_Per Student"] = make_sparkline(
            df_table, "Per Student", YEARS
        )
        df_table = year_filter(df_table, str(year))
        df_table["Enrollment"] = df_table["Amount"] / df_table["Per Student"]

    # special districts columns
    elif (df_table["Gov Type"] == "4").all():
        columns = city_columns
        df_table = year_filter(df_table, str(year))
    else:
        # city columns
        columns = city_columns + percapita_columns
        df_table["sparkline_Per Capita"] = make_sparkline(df_table, "Per Capita", YEARS)
        df_table = year_filter(df_table, str(year))
        df_table["Population"] = df_table["Amount"] / df_table["Per Capita"]

    return df_to_data(df_table), columns


#####  Update city cards
@app.callback(
    [
        Output("city_cards_container", "children"),
        Output("store_clicked_on", "data"),
        Output("city_cards_title", "children"),
    ],
    [
        Input("store_city_exp_or_rev", "data"),
        Input("selected_cities_dropdown", "value"),
        Input("city_year", "value"),
        Input({"type": "sunburst_output", "index": ALL}, "clickData"),
        Input("store_selected_cities", "data"),
        Input("city_state", "value"),
    ],
    [State("store_clicked_on", "data")],
)
def update_city_cards(
    exp_or_rev, selected_cities, year, clickData, city_dict, state, clicked_on
):
    if selected_cities == []:
        return [], [], []

    title = "".join(
        [str(year), " ", exp_or_rev, " for selected cities, counties and districts"]
    )

    df = rev[state] if exp_or_rev == "Revenue" else exp[state]
    df_cards = df[df["ID code"].isin(selected_cities)].copy()

    # make a df for selected cities that are not in the currently selected state to include in figures
    states = [s for s in rev if s != state]
    df_sel_cities = []
    for s in states:
        df = rev[s] if exp_or_rev == "Revenue" else exp[s]
        df_sel_cities.append(df[df["ID code"].isin(selected_cities)])
    if df_sel_cities != []:
        df_sel_cities = pd.concat(df_sel_cities, ignore_index=True)
        df_cards = pd.concat([df_sel_cities, df_cards], ignore_index=True)

    df_cards = year_filter(df_cards, str(year))

    categories = list(du.revenue_cats) + list(du.expenditure_cats)
    path = ["ID name", "Category"]  # default if no click data

    input_id = dash.callback_context.triggered[0]["prop_id"]

    # Reset clicked_on if switch reports
    if "store_city_exp_or_rev" in input_id:
        clicked_on = None

    # Find segment clicked on in sunburst
    if "index" in input_id:
        # input_id has 'ID code' but sunburst_id has 'ID name'
        # this converts the code to the name
        ID_name = city_dict[input_id.split('"')[3]]

        for points in clickData:
            if points:
                # this finds the ID name in the sunburst click_data
                sunburst_id_name = points["points"][0]["id"].split("/")[0]

                if ID_name == sunburst_id_name:
                    clicked_on = points["points"][0]["label"]

    # return to upper level if city name clicked on
    if clicked_on:
        if df_cards["ID name"].isin([clicked_on]).any():
            path = ["ID name", "Category"]  # upper level
            clicked_on = None

        # save clicked_on but don't change figure
        elif df_cards["Description"].isin([clicked_on]).any():
            return dash.no_update, clicked_on, title

        # drill down if upper level clicked on
        else:
            path = ["ID name", "Description"]

    children = []
    for city_code in selected_cities:
        df_city = df_cards[df_cards["ID code"] == city_code]

        # show per capita, per student, or amount depending on the type of govt
        # as defined in 3rd char of city code
        type = city_code[2]
        column = (
            "Amount" if type == "4" else "Per Student" if type == "5" else "Per Capita"
        )
        if clicked_on:
            df_city = df_cards[
                (df_cards["ID code"] == city_code)
                & (df_cards["Category"] == clicked_on)
            ]
        new_element = html.Div(
            style={"width": "25%", "display": "inline-block", "padding": 10},
            children=[
                dcc.Graph(
                    id={"type": "sunburst_output", "index": city_code},
                    style={"height": 225},
                    config={"displayModeBar": False},
                    figure=make_sunburst(df_city, path, df_city[column], "",),
                ),
                html.Div(
                    id={"type": "state_stats", "index": city_code},
                    children=make_stats_table(df_city, clicked_on),
                ),
            ],
        )
        children.append(new_element)
    return children, clicked_on, title


if __name__ == "__main__":
    app.run_server(debug=True)

