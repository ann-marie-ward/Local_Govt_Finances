"""
These are helper functions for the Exploring State and Local 
Govermnemtns app.


"""

import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import pathlib
import pickle
import colorlover


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("./data").resolve()
DATA_PREP_PATH = PATH.joinpath("./data_prep_city").resolve()

# file that shows which item codes are in each line of the summary report
with open(DATA_PATH.joinpath("df_summary.pickle"), "rb") as handle:
    df_summary = pickle.load(handle)

df_cat_desc = df_summary[["Line", "Category", "Description"]]

line_desc = dict(zip(df_summary.Line, df_summary.Description))

#####   App init settings:
INIT_ST = "AL"
INIT_STATE = "Alabama"
YEARS = [str(year) for year in range(2012, 2018)]
LOCAL_YEARS = [str(year) for year in range(2014, 2018)]
START_YR = "2017"

INIT_CAT = "Public Safety"
INIT_SUBCAT = "Police Protection"
INIT_STATE_SUBCATS = df_cat_desc[df_cat_desc["Category"] == "Public Safety"][
    "Description"
].unique()


state_abbr = {
    "United States": "US",
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

abbr_state = dict(map(reversed, state_abbr.items()))

states_only = state_abbr.copy()
del states_only["United States"]

abbr_state_noUS = abbr_state.copy()
del abbr_state_noUS["US"]

state_code = {
    "United States": "00",
    "Alabama": "01",
    "Alaska": "02",
    "Arizona": "03",
    "Arkansas": "04",
    "California": "05",
    "Colorado": "06",
    "Connecticut": "07",
    "Delaware": "08",
    "District of Columbia": "09",
    "Florida": "10",
    "Georgia": "11",
    "Hawaii": "12",
    "Idaho": "13",
    "Illinois": "14",
    "Indiana": "15",
    "Iowa": "16",
    "Kansas": "17",
    "Kentucky": "18",
    "Louisiana": "19",
    "Maine": "20",
    "Maryland": "21",
    "Massachusetts": "22",
    "Michigan": "23",
    "Minnesota": "24",
    "Mississippi": "25",
    "Missouri": "26",
    "Montana": "27",
    "Nebraska": "28",
    "Nevada": "29",
    "New Hampshire": "30",
    "New Jersey": "31",
    "New Mexico": "32",
    "New York": "33",
    "North Carolina": "34",
    "North Dakota": "35",
    "Ohio": "36",
    "Oklahoma": "37",
    "Oregon": "38",
    "Pennsylvania": "39",
    "Rhode Island": "40",
    "South Carolina": "41",
    "South Dakota": "42",
    "Tennessee": "43",
    "Texas": "44",
    "Utah": "45",
    "Vermont": "46",
    "Virginia": "47",
    "Washington": "48",
    "West Virginia": "49",
    "Wisconsin": "50",
    "Wyoming": "51",
}

code_state = dict(map(reversed, state_code.items()))


code_abbr = dict(zip(list(code_state), list(abbr_state)))


# this is position 3 of the ID code Note- "c" is only in my app so that both
#  cities and towns can be selected in the dropdown.  It is not in the data
code_type = {
    "0": "State",
    "1": "Counties",
    "c": "Cities and Towns",
    "2": "Cities",
    "3": "Townships",
    "4": "Special Districts",
    "5": "School Districts",
}

type_code = dict(map(reversed, code_type.items()))

# it's true, 4 is missing
code_level = {
    "1": "State and Local",
    "2": "State",
    "3": "Local",
    "5": "County",
    "6": "City",
    "7": "Township",
    "8": "Special District",
    "9": "School District",
}

level_code = dict(map(reversed, code_level.items()))

code_special_district = {
    "01": "Air transportation (airports)",
    "02": "Cemeteries",
    "03": "Miscellaneous commercial activities",
    "04": "Correctional institutions",
    "05": "Other corrections",
    "09": "Education (school building authorities)",
    "24": "Fire protection",
    "32": "Health",
    "40": "Hospitals",
    "41": "Industrial development",
    "42": "Mortgage credit",
    "44": "Regular highways",
    "45": "Toll highways",
    "50": "Housing and community development",
    "51": "Drainage",
    "52": "Libraries",
    "59": "Other natural resources",
    "60": "Parking facilities",
    "61": "Parks and recreation",
    "62": "Police protection",
    "63": "Flood control",
    "64": "Irrigation",
    "77": "Public welfare institutions",
    "79": "Other public welfare",
    "80": "Sewerage",
    "81": "Solid waste management",
    "86": "Reclamation",
    "87": "Sea and inland port facilities",
    "88": "Soil and water conservation",
    "89": "Other single-function districts",
    "91": "Water supply utility",
    "92": "Electric power utility",
    "93": "Gas supply utility",
    "94": "Mass transit system utility",
    "96": "Fire protection and water supply - combination of services",
    "97": "Natural resources and water supply - combination of services",
    "98": "Sewerage and water supply - combination of services",
    "99": "Other multifunction districts",
}
special_district_code = dict(map(reversed, code_special_district.items()))

level_code = dict(map(reversed, code_level.items()))


# Line numbers from the census spreadsheet and df_summary for each expenditure category
expenditure_cats = {
    "Education": [71, 73, 75, 76],
    "Administration": [106, 108, 109, 110],
    "Health & Welfare": [101, 84, 83, 81, 78, 80, 79, 85],
    "Parks & Recreation": [99, 97],
    "Public Safety": [107, 94, 93, 92, 96],
    "Transportation": [88, 86, 89, 90],
    "Utilities": [102, 104, 116, 117, 118, 115],
    "Other": [119, 111, 112],
}

# Line numbers from the census spreadsheet and df_summary for each revenue category
revenue_cats = {
    "Inter-Governmental": [4],
    "Property Tax": [9],
    "Sales Tax": [11, 13, 14, 15, 16, 17],
    "Income Tax": [18],
    "Other Tax": [19, 20, 21],
    "Current Charges": [24, 27, 28, 29, 30, 31, 32, 33, 34, 37, 47],
    "Utilities": [35, 36, 44, 45, 46],
    "Other": [39, 40, 41, 42, 48],
}


exp_lines = [
    71,
    73,
    75,
    76,
    106,
    108,
    109,
    110,
    101,
    84,
    83,
    81,
    78,
    80,
    79,
    85,
    99,
    97,
    107,
    94,
    93,
    92,
    96,
    88,
    86,
    89,
    90,
    102,
    104,
    116,
    117,
    118,
    115,
    119,
    111,
    112,
]

rev_lines = [
    4,
    9,
    11,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    24,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    37,
    47,
    35,
    36,
    44,
    45,
    46,
    39,
    40,
    41,
    42,
    48,
]

sunburst_colors = {
    "Education": "#446e96",
    "Inter-Governmental": "#446e96",
    "Administration": "#999999",
    "Property Tax": "#999999",
    "Health & Welfare": "#d47500",
    "Sales Tax": "#3cb521",
    "Parks & Recreation": "#3cb521",
    "Income Tax": "#cd0200",
    "Public Safety": "#cd0200",
    "Other Tax": "#d47500",
    "Transportation": "#3399f3",
    "Current Charges": "#3399f3",
    "Utilities": "#eeeeee",
    "Other": "#333333",
    "(?)": "white",
}


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
                    "barmode": "relative",
                    "hovermode": "closest",
                    "height": 375,
                    "margin": {"t": 10, "l": 10, "r": 10, "b": 200},
                },
            },
        )
    ]


def get_col(col_name, year):
    """Helps select column from df_exp and df_rev.
    returns  'Amount_2017' from input args ('Amount', 2017)
    """
    return "".join([col_name, "_", year])


def make_sparkline(dff, spark_col, spark_yrs):
    """Makes df column with data formatted for sparkline figure.

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
    dff = pd.DataFrame()
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
            dff[column + "_color"] = pd.cut(
                df_numeric_columns[column],
                bins=ranges,
                labels=colors,
                duplicates="drop",
            )
        except:
            return [], [], pd.DataFrame(), 0

    return (
        styles,
        html.Div(legend, style={"padding": "5px 0 5px 0"}),
        dff,
        df_max,
    )
