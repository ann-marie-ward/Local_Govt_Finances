
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc

external_stylesheets = [
   dbc.themes.SPACELAB,
  #  'https://www.w3schools.com/w3css/4/w3.css',
 # 'https://codepen.io/chriddyp/pen/bWLwgP.css' ,     
 #    'mycss.css'
    
    #{
    #    'href': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css',
    #    'rel': 'stylesheet',
    #}
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)



server = app.server
app.config.suppress_callback_exceptions = True

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("State & Local", href="/page/budget")),
        dbc.NavItem(dbc.NavLink("City/District", href="/page/city_budget")),
        dbc.NavItem(dbc.NavLink("Upload Data", href="/page/upload")),   
        dbc.NavItem(dbc.NavLink("About", href="/page/about")),
    ],
    brand="Understanding State and Local Government Finances",   
    brand_href="/page/budget",
    color="primary",
    dark=True,
   # className= 'float-right d-block sticky-top',
)


footer = html.Div(
    dcc.Markdown( 

    '''
Source: U.S. Census Bureau, 2017 Annual Surveys of State and Local Government Finances. Data users who create their own estimates using data from this report 																																																																																																																																		
should cite the U.S. Census Bureau as the source of the original data only. The data in this table are based on information from public records and contain no confidential data. 																																																																																																																																		
The state government data in this table are from a survey of all state governments and are not subject to sampling error.  The 2017 local government data in this table are from 																																																																																																																																		
a sample of local governments, and as such, are subject to sampling variability.  Additional information on sampling and nonsampling error, response rates, and definitions																																																																																																																																		
may be found at:																																																																																																																																		
http://www2.census.gov/govs/state/17_methodology.pdf		and	http://www2.census.gov/govs/local/2017_local_finance_methodology.pdf																																																																																																																															

    '''
    )
)

