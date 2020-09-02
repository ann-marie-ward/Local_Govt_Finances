from dash.dependencies import Input, Output, State
import dash_table
import dash_table.FormatTemplate as FormatTemplate
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import pathlib
import dash_bootstrap_components as dbc


from app import app, navbar3, footer3, asset_allocation_text, backtesting_text

# Input Files
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../assets").resolve()

#  make dataframe from  spreadsheet:
df = pd.read_excel(DATA_PATH.joinpath("historic.xlsx"))

MAX_YR = df.Year.max()
MIN_YR = df.Year.min()

# since data is as of year end, need to add start year
df = (
    df.append({"Year": MIN_YR - 1}, ignore_index=True)
    .sort_values("Year", ignore_index=True)
    .fillna(0)
)


def highlights():
    """ creates data to highlight certain time periods """
    years = ["2007", "2000", "1970", "1929", "1928"]
    planning_time = [13, 10, 10, 20, 93]
    time_period_names = [
        "2007-2008 Great Financial Crisis",
        "2000 Dotcom Bubble peak",
        "1970s Energy Crisis",
        "1929 start of Great Depression",
        "1928-2019",
    ]
    
    options = [{"label": time_period, "value" :yr} for time_period, yr in zip(time_period_names,  years)]
    timeframe = {
        yr: {"start_yr": int(yr), "planning_time": time}
        for yr, time in zip(years, planning_time)
    }
    return options, timeframe


OPTIONS, TIMEFRAME = highlights()


##################  Calculations - Backtest Returns #################


def backtest(stocks, cash, start_bal, nper, start_yr, pmt):
    """ calculates the investment returns for user selected asset allocation,
        rebalanced annually
    """

    end_yr = start_yr + nper - 1
    cash_allocation = cash / 100
    stocks_allocation = stocks / 100
    bonds_allocation = (100 - stocks - cash) / 100

    # Select time period - since data is for year end, include year prior for start ie year[0]
    dff = df[(df.Year >= start_yr - 1) & (df.Year <= end_yr)].set_index(
        "Year", drop=False
    )
    dff["Year"] = dff["Year"].astype(int)

    # add columns for My Portfolio returns
    dff["Cash"] = cash_allocation * start_bal
    dff["Bonds"] = bonds_allocation * start_bal
    dff["Stocks"] = stocks_allocation * start_bal
    dff["Total"] = start_bal
    dff["Rebalance"] = True

    # calculate My Portfolio returns
    for yr in dff.Year + 1:
        if yr <= end_yr:
            # Rebalance at the beginning of the period by reallocating
            # last period's total ending balance
            if dff.loc[yr, "Rebalance"]:
                dff.loc[yr, "Cash"] = dff.loc[yr - 1, "Total"] * cash_allocation
                dff.loc[yr, "Stocks"] = dff.loc[yr - 1, "Total"] * stocks_allocation
                dff.loc[yr, "Bonds"] = dff.loc[yr - 1, "Total"] * bonds_allocation

            # calculate this period's  returns
            dff.loc[yr, "Cash"] = dff.loc[yr, "Cash"] * (
                1 + dff.loc[yr, "3-mon T.Bill"]
            )
            dff.loc[yr, "Stocks"] = dff.loc[yr, "Stocks"] * (1 + dff.loc[yr, "S&P 500"])
            dff.loc[yr, "Bonds"] = dff.loc[yr, "Bonds"] * (
                1 + dff.loc[yr, "10yr T.Bond"]
            )
            dff.loc[yr, "Total"] = dff.loc[yr, ["Cash", "Bonds", "Stocks"]].sum()

    dff = dff.reset_index(drop=True)
    columns = ["Cash", "Stocks", "Bonds", "Total"]
    dff[columns] = dff[columns].round(0)

    ### create columns for when portfolio is all cash, all bonds or  all stocks,
    #   include inflation too
    #
    # create new df that starts in yr 1 rather than yr 0
    dff1 = (dff[(dff.Year >= start_yr) & (dff.Year <= end_yr)]).copy()
    #
    # calculate the returns in new df:
    columns = ["All_Cash", "All_Bonds", "All_Stocks", "Inflation_only"]
    annual_returns = ["3-mon T.Bill", "10yr T.Bond", "S&P 500", "Inflation"]
    for col, return_pct in zip(columns, annual_returns):
        dff1[col] = round(start_bal * (1 + (1 + dff1[return_pct]).cumprod() - 1), 0)
    #
    # select columns in the new df to merge with original
    dff1 = dff1[["Year"] + columns]
    dff = dff.merge(dff1, how="left")
    # fill in the starting balance for year[0]
    dff.loc[0, columns] = start_bal

    return dff


def update_cagr(dff, planning_time, start_bal):
    """calculate CAGR for cash, bonds and stocks in selected period and format for display panel

            Compound Annual Growth Rate = CAGR = end$ /start$ exp (1/#yrs) -1 """

    end = dff.loc[
        planning_time,
        ["All_Cash", "All_Bonds", "All_Stocks", "Total", "Inflation_only"],
    ]

    cagr = (((end / start_bal) ** (1 / planning_time)) - 1).fillna(0)
  
    # format cagr
    cagr = [
        "{:.1%}".format(cagr[asset])
        for asset in ["All_Cash", "All_Bonds", "All_Stocks", "Total", "Inflation_only"]
    ]
    return cagr


def update_worst(dff):
    """calculate worst returns for cash, bonds and stocks in selected period
            and format for display panel """

    returns = ["3-mon T.Bill", "10yr T.Bond", "S&P 500"]
    worst = []
    for returns in returns:
        worst_yr_loss = min(dff[returns])
        worst_loss = dff.loc[dff[returns] == worst_yr_loss]
        worst_year = worst_loss.iloc[0, 0]
        worst.append("{}:  {:.1%}".format(worst_year, worst_yr_loss))
    return worst


######################  Figures  ####################################


#######  Pie chart


def make_pie(slider_input, title):
    colors = ["#3cb521", "#f5b668", "#3399f3"]
    fig = go.Figure(
        data=[
            go.Pie(labels=["Cash", "Bonds", "Stocks"], values=slider_input, sort=False)
        ]
    )
    fig.update_traces(textinfo="label+percent", marker=dict(colors=colors)),
    fig.update_layout(
        title_text=title,
        title_x=0.5,
        margin=go.layout.Margin(b=25, t=75, l=35, r=25),
        height=375,
        paper_bgcolor="whitesmoke",
    )
    return fig


pie_chart = html.Div(
    dcc.Graph(
        id="pie_allocation3",
        figure=make_pie([10, 40, 50], "Moderate Asset Allocation",),
    ),
    className="mb-2",
    style={"height": "375px"},
)

#########  Line chart


def make_returns_chart(dff, start_bal):
    start = dff.loc[1, "Year"]
    x = dff["Year"]
    yrs = dff["Year"].size - 1
    title = f"Returns for {yrs} years starting {start}"
    dtick = 1 if yrs < 16 else 2 if yrs in range(16, 30) else 5


    fig = go.Figure()    
    fig.add_trace(go.Scatter(x=x, y=dff["All_Cash"], name="All Cash", marker=dict(color="#3cb521")))
    fig.add_trace(go.Scatter( x=x,
                y=dff["All_Bonds"],
                name="All Bonds (10yr T.Bonds)",
                marker=dict(color="#d47500"),
            ))
    fig.add_trace(go.Scatter(x=x,
                y=dff["All_Stocks"],
                name="All Stocks (S&P500)",
                marker=dict(color="#3399f3"),
            ))
    fig.add_trace(go.Scatter(x=x,
                y=dff["Total"],
                name="My Portfolio",
                marker=dict(color="black"),
                line=dict(width=6, dash="dot"),
            ))
    fig.add_trace(go.Scatter( x=x,
                y=dff["Inflation_only"],
                name="Inflation",
                visible=True,
                marker=dict(color="cd0200"),
            ))
    fig.update_layout(
            title=title,
            showlegend=True,
            legend=dict(x=0.01, y=0.99),
            height=400,
            margin=dict(l=40, r=10, t=60, b=30),
            yaxis=dict(tickprefix="$", fixedrange=True),
            xaxis=dict(title="Year Ended", fixedrange=True, dtick=dtick),
        )
    return fig


#####################  Tables   #####################################


total_returns_table = html.Div(
    [
        dash_table.DataTable(
            id="total_returns3",
            columns=[{"id": "Year", "name": "Year", "type": "text"}]
            + [
                {
                    "id": col,
                    "name": col,
                    "type": "numeric",
                    "format": FormatTemplate.money(0),
                }
                for col in ["Cash", "Bonds", "Stocks", "Total"]
            ],
            style_table={
                "overflowY": "scroll",
                "border": "thin lightgrey solid",
                "maxHeight": "425px",
            },
            style_cell={"textAlign": "right", "font-family": "arial"},
            style_cell_conditional=[{"if": {"column_id": "Year"}, "type": "text"}],
        )
    ]
)


annual_returns_pct_table = html.Div(
    [
        dash_table.DataTable(
            id="annual_returns_pct",
            columns=(
                [{"id": "Year", "name": "Year", "type": "text"}]
                + [
                    {
                        "id": col,
                        "name": col,
                        "type": "numeric",
                        "format": FormatTemplate.percentage(1),
                    }
                    for col in df.columns[1:]
                ]
            ),
            style_cell={"textAlign": "right", "font-family": "arial"},
            style_table={
                "overflowY": "scroll",
                "border": "thin lightgrey solid",
                "maxHeight": "400px",
            },
            data=df.to_dict("records"),
        )
    ],
)


########## Make table for best and worst periods

table_header = [
    html.Thead(
        html.Tr(
            [
                html.Th(" "),
                html.Th(" "),
                html.Th(id="title_cagr"),
                html.Th(id="title_crash3"),
            ]
        )
    )
]

fa_cash = html.I(className="fa fa-money-bill-alt", style={"font-size": "150%"})
fa_bonds = html.I(className="fa fa-handshake", style={"font-size": "150%"})
fa_stocks = html.I(className="fa fa-industry ", style={"font-size": "150%"})
fa_inflation = html.I(className="fa fa-ambulance", style={"font-size": "150%"})

row1 = html.Tr(
    [
        html.Td("Cash"),
        html.Td(fa_cash),
        html.Td(id="cash_cagr"),
        html.Td(id="cash_crash3"),
    ],
)
row2 = html.Tr(
    [
        html.Td("Bonds"),
        html.Td(fa_bonds),
        html.Td(id="bond_cagr"),
        html.Td(id="bond_crash3"),
    ],
)
row3 = html.Tr(
    [
        html.Td("Stocks"),
        html.Td(fa_stocks),
        html.Td(id="stock_cagr"),
        html.Td(id="stock_crash3"),
    ],
)
row4 = html.Tr(
    [
        html.Td("Inflation"),
        html.Td(fa_inflation),
        html.Td(id="inflation_cagr"),
        html.Td(" "),
    ],
)

table_body = [html.Tbody([row1, row2, row3, row4], className="text-center")]

best_worst_table = dbc.Table(
    table_header + table_body,
    bordered=True,
    responsive=True,
    style={"backgroundColor": "whitesmoke"},
)


datasource_text = dcc.Markdown(
    """    
    [Data source:](http://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html)
    Historical Returns on Stocks, Bonds and Bills from NYU Stern School of Business
    """
)


#####################  Make Tabs  ###################################


#######  Play tab components

asset_allocation_card = html.Div(
    dbc.Card(
        dbc.CardBody(
            html.Div(
                html.Div(asset_allocation_text, className="ml-3"),
                style={
                    "border-left": "solid",
                    "border-color": "#446e9b",
                    "border-left-width": "10px",
                },
            )
        ),
        className="mt-4",
    )
)


slider_card = html.Div(
    dbc.Card(
        dbc.CardBody(
            [
                html.H4("First set cash allocation %:", className="card-title"),
                dcc.Slider(
                    id="cash3",
                    marks={i: "{}%".format(i) for i in range(0, 101, 10)},
                    min=0,
                    max=100,
                    step=5,
                    value=10,
                    included=False,
                    persistence=True,
                    persistence_type="session",
                ),
                html.H4(
                    "Then set stock allocation % ",
                    className="card-title mt-3",
                ),
                html.Div("(The rest will be bonds)", className='card-title'),
                dcc.Slider(
                    id="stock_bond3",
                    marks={i: "{}%".format(i) for i in range(0, 91, 10)},
                    persistence=True,
                    persistence_type="session",
                    min=0,
                    max=90,
                    step=5,
                    value=50,
                    included=False,
                ),
            ],
        ),
        className="mt-4",
    )
)

inflation_checkbox = html.Div(
    dcc.Checklist(
        id="inflation",
        persistence=True,
        persistence_type="session",
        labelClassName="m-2",
        inputClassName="mr-3",
        options=[{"label": "Include inflation on graph", "value": "Yes",}],
        value=["Yes"],
    )
)


time_period_card = html.Div(
    dbc.Card(
        [
            html.H4("Or check out one of these time periods:", className="card-title"),
            dcc.RadioItems(
                id="select_timeframe",
                options=OPTIONS,
                labelStyle={"display": "block"},
                labelClassName="m-2",
                inputClassName="mr-3",
                value="2007",
            ),
        ],
        body=True,
        className="mt-4",
    )
)

amount_input_card = html.Div(
    dbc.Card(
        [
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Start Amount $ :", addon_type="prepend"),
                    dbc.Input(
                        id="starting_amount3",
                        placeholder="$",
                        type="number",
                        persistence=True,
                        persistence_type="session",
                        min=0,
                        value=10000,
                    ),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Number of Years:", addon_type="prepend"),
                    dbc.Input(
                        id="planning_time3",
                        placeholder="#yrs",
                        type="number",
                        persistence=True,
                        persistence_type="session",
                        min=1,
                        value=13,
                    ),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Start Year:", addon_type="prepend"),
                    dbc.Input(
                        id="start_yr3",
                        placeholder=f"{MIN_YR} to {MAX_YR}",
                        type="number",
                        persistence=True,
                        persistence_type="session",
                        min=MIN_YR,
                        max=MAX_YR,
                        value=2007,
                    ),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Results: ", addon_type="prepend"),
                    dbc.Input(id="results3", type="text", disabled=True,),
                ],
                className="mb-3",
                style={"width": "300px"},
            ),
        ],
        body=True,
        className="mt-4",
    )
)


#########  Results Tab componenets

results_card = html.Div(
    dbc.Card(
        [
            dbc.CardHeader("My Portfolio Returns - Rebalanced Annually"),
            dbc.CardBody(total_returns_table),
        ],
        outline=True,
        className="mt-4",
    )
)

data_source_card = html.Div(
    dbc.Card(
        [
            dbc.CardHeader("Source Data: Annual Total Returns",),
            dbc.CardBody(annual_returns_pct_table),
        ],
        outline=True,
        className="mt-4",
    )
)

#########  Learn Tab  Components
learn_card = html.Div(
    dbc.Card(
        [
            dbc.CardHeader("An Introduction to Backtesting",),
            dbc.CardBody(backtesting_text),
        ],
        outline=True,
        className="mt-4",
    )
)


######## Build tabs
tabs = html.Div(
    dbc.Tabs(
        [
            dbc.Tab(
                learn_card,
                tab_id="tab1",
                label="Learn",
                label_style={"font-size": "150%", "width": "125px"},
            ),
            dbc.Tab(
                [
                    asset_allocation_card,
                    slider_card,
                    amount_input_card,
                    inflation_checkbox,
                    time_period_card,
                ],
                tab_id="tab-2",
                label="Play",
                label_style={"font-size": "150%", "width": "125px"},
            ),
            dbc.Tab(
                [results_card, data_source_card],
                tab_id="tab-3",
                label="Results",
                label_style={"font-size": "150%", "width": "125px"},
            ),
        ],
        id="tabs",
        active_tab="tab-2",
    ),
    style={"minHeight": "800px"},
)


########################  Main Layout     ###########################

layout = dbc.Container(
    [
        navbar3,
        dbc.Row(
            dbc.Col(
                html.H4(
                    "Asset Allocation Visualizer",
                    className="text-center bg-light m-2 p-2",
                ),
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(tabs),
                    width={"size": 5, "order": 1},
                    className="mt-4 border",
                ),
                dbc.Col(
                    [
                        pie_chart,
                        dcc.Graph(id="returns_chart3", className="border"),
                        html.H6(datasource_text),
                        best_worst_table,
                    ],
                    width={"size": 7, "order": 2},
                    className="pt-4 ",
                ),
            ],
            className="ml-4",
        ),
        dbc.Row(dbc.Col(footer3, className="mt-5")),
    ],
    fluid=True,
)


#######################    Callbacks     #############################


@app.callback(
    [
        Output("stock_bond3", "max"),
        Output("stock_bond3", "marks"),
        Output("stock_bond3", "value"),
    ],
    [Input("cash3", "value")],
    [State("stock_bond3", "value")],
)
def update_stock_slider(cash, initial_stock_value):
    max_slider = 100 - int(cash)
    if initial_stock_value > max_slider:
        stocks = max_slider
    else:
        stocks = initial_stock_value

    # formats the slider scale
    if max_slider > 50:
        marks_slider = {i: "{}%".format(i) for i in range(0, max_slider + 1, 10)}
    elif max_slider <= 15:
        marks_slider = {i: "{}%".format(i) for i in range(0, max_slider + 1, 1)}
    else:
        marks_slider = {i: "{}%".format(i) for i in range(0, max_slider + 1, 5)}
    return max_slider, marks_slider, stocks


@app.callback(
    Output("pie_allocation3", "figure"),
    [Input("stock_bond3", "value"), Input("cash3", "value")],
)
def update_pie(stocks, cash):
    bonds = 100 - stocks - cash
    slider_input = [cash, bonds, stocks]
   
    if stocks >= 70:
        style = "Aggressive"
    elif stocks <= 30:
        style = "Conservative"
    else:
        style = "Moderate"
    figure = make_pie(slider_input, style + " Asset Allocation")
    return figure


@app.callback(
    [Output("planning_time3", "value"), Output("start_yr3", "value")],
    [Input("select_timeframe", "value")],
)
def update_timeframe(selected_yr):
    return TIMEFRAME[selected_yr]["planning_time"], TIMEFRAME[selected_yr]["start_yr"]


@app.callback(
    [
        Output("total_returns3", "data"),
        Output("returns_chart3", "figure"),
        Output("title_cagr", "children"),
        Output("cash_cagr", "children"),
        Output("bond_cagr", "children"),
        Output("stock_cagr", "children"),
        Output("inflation_cagr", "children"),
        Output("title_crash3", "children"),
        Output("cash_crash3", "children"),
        Output("bond_crash3", "children"),
        Output("stock_crash3", "children"),
        Output("results3", "value"),
    ],
    [
        Input("stock_bond3", "value"),
        Input("cash3", "value"),
        Input("starting_amount3", "value"),
        Input("planning_time3", "value"),
        Input("start_yr3", "value"),
        Input("inflation", "value"),
    ],
)
def update_totals(stocks, cash, start_bal, planning_time, start_yr, inflation):
    pmt = 0
    if start_bal is None:
        start_bal = 0
    if planning_time is None:
        planning_time = 1
    if start_yr is None:
        start_yr = MIN_YR

    bonds = 100 - stocks - cash
    if stocks >= 70:
        style = "aggressive growth"
    elif stocks <= 30:
        style = "conservative"
    else:
        style = "moderate"

    # calculate valid time frames and ranges for UI

    max_time = MAX_YR + 1 - start_yr
    planning_time = max_time if planning_time > max_time else planning_time
    if start_yr + planning_time > MAX_YR:
        start_yr = min(df.iloc[-planning_time, 0], MAX_YR)  # 0 is Year column
    end_yr = min(MAX_YR, start_yr + planning_time - 1)
    start_yr = int(start_yr)

    # create df of backtest results
    dff = backtest(stocks, cash, start_bal, planning_time, start_yr, pmt)

    # create data for  datatable
    data = dff.to_dict("records")

    # create the line chart
    figure = make_returns_chart(dff, start_bal)

    figure.update_traces(visible=False, selector=dict(name="Inflation"))
    if inflation:
        figure.update_traces(visible=True, selector=dict(name="Inflation"))

    # update cagr
    title_cagr = f"Annual returns (CAGR) from {start_yr} to {end_yr}"
    cash_cagr, bonds_cagr, stocks_cagr, total_cagr, inflation_cagr = update_cagr(
        dff, planning_time, start_bal
    )

    # update worst year info
    title_crash = f"Worst Year from {start_yr} to {end_yr}"
    worst_cash, worst_bonds, worst_stocks = update_worst(dff)

    ending_balance = "${:0,.0f}".format(dff["Total"].iloc[-1])

    return (
        data,
        figure,
        title_cagr,
        cash_cagr,
        bonds_cagr,
        stocks_cagr,
        inflation_cagr,
        title_crash,
        worst_cash,
        worst_bonds,
        worst_stocks,
        ending_balance,
    )


if __name__ == "__main__":
    app.run_server(debug=False)