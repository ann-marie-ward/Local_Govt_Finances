

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
import dash_tabulator
import pandas as pd
import numpy as np
import pathlib
import pickle

from app import app, navbar, footer
import data_utilities as du

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 10)

# Update this when new data is added:
YEARS = [str(year) for year in range(2012, 2018)]
START_YR = "2017"

#########    Read Files #######################################################


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()


with open(DATA_PATH.joinpath("df_exp.pickle"), "rb") as handle:
    df_exp = pickle.load(handle)

with open(DATA_PATH.joinpath("df_rev.pickle"), "rb") as handle:
    df_rev = pickle.load(handle)

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


#########    Table helper functions ###########################################

def get_col(col_name, year):
    """ Helps select column from df_exp and df_rev.  
        returns  'Amount_2017' from input args ('Amount', 2017)
    """
    return "".join([col_name, "_", year])


def year_filter(dff, year):
    """ renames columns to display selected year in table """
    return dff.rename(
        columns={
            get_col("Amount", year): "Amount",
            get_col("Per Capita", year): "Per Capita",
            get_col("Population", year): "Population",
        }
    )

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
    df_spark = df_spark[spark_cols].sub(min, axis="index").div((max-min), axis='index') * 100

    df_spark.fillna(0, inplace=True)

    #putting it all together:
    df_spark["spark"] = df_spark.astype(int).astype(str).agg(",".join, axis=1)
    df_spark["start"] = dff[spark_cols[0]].astype(int).astype(str)
    df_spark["{"] = "{"
    df_spark["}"] = "}"
    df_spark["end"] = dff[spark_cols[-1]].astype(int).astype(str)
    df_spark["sparkline"] = df_spark[["start", "{", "spark", "}", "end"]].agg(
        "".join, axis=1
    )
    return df_spark["sparkline"]




def df_to_data(dff):
    ''' creates data for tabulator from a dataframe '''

    # makes the index the first column 
    dff['id'] = dff.index

    col = dff.pop("id")
    dff.insert(0, col.name, col)   
    return dff.to_dict("records")


#########    Tabulator definitions ###########################################

#options = { "selectable":True, "layout":"fitDataTable", "height":"500px"}
options2 = { "selectable":True,
          "height":"500px", 
           "initialSort":[{"column":"Year", "dir":"dsc"}],
         #  "layout":"fitColumns "
           }
options1 = { "selectable":True,
          "height":"500px", 
       #   "groupBy": "ST"
        #   "layout":"fitDataFill"
      #      "layout":"fitColumns "
          
           }



columns = [ 
    #{"title": 'Year', "field":  'Year',
    # "hozAlign": "left",     
    # "headerFilter":True
    # },

    {"title": 'ST', "field":  'ST',
     "hozAlign": "left",     
     "headerFilter":True
     },   
     {"title": 'State', "field":  'State',
     "hozAlign": "left",     
     "headerFilter":True
     },       
     {"title": 'Category', "field":  'Category',
     "hozAlign": "left",     
     "headerFilter":True
     },
     {"title": 'Sub Category', "field": 'Description',
     "hozAlign": "left",     
     "headerFilter":True
     },
      {"title": 'State/Local', "field": 'State/Local',
     "hozAlign": "left",     
     "headerFilter":True
     },         
     {"title": 'Amount (thousands)', "field":  'Amount',
     "hozAlign": "right", 
     "formatter": "money", "formatterParams":{"precision":0},
    # "headerFilter":True
     },
    {"title": 'Per Capita', "field": 'Per Capita',
     "hozAlign": "right",
     "formatter": "money", "formatterParams":{"precision":0},
    # "topCalc":"sum",  "topCalcParams":{"precision":0}
     },
      {"title": 'Per Capita 2012-2017', "field": 'sparkline',
     "hozAlign": "left",     
     "cssClass" : "bar-extrawide",
     },
]

tabulator = html.Div([
        dash_tabulator.DashTabulator(
                id='tabulator',
                columns=columns,
                data=[],
                options=options2,      
        ),
])


#########   Figures   #########################################################


def make_sunburst(df, path, values, title):
   
    fig = px.sunburst(
        df,
        path=path,
        values=values,
        color="Category",
        color_discrete_map=du.sunburst_colors
        #       hover_data=['Population']
    )
    fig.update_traces(
        go.Sunburst(
            # hovertemplate='<b>%{label} </b> <br>%{customdata[0]}<br> $%{value:,.0f}'
            hovertemplate="<b>%{label} </b> $%{value:,.0f}"
        ),
        insidetextorientation="radial",
    )
    fig.update_layout(
        title_text=title,
        title_x=0.5,
        title_xanchor="center",
        title_yanchor="top",
        #  title_y=0.95,
        margin=go.layout.Margin(b=10, t=30, l=10, r=10),
        # yaxis=go.layout.YAxis(tickprefix="$", fixedrange=True),
        # xaxis=go.layout.XAxis(fixedrange=True),
        # annotations=total_labels,
        # paper_bgcolor="whitesmoke",
        clickmode="event+select",
    )
    return fig


def make_choropleth(dff, title, state, year):
    dff_exp = dff.copy()
    dff_exp = dff_exp.groupby(["ST"]).sum().reset_index()

    fig = go.Figure(
        data=go.Choropleth(
            locations=dff_exp["ST"],  # Spatial coordinates
            z=dff_exp[get_col("Per Capita", year)].astype(
                int
            ),  # Data to be color-coded
            name="Per Capita",
            text=dff_exp["ST"],
            locationmode="USA-states",  # set of locations match entries in `locations`
            colorscale="amp",
            autocolorscale=False,
            colorbar_title="USD",
        )
    )
    fig.update_traces(go.Choropleth(hovertemplate="%{z:$,.0f} %{text}"))

    # highlights selected state borders
    if state != "USA":
        selected_state = dff_exp[dff_exp.ST == du.state_abbr[state]]
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
        margin=go.layout.Margin(b=10, t=20, l=20, r=1),
        yaxis=go.layout.YAxis(tickprefix="$", fixedrange=True),
        xaxis=go.layout.XAxis(fixedrange=True),
        paper_bgcolor="#eeeeee",
    )
    return fig


#########  Figure and stats table div components #############################

def make_stats_table(population, dff_exp, selected, year):
    per_capita = dff_exp[get_col("Per Capita", year)].astype(float).sum() / selected
    total_exp = dff_exp[get_col("Amount", year)].astype(float).sum()

    row1 = html.Tr([html.Td("{:0,.0f}".format(population), style={'text-align':'right'}), html.Td("Population")])
    row2 = html.Tr([html.Td("${:0,.0f}".format(per_capita), style={'text-align':'right'}), html.Td("Per Capita")])
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
            )
        ),
        html.Div(
            id="usa_stats",
            children=make_stats_table(
                df_pop[int(START_YR)].astype(float).sum(), df_exp, 51, START_YR
            ),
        ),
    ],
    className="border",
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
    className="border",
)

mystate_sunburst = html.Div(
    [
        dcc.Graph(
            id="sunburst_mystate",
            figure=make_sunburst(
                df_exp[df_exp["State"] == "Arizona"],
                ["State", "Category"],
                get_col("Amount", START_YR),
                "START_YR My State",
            ),
            style={"height": "225px"},
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
    className="border",
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
            # className='m-3'
        )
    ]
)

map = html.Div(
    [
        dcc.Graph(
            id="map",
            figure=make_choropleth(
                df_exp,
                str(START_YR) + " Per Capita Expenditures",
                "Alabama",
                START_YR,
            ),
            style={"height": "400px"},
        )
    ],
    className="mt-3",
)



#########    buttons, dropdowns, check boxes, sliders  #########################

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
            className="mt-3  p-3 mb-5",
        )
    ]
)


state_dropdown = html.Div(
    [
        # html.Div('Select State or All:', style={'font-weight':'bold'}),
        dcc.Dropdown(
            id="state_dropdown",
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
    className="px-2",
)


table_subtotal = html.Div(
    [
        html.Div("Include:", style={"font-weight": "bold"}),
        dcc.RadioItems(
            id="table_subtotal",
            options=[
                {"label": "State Only", "value": "state"},
                {"label": "Category", "value": "cat"},
                {"label": "Sub Category", "value": "subcat"},
                {"label": "State or Local Govt", "value": "local"},
            ],
            value="state",
            labelStyle={"display": "block"},
            labelClassName="m-2",
            inputClassName="mr-2",
        ),
    ],
    className="pt-4 p-2 border-bottom",
)


#########   Header Cards and Markdown   #######################################
first_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Card title", className="card-title"),
            html.P("This card has some text content, but not much else"),
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


#########     Layout     ######################################################

layout = dbc.Container(
    [
        dbc.Container((navbar), fluid=True),
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
       
        dcc.Store(id="store_exp_or_rev", data="Expenditures"),
        dcc.Store(id="store_state", data="Alabama"),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(  # controls
                            html.Div(
                                [exp_rev_button_group]
                                + [year_slider]
                                + [table_subtotal],
                                className="m-1 border",
                            ),
                            width={"size": 2, "order": 1},
                            className="mt-5 ",
                        ),
                        dbc.Col(  # map and table stacked                         
                            [map] + [tabulator],
                            width={"size": 8, "order": 2},
                            className=" bg-light",
                        ),

                        dbc.Col(  # stacked sunbursts
                            html.Div(
                                [mystate_dropdown]
                                + [mystate_sunburst]
                                + [state_sunburst]
                                + [usa_sunburst],
                                className="m-2 border",
                            ),
                            width={"size": 2, "order": "last"},
                            className="bg-light",
                        ),
                    ]
                ),
                dbc.Row(dbc.Col(state_dropdown, width={"size": 2, "offset": 5})),
                dbc.Row(
                    [
                        dbc.Col(  # large sunburst
                             category_sunburst,
                            width={"size": 8, "offset": 2, "order": "last"},
                            className="borderbg-light",
                        )
                    ]
                ),
                dbc.Row(dbc.Col(html.Div(footer, className="border-top mt-5 small"))),
            ]
        ),
    ],
    fluid=True,
)


#########    Callbacks     ####################################################



##### Update revenue or expenses
@app.callback(
    Output("store_exp_or_rev", "data"),
    [Input("expenditures", "n_clicks"), Input("revenue", "n_clicks")],
)
def update_exp_or_rev(exp, rev):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return "Revenue" if input_id == "revenue" else "Expenditures"




####### updates USA overview sunburst and stats
@app.callback(
    [Output("sunburst_usa", "figure"), Output("usa_stats", "children")],
    [Input("year", "value"), Input("store_exp_or_rev", "data")],
)
def update_usa(year, exp_or_rev):
    year = str(year)
    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    figure = make_sunburst(
        dff, ["USA", "Category"], get_col("Amount", year), year + " USA"
    )
    stats = make_stats_table(df_pop[int(year)].astype(float).sum(), dff, 51, year)
    return figure, stats


#### updates State overview sunburst and stats, and large category sunburst.
@app.callback(
    [
        Output("sunburst_cat", "figure"),
        Output("sunburst_state", "figure"), 
        Output("state_stats", "children")],
    [
        Input("store_state", "data"),
        Input("state_dropdown", "value"),
        Input("year", "value"),
        Input("store_exp_or_rev", "data"),
    ],
)
def update_selected_state(selected_state, state_cat, year, exp_or_rev):    
    year = str(year)
    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

    dff_cat = dff if state_cat == 'USA' else dff[dff["State"] == state_cat]

    if selected_state is None:
        selected_state = "Alabama"  # default

    selected = 1  # TODO allow for multiple selected states
    dff = dff[dff["State"] == selected_state]
    population = int(df_pop.loc[df_pop["State"] == selected_state, int(year)])
   
    title = year + " Selected State"

    # Update sunburst
    sunburst_category_fig = make_sunburst(
        dff_cat,
        ["Category", "Description", "State/Local"],
        get_col("Amount", str(year)),
        year
    )

    return (
        sunburst_category_fig,
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
    ],
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



#######  update map and table  
@app.callback(
    [
        Output("map", "figure"),     
        Output("tabulator", "data"),
        
        Output('store_state', "data")
    ],
    [        
        Input("year", "value"),              
        Input("table_subtotal", "value"),
        Input('tabulator', 'rowClicked'),
        Input("map", "clickData"),
        Input("store_exp_or_rev", "modified_timestamp"),
        Input("store_state", "modified_timestamp"),        

    ],
    [
        State("store_exp_or_rev", "data"),
        State("store_state", "data")
    ],
)
def update_map_table(year, subtotal, row, mapClick, _, __, exp_or_rev, state):   
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
   
    # update selected state
    if triggered_id == 'map':
        click_state = mapClick["points"][0]["location"]
        state =  du.abbr_state[click_state]
    elif triggered_id == 'tabulator':
        state = row['State']  

    # make revenue or expenditure report
    dff_map = df_rev if exp_or_rev == "Revenue" else df_exp
    dff_table =  dff_map.copy()
    dff_sunburst = dff_map.copy()
    update_title = " ".join([str(year), exp_or_rev, "Per Capita by State"])
    sunburst_title = " ".join([str(year), exp_or_rev, "Per Capita All States"])

    # subtotal table
    if subtotal == "state":
        dff_table = dff_table.groupby(["ST", "State"]).sum().reset_index()
    elif subtotal == "cat":
        dff_table = dff_table.groupby(["ST", "State", "Category"]).sum().reset_index()
    elif subtotal == "subcat":
        dff_table = (
            dff_table.groupby(["ST", "State", "Category", "Description"]).sum().reset_index()
        )
    elif subtotal == "local":
        dff_table = (
            dff_table.groupby(["ST", "State", "Category", "Description", "State/Local"])
            .sum()
            .reset_index()
        )
    dff_table["sparkline"] = make_sparkline(dff_table, "Per Capita", YEARS)
    dff_table = year_filter(dff_table, str(year))

    # Update map and title with selected row from table
    if row:
        cat = row.get('Category')
        if cat:
            dff_map = dff_map[dff_map['Category'] == cat]
            update_title = " ".join([str(year), exp_or_rev, cat])

        subcat = row.get('Description')
        if subcat:
             dff_map = dff_map[dff_map['Description'] == subcat]
             update_title = " ".join([str(year), exp_or_rev, subcat])

        local = row.get('State/Local')
        if local:
             dff_map = dff_map[dff_map['State/Local'] == local]
             update_title = " ".join([update_title, "and", local, "gvmt only"])   
    
    return (
        make_choropleth(dff_map, update_title, state, str(year)),
        df_to_data(dff_table),        
        state
    )


if __name__ == "__main__":
    app.run_server(debug=True)





    
#category_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="category_dropdown",
#            options=[{"label": c, "value": c} for c in df_exp["Category"].unique()],
#            placeholder="Select a category",
#        )
#    ],
#    className="px-2",
#)

#sub_category_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="subcategory_dropdown",
#            options=[{"label": c, "value": c} for c in df_exp["Description"].unique()],
#            placeholder="Select a sub category",
#            style={'font-size' : '90%'}
#        )
#    ],
#    className="px-2",
#)

#state_local_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="state_local_dropdown",
#            options=[
#                {"label": "State", "value": "State"},
#                {"label": "Local", "value": "Local"},
#            ],
#            placeholder="Select State or Local",
#        )
#    ],
#    className="px-2",
#)






###### updates sub category dropdown
#@app.callback(
#    [
#        Output("subcategory_dropdown", "options"),
#        Output("subcategory_dropdown", "value"),
#    ],
#    [Input("category_dropdown", "value"), Input("store_exp_or_rev", "data")],
#)
#def update_sub_category_dropdown(cat, exp_or_rev):
#    print(exp_or_rev)
#    dff = df_exp if exp_or_rev == "Expenditures" else df_rev

#    if cat is None:
#        options = [{"label": s, "value": s} for s in dff["Description"].unique()]
#    else:
#        subcats = dff[dff["Category"] == cat]
#        options = [{"label": s, "value": s} for s in subcats["Description"].unique()]

#    return options, None


######## update subtotal selection with dropdown
#@app.callback(
#    Output("table_subtotal", "value"),
#    [
#        Input("category_dropdown", "value"),
#        Input("subcategory_dropdown", "value"),
#        Input("state_local_dropdown", "value"),
#    ],
#)
#def update_subtotals(cat, subcat, local):
#    if local:
#        return "local"
#    if subcat:
#        return "subcat"
#    if cat:
#        return "cat"
#    else:
#        return "state"

    ## filter
    #if state != "USA":
    #    dff_table = (
    #        dff_table[dff_table["State"] == state]
    #        if state
    #        else dff_table[dff_table["State"] == "Alabama"]
    #    )
    #    dff_sunburst = dff_table.copy()
    #    sunburst_title = " ".join([str(year), exp_or_rev, state])
    #if cat and subcat is None:
    #    dff_table = dff_table[dff_table["Category"] == cat]
    #    dff_map = dff_map[dff_map["Category"] == cat]
    #    update_title = " ".join([str(year), exp_or_rev, cat])
    #if subcat:
    #    dff_table = dff_table[dff_table["Description"] == subcat]
    #    dff_map = dff_map[dff_map["Description"] == subcat]
    #    update_title = " ".join([str(year), exp_or_rev, subcat])
    #if local:
    #    dff_table = dff_table[dff_table["State/Local"] == local]
    #    dff_map = dff_map[dff_map["State/Local"] == local]
    #    update_title = " ".join([update_title, "and", local, "gvmt only"])



    
def make_table(dff):

    #dff = dff.groupby(["State"]).sum().reset_index()
    #dff["sparkline"] = make_sparkline(dff, "Per Capita", YEARS)
    #dff = table_yr(dff, START_YR)

    return html.Div(
        [
            dash_table.DataTable(
                id="table",
                columns=[
                    {"id": "State", "name": "State", "type": "text"},
                    {"id": "Category", "name": "Category", "type": "text"},
                    {"id": "Description", "name": "Sub Category", "type": "text"},
                    {"id": "State/Local", "name": "State or Local ", "type": "text"},
                    {
                        "id": "Amount",
                        "name": "Total Amount",
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                    {
                        "id": "Per Capita",
                        "name": "Per Capita",
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                    {
                        "id": "sparkline",
                        "name": "Per Capita 2012-2017",
                        "type": "numeric",
                        "format": FormatTemplate.money(0),
                    },
                ],
                data=dff.to_dict("records"),
                sort_action="native",
                sort_mode="multi",
                export_format="xlsx",
                export_headers="display",
                style_table={
                    "overflowY": "scroll",
                    "border": "thin lightgrey solid",
                    "maxHeight": "450px",
                },
                style_cell={
                    "textAlign": "left",
                    "font-family": "arial",
                    "font-size": "16px",
                },
                style_cell_conditional=[
                    {"if": {"column_id": c}, "textAlign": "right"}
                    for c in ["Per Capita", "Amount"]
                ],
                style_data_conditional=[
                    {
                        "if": {"state": "active"},
                        "backgroundColor": "rgba(150, 180, 225, 0.2)",
                        "border": "1px solid blue",
                    },
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "rgba(0, 116, 217, .03)",
                        "border": "1px solid blue",
                    },
                    {
                        "if": {"column_id": "sparkline"},
                        "width": 100,
                        "font-family": "Sparks-Bar-Extrawide",
                        "padding-right": "20px",
                        "padding-left": "20px",
                    },
                ],
            )
        ],
        id="table_div",
    )

