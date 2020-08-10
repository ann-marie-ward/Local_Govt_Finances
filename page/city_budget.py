import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly.express as px
import dash_table
import dash_table.FormatTemplate as FormatTemplate

import dash_bootstrap_components as dbc
import dash_tabulator
import pandas as pd
import numpy as np
import pathlib
import pickle
import json

import data_utilities as du
from app import app, navbar, footer

styles = {
            'pre': {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll',
                
            },
           
        }

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 12)


# Update this when new data is added:
#YEARS = [str(year) for year in range(2012, 2018)]
YEARS = ['2014', '2015', '2016', '2017']
START_YR = "2017"

init_selected_cities = {'48201702100000': 'SEATTLE, WA', '38202600300000': 'PORTLAND, OR',
                        '03201000200000': "TUCSON, AZ"}
                #        '03201000200000': "TUCSON", '03201090200000': "MARANA"}


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
DATA_PREP_PATH = PATH.joinpath("../data_prep_city").resolve()

# file with meta data info for each city like name, state, population etc
# dictionary with year as key
with open(DATA_PATH.joinpath('Fin_GID.pickle'), 'rb') as handle:
    Fin_GID = pickle.load(handle)


# file which shows which item codes are in each line of the summary report
with open(DATA_PATH.joinpath('df_summary.pickle'), 'rb') as handle:
    df_summary = pickle.load(handle)


# City Expenditures df
with open(DATA_PATH.joinpath('df_city_exp.pickle'), 'rb') as handle:
    df_exp = pickle.load(handle)

# City Revenue df
with open(DATA_PATH.joinpath('df_city_rev.pickle'), 'rb') as handle:
    df_rev = pickle.load(handle)

# used to add line description to report
df_description = df_summary[['Line', 'Description']]


# add category
df_summary['Category']= ''
df_summary['Type']= ''
for cat in du.revenue_cats:
    for line_no in du.revenue_cats[cat]:
        df_summary.loc[df_summary['Line'] == line_no, ['Category', 'Type']] = [cat, 'R']      
        
for cat in du.expenditure_cats:
    for line_no in du.expenditure_cats[cat]:
        df_summary.loc[df_summary['Line'] == line_no, ['Category', 'Type']] = [cat, 'E']


#########  Table helper functions #############################################


def make_dff_exp_rev(selected_cities, exp_or_rev):
    ''' creates the revenue and expense report in a wide format - years as columns
        for selected cities to display in table
    '''

    if exp_or_rev == 'expenditures':
       df_table = df_exp[df_exp['ID code'].isin(selected_cities)]
    else:
        df_table = df_rev[df_rev['ID code'].isin(selected_cities)]   
    
    df_table['Amount'] =   df_table['Amount'] * 1000
    df_table['Per Capita'] = (df_table['Amount'] / df_table['Population']).fillna(0).replace([np.inf, -np.inf], 0)
    df_table['Per Student'] = (df_table['Amount'] / df_table['Enrollment']).fillna(0).replace([np.inf, -np.inf], 0)
    
    # drop Population and Enrollment
    df_table = df_table[[
    'Line', 'Category', 'ST', 'ID name', 'Amount', 'ID code', 'Year', 'Per Capita', 'Per Student']]


    df_table = pd.merge(df_table, df_description, how='left', on="Line")    

    # make table wide  (years as columns)
    df_tablew = (
        df_table.groupby(["ST", "ID code", "ID name", "Category", "Description", 'Year'])
                .sum()
                .unstack('Year')
                .reset_index()
    )
    # flatten multi-level column headings
    level0=df_tablew.columns.get_level_values(0)
    level1=df_tablew.columns.get_level_values(1)
    df_tablew.columns = level0+'_'+level1
    df_tablew = df_tablew.rename(columns={'ST_': 'ST', 'ID code_': 'ID code', 'ID name_': 'ID name', 
                                          'Category_': 'Category', 'Description_': 'Description'})
    df_tablew['ID name'] = df_tablew['ID name'] + ", " + df_tablew['ST']
    return(df_tablew.to_dict('records'))


def get_col(col_name, year):
    """ Helps select column from df_exp and df_rev.  
        returns  'Amount_2017' from input args ('Amount', 2017)
    """
    return "".join([col_name, "_", year])


def year_filter(dff, year):
    """ renames columns to so selected year doesn't have the year extention ie Amount_2017 """
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


#######  Tabulator Selection table ############################################

def df_to_data(dff):
    ''' creates data for tabulator from a dataframe '''

    # makes the index the first column 
    dff['id'] = dff.index

    col = dff.pop("id")
    dff.insert(0, col.name, col)   
    return dff.to_dict("records")


#options = { "selectable":True, "layout":"fitDataTable", "height":"500px"}
display_cities_options = { "selectable":False,
          "maxHeight":"500px", 
           "initialSort":[{"column":"Year", "dir":"dsc"}],
         #  "layout":"fitColumns "
           }
select_cities_options = { "selectable":True,
          "maxHeight":"300px",   
        
       #   "groupBy": "ST"
        #   "layout":"fitDataFill"
      #      "layout":"fitColumns "
          
           }

downloadButtonType = {"css": "btn btn-primary btn-sm", "text":"Export", "type":"xlsx"}


#  This is the same as if you were using tabulator directly in js 
columns = [  
    {"formatter":"rowSelection",  "hozAlign":"center", 
     "headerSort":False, "width": 20,
     "cellClick":"function(e, cell){ cell.getRow().toggleSelect();}"
    },
    {"title": 'State', "field":  'ST',
     "hozAlign": "left",     
     "headerFilter":True,
     "hozAlign":"center"
     },    
     {"title": 'State name', "field":  'State',
     "hozAlign": "left",     
     "headerFilter":True,
     
     },    
     {"title": 'County', "field":  'County name',
     "hozAlign": "left",     
     "headerFilter":True
     },
     {"title": 'Local govt name', "field":  'ID name',
     "hozAlign": "left",     
     "headerFilter":True
     },
      {"title": 'Special districts', "field":  'Special districts',
     "hozAlign": "left",     
     "headerFilter":True
     },
     
     {"title": 'Population', "field":  'Population',
     "hozAlign": "right", 
     "formatter": "money", "formatterParams":{"precision":0},
    
    
    # "headerFilter":True
     },
    {"title": 'School Enrollment', "field": 'Enrollment',
     "hozAlign": "right",
     "formatter": "money", "formatterParams":{"precision":0},
    # "topCalc":"sum",  "topCalcParams":{"precision":0}
     },    
     
]


select_city_tabulator = dash_tabulator.DashTabulator(
                id='select_city_tabulator',
                columns=columns,
                data=df_to_data(Fin_GID[START_YR]),
                options=select_cities_options,
                downloadButtonType=downloadButtonType,
        ),



##########  Tabulator - City summary report output 
city_columns = [    

    {"title": 'State', "field":  'ST',
     "hozAlign": "left",     
     "headerFilter":True
     },    
     {"title": 'City/District', "field":  'ID name',
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
         
     {"title": 'Amount', "field":  'Amount',
     "hozAlign": "right", 
     "formatter": "money", "formatterParams":{"precision":0},
    # "headerFilter":True
     },
    {"title": 'Per Capita', "field": 'Per Capita',
     "hozAlign": "right",
     "formatter": "money", "formatterParams":{"precision":0},
    # "topCalc":"sum",  "topCalcParams":{"precision":0}
     },
     {"title": 'Per Capita 2014-2017', "field": 'sparkline_Per Capita',
     "hozAlign": "left",     
     "cssClass" : "bar-extrawide",
     },
     {"title": 'Per Student', "field": 'Per Student',
     "hozAlign": "right",
     "formatter": "money", "formatterParams":{"precision":0},
    # "topCalc":"sum",  "topCalcParams":{"precision":0}
    },
    {"title": 'Per Student 2014-2017', "field": 'sparkline_Per Student',
     "hozAlign": "left",     
     "cssClass" : "bar-extrawide",
     },
     
     
]

city_tabulator = dash_tabulator.DashTabulator(
                id='city_table',
                columns=city_columns,
                data=[],
                options=display_cities_options, 
                downloadButtonType=downloadButtonType,
        ),


##############  City Cards (sunburst + stats table)   #########################

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
        margin=go.layout.Margin(b=10, t=10, l=1, r=1),
        # yaxis=go.layout.YAxis(tickprefix="$", fixedrange=True),
        # xaxis=go.layout.XAxis(fixedrange=True),
        # annotations=total_labels,
        # paper_bgcolor="whitesmoke",
        clickmode="event+select",
    )
    
    return fig

def make_stats_table(dff):
    row1=[]
    row2=[]    
    per_capita = dff["Per Capita"].astype(float).sum() 
    per_student = dff["Per Student"].astype(float).sum()
    total_amt = dff["Amount"].astype(float).sum() * 1000

    if per_capita > 0:        
        population = total_amt / per_capita 
        row1 = html.Tr([html.Td("{:0,.0f}".format(population), style={'text-align':'right'}), html.Td("Population")])
        row2 = html.Tr([html.Td("${:0,.0f}".format(per_capita), style={'text-align':'right'}), html.Td("Per Capita")])
    elif per_student > 0:        
        enrollment = total_amt / per_student       
        row1 = html.Tr([html.Td("{:0,.0f}".format(enrollment), style={'text-align':'right'}), html.Td("School Enrollment")])
        row2 = html.Tr([html.Td("${:0,.0f}".format(per_student), style={'text-align':'right'}), html.Td("Per Student")])
    else:
        row2 = html.Tr([html.Td("${:0,.0f}".format(total_amt), style={'text-align':'right'}), html.Td("Total Amount")])

    table_body = [html.Tbody([row2, row1])]

    return dbc.Table(
        table_body,
        bordered=False,
        className="table table-sm table-light",
        style={"font-size": "12px"},
    )


########### buttons, dropdowns, check boxes, sliders  #########################

selected_cities_dropdown = html.Div(
    [
        dcc.Dropdown(
                    id='selected_cities_dropdown',
                    placeholder='Select cities from the table',
                    options=[{'label': name, 'value': code} for code, name in init_selected_cities.items()], 
                    value=list(init_selected_cities),
                    multi=True,                    
                  
                ), 
        
    ], className = 'overflow-auto', style={'height': '300px'}  
    
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
            included = False,
            className="mt-3  p-3 mb-5",
        )
    ]
)

category_dropdown = html.Div(
    [
        dcc.Dropdown(
            id="city_category_dropdown",
            options=[{"label": "All Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in df_exp["Category"].unique()],
            placeholder="Select a category",
            style={'font-size' : '90%'}
        )
    ],
    className="px-2",  style={'display':'none'}
)

sub_category_dropdown = html.Div(
    [
        dcc.Dropdown(
            id="city_subcategory_dropdown",
            options=[{"label": "All Sub Categories", "value": "all"}]
            + [{"label": c, "value": c} for c in df_description["Description"].unique()],
            placeholder="Select a sub category",
            style={'font-size' : '90%'}
        )
    ],
    className="px-2", style={'display': 'none'}
)

table_subtotal = html.Div(
    [
        html.Div("Show in the table:", style={"font-weight": "bold"}),
        dcc.RadioItems(
            id="table_subtotal",
            options=[
                {"label": "City/District totals only", "value": "city_totals"},
                {"label": "All Categories", "value": "all_cats"},
                {"label": "All Sub Categies", "value": "all_subcats"},
                
            ],
            value="city_totals",
            labelStyle={"display": "block"},
            labelClassName="m-2",
            inputClassName="mr-2",
        ),
    ],
    className="p-3 border",
)


#####################   Header Cards and Markdown #############################
first_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Card title", className="card-title"),
            html.P("This card has some text content, but not much else"),
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
        dbc.Container((navbar), fluid=True),        
        html.Div([
            dcc.Store(id='store_selected_cities', data=init_selected_cities),                  
            dcc.Store(id="store_city_exp_or_rev", data="expenditures"),
            dcc.Store(id='store_dff_exp', data=make_dff_exp_rev(init_selected_cities, 'expenditures')),
            dcc.Store(id='store_dff_rev', data=make_dff_exp_rev(init_selected_cities, 'revenue')),
            dcc.Store(id='store_clicked_on', data=None)
        ]),  
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
            

        #############  City selection  ###################

        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col( 
                            html.Div([
                               html.H5('Selected rows from table'),
                                html.Div(selected_cities_dropdown),
                            ],className="m-1 border"),
                            width={"size": 2, "order": 1, "offset": 1},
                           # className="mt-5 ",
                        ),
                        dbc.Col(
                            html.Div([                                
                                dcc.Loading(html.Div(select_city_tabulator)),
                            ]),
                            width={"size": 8, "order": 2},
                           # className=" bg-light",
                        ),                        
                    ]
                ),
            ]
        ),
       html.Div([
        ##################### city cards ###################################
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(  # controls
                            html.Div(
                                [exp_rev_button_group] 
                                + [year_slider],
                               
                                className="m-3 bg-white border",
                            ),
                            width={"size": 2, "order": 1},
                            className="mt-5",
                        ),
                        dbc.Col(
                            html.Div([
                                html.H2(id='city_cards_title', children=[],
                                       className='text-white',
                                ),
                                html.Div(id='city_cards_container', children=[])
                            ]),
                             width={"size": 10, "order": "last"}),
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
                                + [table_subtotal],
                                className="mt-5 mr-3 ml-3 p-2 border bg-white",
                            ),
                            width={"size": 2, "order": 1},
                           # className=" ",
                        ),
                        dbc.Col(
                            html.Div([
                                html.H5(id='city_table_title'),
                                html.Div(city_tabulator,
                                         className= 'mr-3'
                                         
                                ),
                            ]),
                            width={"size": 10, "order": 2},
                            className="mb-5",
                        ),                        
                    ]
                ),
            ]
        )
        ], className='bg-primary mr-5 ml-5'),
       html.Div(id='test'),
       ###########################   footer #########################
        html.Div(#footer
            [                
                dbc.Row(dbc.Col(html.Div(footer, className="border-top mt-5 small"))),
            ]            
        ),
    ],
    fluid=True,
)

#########################  Callbacks ##########################################

##### Update selected cities 
@app.callback(
   [       
       Output('store_selected_cities', 'data'),
       Output('selected_cities_dropdown', 'options'),     
       Output('selected_cities_dropdown', 'value'),
    ],
    [
        Input('select_city_tabulator', 'rowClicked'),        
    ],
     [
        State('store_selected_cities', 'data'),
        State('selected_cities_dropdown', 'value')
    ]
)
def update_selected_cities_data(tabulator_row, selected_cities_store, selected_cities_dd):  
   
    new_selection = []
    options =  [] 
     
    #TODO add state name to ID name... duplicate ID names in file ?
    if tabulator_row:
        selected_cities_store[tabulator_row['ID code']] = ', '.join([tabulator_row['ID name'] ,tabulator_row['ST']])
     
        if selected_cities_dd:
            if tabulator_row['ID code'] not in selected_cities_dd:
                selected_cities_dd.append(tabulator_row['ID code'])
        else:
            selected_cities_dd = [tabulator_row['ID code']]
    
    if selected_cities_store:      
        options = [{'label': name, 'value': code} for code, name in selected_cities_store.items()]        
   
    return selected_cities_store, options, selected_cities_dd


##### Update revenue and expense report for selected cities 
@app.callback(
   [       
       Output('store_dff_exp', 'data'),
       Output('store_dff_rev', 'data') 
    ],
    [
        Input('selected_cities_dropdown', 'value')     
    ]     
)
def update_selected_cities_data(selected_cities_dd):           
    return(
         make_dff_exp_rev(selected_cities_dd, 'expenditures'),
         make_dff_exp_rev(selected_cities_dd, 'revenue')
    )
    
 

######  Update revenue or expenses store
@app.callback(
    [
        Output("store_city_exp_or_rev", "data"),
        Output("city_category_dropdown", "value")
    ],
    [
        Input("city_expenditures", "n_clicks"), 
        Input("city_revenue", "n_clicks"),
     
    ],    
)
def update_exp_or_rev(exp, rev):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]   
    return "revenue" if input_id == "city_revenue" else "expenditures", None

##### updates sub category dropdown
@app.callback(
    [
        Output("city_subcategory_dropdown", "options"),
        Output("city_subcategory_dropdown", "value"),
        Output("city_category_dropdown", "options"),
        
    ],
    [
        Input("city_category_dropdown", "value"), 
        Input("store_city_exp_or_rev", "data"),  
       
    ],
)
def update_sub_category_dropdown(cat, exp_or_rev):

    report_cats = du.revenue_cats if exp_or_rev == "revenue" else du.expenditure_cats   
    
    cat_options = ([{"label": "All Categories", "value": "all"}] 
              + [{"label": c, "value": c} for c in report_cats])

    
    dff= df_summary[df_summary['Category'].isin(report_cats)]
    if (cat is None) or (cat == 'all'):
        subcat_options=([{"label": "All Sub Categories", "value": "all"}] 
               + [{"label": s, "value": s} for s in dff["Description"].unique()])
    else:        
        subcats = dff[dff["Category"] == cat]
        subcat_options = ([{"label": "All Sub Categories", "value": "all"}] 
                  + [{"label": s, "value": s} for s in subcats["Description"].unique()])
    return subcat_options, None, cat_options




#####  Update city table 
@app.callback(          
       Output('city_table', 'data'), 
    [   
        Input('store_city_exp_or_rev', 'data'),       
        Input('city_year', 'value'),
        Input("city_category_dropdown", "value"),
        Input("city_subcategory_dropdown", "value"),
        Input('table_subtotal', 'value'),
        Input('store_clicked_on', 'data'),
       
        Input('store_dff_exp', 'data'),
        Input('store_dff_rev', 'data'),       
    ],    
)
def update_city_table(exp_or_rev, year, cat, subcat, subtotal, clicked_on,  dff_exp, dff_rev): 
    
    if dff_exp == []:
        return '', []   

    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0] 
    
    categories = list(du.revenue_cats) + list(du.expenditure_cats)
      
    df_table = pd.DataFrame(dff_exp if exp_or_rev == 'expenditures' else dff_rev)   
   
    if input_id == 'store_clicked_on' and clicked_on:
        print('This:', clicked_on)
        if clicked_on in categories:
            cat = clicked_on
        elif df_table['ID name'].str.contains(clicked_on).any():
            cat= None
        else:
            subcat= clicked_on
            print(subcat)
        
        
        
    # filter        
   # if cat and (cat != 'all'):   # if dropdown
    if cat and (subtotal != 'all_cats'):     # if button
        df_table = df_table[df_table["Category"] == cat] 
        #   print('2', df_table.head(2))
  #  if subcat and (subcat != 'all'):  # if dropdown
    if subcat and (subtotal != 'all_subcats'): 
        df_table = df_table[df_table["Description"] == subcat]             
        #  print('3', df_table.head(2))
       
    # subtotal         
    #if subcat:
    if subcat or (subtotal == 'all_subcats'):
        df_table = (
            df_table.groupby(["ST", "ID code", "ID name", "Category", "Description"]).sum().reset_index()
        ) 
        # print('7', df_table.head(2))
   # elif cat: 
    elif cat or (subtotal == 'all_cats'):
        df_table = df_table.groupby(["ST","ID code", "ID name", "Category"]).sum().reset_index()
        # print('6', df_table.head(2))
    else: 
        df_table = df_table.groupby([ "ST", "ID code", "ID name"]).sum().reset_index()
        # print('5', df_table.head(2))
    


    # remove empty cols
    df_table = df_table.loc[:, (df_table != 0).any(axis=0)]        

    # add sparklines
    df_table["sparkline_Per Capita"] = make_sparkline(df_table, "Per Capita", YEARS)
       
    if any("Per Student" in s for s in df_table.columns):        
            df_table["sparkline_Per Student"] = make_sparkline(df_table, "Per Student", YEARS)
        
    # filter based on year slider
    df_table = year_filter(df_table, str(year))
          
   
    return df_to_data(df_table)



#####  Update city cards 
@app.callback(
   [       
       Output('city_cards_container', 'children'),  
       Output('city_cards_title', 'children'),
       Output('store_clicked_on', 'data')
    ],
    [   
        Input('store_city_exp_or_rev', 'data'),
        Input('selected_cities_dropdown', 'value'), 
        Input('city_year', 'value'),
        Input('store_dff_exp', 'data'),
        Input('store_dff_rev', 'data'),
        Input({'type': 'sunburst_output', 'index': ALL}, 'clickData'),
        Input('store_selected_cities', 'data')
    ],
)
def update_city_cards(exp_or_rev, selected_cities, year, dff_exp, dff_rev, clickData, city_dict): 
    if selected_cities == []:
        return [], [], None

    title_exp = ' Expenditures for selected cities, counties and districts'
    title_rev = ' Revenue for selected cities, counties or districts '
    title = str(year)+ title_exp   if exp_or_rev == 'expenditures' else str(year) + title_rev
    df_cards = pd.DataFrame(dff_exp if exp_or_rev == 'expenditures' else dff_rev)
    df_cards = year_filter(df_cards, str(year))
  
    categories = list(du.revenue_cats) + list(du.expenditure_cats)
    path =   ["ID name", "Category"] # default if no click data
    clicked_on = None

    # Find segment clicked on in sunburst
    input_id = dash.callback_context.triggered[0]['prop_id']    
    if 'index' in input_id:        
        ID_name = city_dict[input_id.split('"')[3]]       
        for points in clickData:           
            if points:
                print(points['points'][0])
                if ID_name==points['points'][0]['root']:
                    clicked_on = points['points'][0]['label']  
                    if (df_cards['ID name'] ==clicked_on).any():                        
                         path =   ["ID name", "Category"] # default if no click data
                         clicked_on = None
                        
                    elif (df_cards['Description'] ==clicked_on).any():
                        return  dash.no_update, dash.no_update, clicked_on
                    else:
                        path = ["ID name", "Description"]
                        title = title + ': ' + clicked_on

    children=[]
    for city_code in selected_cities:
        df_city = df_cards[df_cards['ID code'] == city_code]
        if clicked_on:
            df_city = df_cards[(df_cards['ID code'] == city_code) & (df_cards['Category'] == clicked_on)]
        new_element = html.Div(
            # style={'width': '25%', 'display': 'inline-block', 'outline': 'thin lightgrey solid', 'padding': 10},
            style={'width': '25%', 'display': 'inline-block', 'padding': 10},
            children=[
                dcc.Graph(
                    id={
                        'type': 'sunburst_output',
                        'index': city_code
                    },
                    style={'height': 200},
                    figure=make_sunburst(
                                    df_city,
                                    path, 
                                    df_city["Per Capita"],
                                    '',
                                ),
                ),
                html.Div(
                    id={'type':"state_stats", 'index': city_code},
                    children=make_stats_table(df_city)                           
                ),                           
            ]
        )
        children.append(new_element)
    return children, title, clicked_on




if __name__ == '__main__':
    app.run_server(debug=True)






########  update map and table  ##################################################\
#@app.callback(
#    [
#        Output("map", "figure"),
#        Output("table", "data"),
#        Output("sunburst_cat", "figure"),
#    ],
#    [
#        Input("store_exp_or_rev", "modified_timestamp"),
#        Input("year", "value"),
#        Input("state", "value"),
#        Input("category_dropdown", "value"),
#        Input("subcategory_dropdown", "value"),
#        Input("state_local_dropdown", "value"),
#        Input("table_subtotal", "value"),
#    ],
#    [State("store_exp_or_rev", "data")],
#)
#def update_map(__, year, state, cat, subcat, local, subtotal, exp_or_rev):

#    dff_map = df_rev if exp_or_rev == "Revenue" else df_exp
#    dff_table = dff_sunburst = dff_map.copy()
#    update_title = " ".join([str(year), exp_or_rev, "Per Capita by State"])
#    sunburst_title = " ".join([str(year), exp_or_rev, "Per Capita All States"])



#    # filter
#    if state != "USA":
#        dff_table = (
#            dff_table[dff_table["State"] == state]
#            if state
#            else dff_table[dff_table["State"] == "Alabama"]
#        )
#        dff_sunburst = dff_table.copy()
#        sunburst_title = " ".join([str(year), exp_or_rev, state])
#    if cat and subcat is None:
#        dff_table = dff_table[dff_table["Category"] == cat]
#        dff_map = dff_map[dff_map["Category"] == cat]
#        update_title = " ".join([str(year), exp_or_rev, cat])
#    if subcat:
#        dff_table = dff_table[dff_table["Description"] == subcat]
#        dff_map = dff_map[dff_map["Description"] == subcat]
#        update_title = " ".join([str(year), exp_or_rev, subcat])
#    if local:
#        dff_table = dff_table[dff_table["State/Local"] == local]
#        dff_map = dff_map[dff_map["State/Local"] == local]
#        update_title = " ".join([update_title, "and", local, "gvmt only"])

#    # subtotal
#    if subtotal == "state":
#        dff_table = dff_table.groupby(["State"]).sum().reset_index()
#    elif subtotal == "cat":
#        dff_table = dff_table.groupby(["State", "Category"]).sum().reset_index()
#    elif subtotal == "subcat":
#        dff_table = (
#            dff_table.groupby(["State", "Category", "Description"]).sum().reset_index()
#        )
#    elif subtotal == "local":
#        dff_table = (
#            dff_table.groupby(["State", "Category", "Description", "State/Local"])
#            .sum()
#            .reset_index()
#        )

#    dff_table["sparkline"] = make_sparkline(dff_table, "Per Capita", YEARS)
#    dff_table = table_yr(dff_table, str(year))

#    # update sunburst
#    figure = make_sunburst(
#        dff_sunburst,
#        ["Category", "Description", "State/Local"],
#        get_col("Amount", str(year)),
#        sunburst_title,
#    )

#    return (
#        make_choropleth(dff_map, update_title, state, str(year)),
#        dff_table.to_dict("records"),
#        figure,
#    )
















#    ################  Dash Table  ####################

#def make_table():

#     #column names
#    #  'ID code',	
#    # 'State',
#    #'ID name',						
#    #'County name',    		
#    #'Population',	
#    #'Enrollment',	
#    #'Function code for special districts',	
        
#    return html.Div(
#        [            
#            dash_table.DataTable(
#                id="table",
#                columns=[
#                    {"id": "State", "name": "State", "type": "text"},                    
#                    {"id": "County name", "name": "County", "type": "text"},                   
#                    {"id": "ID name", "name": "City/district", "type": "text"},
                                       
                    
#                    {
#                        "id": "Population",
#                        "name": "Population",
#                        "type": "numeric",
#                        "format": FormatTemplate.money(0),
#                    },
#                    {
#                        "id": "Enrollment",
#                        "name": "Enrollment",
#                        "type": "numeric",
#                        "format": FormatTemplate.money(0),
#                    },
#                    {"id": "Special districts", "name": "Special Districts1 ", "type": "text"},                     
#                ],        
               
#                data=df_Fin_GID.to_dict("records"),
#                sort_action="native",
#                sort_mode="multi", 
#                row_selectable='multi',
#                filter_action="native",
#                selected_rows=[],
                
               
               
#                style_table={
#                    "overflowY": "scroll",
#                    "border": "thin lightgrey solid",
#                    "maxHeight": "450px",
#                },
#                style_cell={
#                    "textAlign": "left",
#                    "font-family": "arial",
#                    "font-size": "16px",                               
#                },
#                 style_cell_conditional=[
#                    {"if": {"column_id": c}, "textAlign": "right"}
#                    for c in ["Population", "Enrollment"]
#                ],   
                 
                 
#                style_data_conditional=[
#                     {
#                        'if': {
#                            'state': 'active'  
#                        },
#                       'backgroundColor': 'rgba(150, 180, 225, 0.2)',
#                       'border': '1px solid blue',                      
#                    },
#                     {
#                        'if': {
#                            'state': 'selected'  
#                        },
#                       'backgroundColor': 'rgba(0, 116, 217, .03)',
#                       'border': '1px solid blue',                      
#                    },                  
                     
#                ]

#            )
#        ],
#        id="table_div",       
#    )    


 
################  Dash table - summary report output ##############################

#def make_table():

#    return html.Div(
#        [
#            dash_table.DataTable(
#                id="city_table",
#                columns=[
#                    {"id": "Year", "name": "Year", "type": "text"},
#                    {"id": "ST", "name": "ST", "type": "text"},
                    
#                    {"id": "ID name", "name": "City/District", "type": "text"},
#                    {"id": "Category", "name": "Category", "type": "text"},
#                    {"id": "Description", "name": "Sub Category", "type": "text"},                   
#                    {
#                        "id": "Amount",
#                        "name": "Total Amount",
#                        "type": "numeric",
#                        "format": FormatTemplate.money(0),
#                    },
#                    {
#                        "id": "Per Capita",
#                        "name": "Per Capita",
#                        "type": "numeric",
#                        "format": FormatTemplate.money(0),
#                    },
#                    {
#                        "id": "Per Student",
#                        "name": "Per Student",
#                        "type": "numeric",
#                        "format": FormatTemplate.money(0),
#                    },


#                    {
#                        "id": "Spark",
#                        "name": " ".join(["Per Capita/Student", YEARS[0], YEARS[-1]]),                                         
#                    },
#                ],
              
#                sort_action="native",
#                #row_selectable='multi',
#                sort_mode="multi",
#                filter_action="native",
#                export_format="xlsx",
#                export_headers="display",
#                style_table={
#                    "overflowY": "scroll",
#                    "border": "thin lightgrey solid",
#                    "maxHeight": "450px",
#                },
#                style_cell={
#                    "textAlign": "left",
#                    "font-family": "arial",
#                    "font-size": "16px",
#                },
#                style_cell_conditional=[
#                    {"if": {"column_id": c}, "textAlign": "right"}
#                    for c in ["Per Capita", "Amount", "Per Student", "Spark"]
#                ],
#                style_data_conditional=[
#                    {
#                        "if": {"state": "active"},
#                        "backgroundColor": "rgba(150, 180, 225, 0.2)",
#                        "border": "1px solid blue",
#                    },
#                    {
#                        "if": {"state": "selected"},
#                        "backgroundColor": "rgba(0, 116, 217, .03)",
#                        "border": "1px solid blue",
#                    },
#                    {
#                        "if": {"column_id": "Spark"},
#                        "width": 100,
#                        "font-family": "Sparks-Bar-Extrawide",
#                        "padding-right": "20px",
#                        "padding-left": "20px",
#                    },
#                ],
#            )
#        ],       
#    )

########################  Figures #########################################
#mycity_sunburst = html.Div(
#    [
#        dcc.Graph(
#            id="sunburst_mystate",
#            figure=make_sunburst(
#                df_exp[df_exp["State"] == "Arizona"],
#                ["State", "Category"],
#                get_col("Amount", START_YR),
#                "START_YR My State",
#            ),
#            style={"height": "225px"},
#        ),
#        html.Div(
#            id="mystate_stats",
#            children=make_stats_table(
#                int(df_pop.loc[df_pop["State"] == "Arizona", int(START_YR)]),
#                df_exp[df_exp["State"] == "Arizona"],
#                1,
#                START_YR,
#            ),
#        ),
#    ],
#    className="border",
#)
#year_slider = html.Div(
#    [       
#        dcc.Slider(
#            id="city_year",
#            min=int(min(YEARS)),
#            max=int(max(YEARS)),
#            step=1,           
#            marks={
#                int(year): {"label": year, "style": {"writing-mode": "vertical-rl"}}
#                for year in YEARS
#            },
#            value=int(START_YR),
#            className="mt-3  p-3 mb-5",
#        )
#    ]
#)


#city_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="city_dropdown",
#            options =[{"label": "All slected cities", "value": "all"}],
#            value = 'all',
#            clearable=False,
#            className="mt-2",
#        )
#    ],
#    className="px-2",
#)
#mycity_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="mycity",
#            #options=[{"label": state, "value": state} for state in df_pop["State"]],
#            #value="Arizona",
#            #clearable=False,
#        )
#    ],
#    className="px-2",
#)


# This initializes the summary dictionary with line number and description only.
# Cities are added to the df_summary as columns when selected from the table,
#   -- note the columns are added in a callback using the add_city(..) function
# the summary dictionary has one df_summary for each year
#summary = {year: df_summary[['Line', 'Description']] for year in YEARS}

#def add_city(city_idcode, year):
#    ''' Adds a city column to the df_summary from the individual unit data file '''
   
#    df_fin = fin[year]  
#    df_fin = df_fin[df_fin['ID code'] == str(city_idcode)]

#    city_column = []
#    for line in summary_dict:
#        df_line= df_fin[df_fin['Item code'].isin(summary_dict[line])]
#        city_column.append(df_line['Amount'].sum())
#    return city_column


#def make_df_report(df, year, report):
#    """  Make df for a single year of a report.   The report is summarized based on categories
#        as defined in data_utilities.py
    
#        This creates a df of expenditure or revenue categories consitant with:
#        https://www.census.gov/library/visualizations/interactive/state-local-snapshot.html
#        This is a helper function to create the complete expenditure dataset for all years

#     Args:  
#        df (dataframe) : created from dff_summary for a year
#        year  (int)  :  4 digit year
#        report (str) : type of report

#    Returns:
#        A dataframe in a shape needed for the sunburst and treemap charts for a single year
#    """

#    if report == "revenue":
#        report_cats = du.revenue_cats
#    elif report == "expenditures":
#        report_cats = du.expenditure_cats
      
#    # add report categories to the summary df
#    dff = df.copy()
#    for cat in report_cats:
#        for line_no in report_cats[cat]:
#            dff.loc[dff[("Line")] == line_no, "Category"] = cat

#    # create a subset df that is only report categories 
#    dff = dff.dropna(subset=[("Category")])
#    df_report = pd.melt(
#                dff,
#                id_vars=["Line", "Category", "Description"],
#                var_name="ID code",
#                value_name="Amount",
#            )
   
#    df_report = df_report[df_report['Amount'] > 0]

#    # add columns from df_Fin_GID
#    df_report = df_report.merge(Fin_GID[year], on="ID code")
#    columns = ['Line', 'Category', 'Description', 'ST', 'ID name', 'Amount', 'ID code', 'Population', 'Enrollment']
#    df_report = df_report[columns]   

#    df_report['Per Capita'] = (df_report['Amount'] / df_report['Population'] * 1000).fillna(0).replace([np.inf, -np.inf], 0)
#    df_report['Per Student'] = (df_report['Amount'] / df_report['Enrollment'] * 1000).fillna(0).replace([np.inf, -np.inf], 0)
#    df_report['Year'] = year
      
#    return df_report


###### updates sub category dropdown
#@app.callback(
#    [
#        Output("city_subcategory_dropdown", "options"),
#        Output("city_subcategory_dropdown", "value"),
#    ],
#    [
#        Input("city_category_dropdown", "value"), 
#        Input("store_city_exp_or_rev", "data"),
#        Input("store_selected_cities", "data")
     
#     ],

#  #  [State('store_df_exp', 'data'), State('store_df_rev', 'data')]
#)
#def update_sub_category_dropdown(cat, exp_or_rev, __):    

#  #TODO -make a global list of cats and subcats to use instead of recalc each time????

#   # dff = pd.dataframe(df_exp) if exp_or_rev == "expenditures" else pd.dataframe(df_rev)
#    dff = df_exp
#    if exp_or_rev == "revenue":    
#        dff = df_rev
       
#    if cat is None:
#        options = [{"label": s, "value": s} for s in dff["Description"].unique()]
#    else:
#        df_subcats = dff[dff["Category"] == cat]       
#        options = [{"label": s, "value": s} for s in df_subcats["Description"].unique()]

#    return options, None


###### updates city dropdown
#@app.callback(
#    [
#        Output("city_dropdown", "options"),
#        Output("city_dropdown", "value"),
#    ],
#    [  
#        Input('selected_cities_dropdown', 'value'), 
#        Input('selected_cities_dropdown', 'options'),  
#     ],   
#     [
#         State("city_dropdown", "value"),
#     ]
#)
#def update_city_dropdown(selected_values, selected_options, current_value):        
#    if selected_values:
#        options=(
#            [{"label": "All slected cities", "value": "all"}] 
#            + [option for option in selected_options if option['value'] in selected_values]
#        )
#        value = current_value
#    else:
#         options= [{"label": "All slected cities", "value": "all"}] 
#         value = 'all'    
#    return options, value
   

#category_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="city_category_dropdown",
#            #options=[{"label": c, "value": c} for c in df_exp["Category"].unique()],
#            placeholder="Select a category",
#        )
#    ],
#    className="px-2",
#)

#sub_category_dropdown = html.Div(
#    [
#        dcc.Dropdown(
#            id="city_subcategory_dropdown",
#           # options=[{"label": c, "value": c} for c in df_exp["Description"].unique()],
#            placeholder="Select a sub category",
#            style={'font-size' : '90%'}
#        )
#    ],
#    className="px-2",
#)
