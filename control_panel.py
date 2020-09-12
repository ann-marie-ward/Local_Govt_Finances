import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import data_utilities as du


########### common
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


year_slider = html.Div(
    [
        #  html.Div('Select Year:', style={'font-weight':'bold'}),
        dcc.Slider(
            id="year",
            min=int(min(du.YEARS)),
            max=int(max(du.YEARS)),
            step=1,
            # marks={int(year) : year for year in YEARS },
            marks={
                int(year): {"label": year, "style": {"writing-mode": "vertical-rl"}}
                for year in du.YEARS
            },
            value=int(du.START_YR),
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
            + [{"label": state, "value": state} for state in du.states_only],
            value="USA",
            clearable=False,
            className="mt-2",
        ),
    ],
    className="px-2",
)


category_dropdown = html.Div(
    [
        html.Div("Select a Category:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="category_dropdown",
            options=[{"label": "All Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in du.expenditure_cats],
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
            + [{"label": c, "value": c} for c in du.INIT_STATE_SUBCATS],
            # placeholder="Select a sub category",
            style={"font-size": "90%"},
            value=du.INIT_SUBCAT,
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

clear_button = html.Div(
    [
        dbc.Button(
            "Clear selections",
            id="clear",
            n_clicks=0,
            color="light",
            className="mt-1 btn-sm float-right",
        )
    ]
)

warning_msg_collapse = html.Div(
    [
        dbc.Button(id="collapse-button", style={"display": "none"}),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(
                    "To see data, try clearing some selections",
                    className="border border-warning font-weight-bold text-warning",
                    id="warning_msg",
                )
            ),
            id="collapse",
        ),
    ],
    style={"width": "400px"},
)


#############   Local only buttons  and controls  ###############################

type_dropdown = html.Div(
    [
        html.Div(
            "Select a Type: ie local, county gov, school district...",
            style={"font-weight": "bold"},
        ),
        dcc.Dropdown(
            id="local_type",
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
            id="local_county_dropdown",
            options=[{"label": "All Counties", "value": "all"}],
            placeholder="Enter a name",
        ),
    ],
    className="px-2",
)

local_dropdown = html.Div(
    [
        html.Div("Select a Name:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id="local_name_dropdown",
            options=[{"label": "All ", "value": "all"}],
            placeholder="Enter a name",
        ),
    ],
    className="px-2",
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

mystate_dropdown = html.Div(
    [
        dcc.Dropdown(
            id="mystate",
            options=[{"label": state, "value": state} for state in du.states_only],
            value="Arizona",
            clearable=False,
        )
    ],
    className="mt-3",
)


controls_group = html.Div(
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
            [
                county_dropdown,
                type_dropdown,
                local_dropdown,
            ],
            className="mt-2, pb-4 bg-white",
            style={"display": "none"},
            id="local_controls",
        ),
        html.Div(
            clear_button,
            className="ml-1",
        ),
    ]
)
