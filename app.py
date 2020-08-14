
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc


# 3rd party js to export as xlsx for Tabulator
external_scripts = ['https://oss.sheetjs.com/sheetjs/xlsx.full.min.js']


external_stylesheets = [
   dbc.themes.SPACELAB, 
 # 'https://codepen.io/chriddyp/pen/bWLwgP.css' ,    
]

app = dash.Dash(__name__, external_scripts=external_scripts, external_stylesheets=external_stylesheets, )

server = app.server
app.config.suppress_callback_exceptions = True


navbar = html.Div([
    dbc.Row(
                [
                    dbc.Col(
                        html.H3('Exploring Government Finances', className ='text-white'),         
                        width={"size": 3, "order": 1, "offset": 1},
                        
                    ),
                    dbc.Col(
                        html.H4(dcc.Link('State', href="/page/state", className ='text-white') ),       
                        width={"size": 1, "order": 10, "offset": 4},
                    ),
                    dbc.Col(
                        html.H4(dcc.Link('Local', href="/page/local", className ='text-white')),   
                      
                        width={"size": 1, "order": 11,},
                    ),
                    dbc.Col(
                        html.H4(dcc.Link('About', href="/page/about", className ='text-white')),       
                        width={"size": 1, "order": 12,},
                    )
                ], 
                no_gutters=True,                
                className ='bg-primary p-3',
                
    ), 
])



#navbar = dbc.NavbarSimple(
#    children=[
#        dbc.NavItem(dbc.NavLink("State", href="/page/budget")),
#        dbc.NavItem(dbc.NavLink("Local", href="/page/city_budget")),
#     #   dbc.NavItem(dbc.NavLink("Upload Data", href="/page/upload")),   
#        dbc.NavItem(dbc.NavLink("About", href="/page/about")),
       
#    ],
#    brand="Exploring Government Finances",   
#    brand_href="/page/budget",
#    color="primary",
#    dark=True,
#    sticky="top",
#    className= 'nav justify-content-right large',
#)





footer = html.Div([
    dcc.Markdown( 

    '''
Source: U.S. Census Bureau Annual Surveys of State and Local Government Finances. Data users who create their own estimates using data from this report 																																																																																																																																		
should cite the U.S. Census Bureau as the source of the original data only. The data in this table are based on information from public records and contain no confidential data. 																																																																																																																																		
The state government data in this table are from a survey of all state governments and are not subject to sampling error.  The local government data in this table are from 																																																																																																																																		
a sample of local governments, and as such, are subject to sampling variability.  Additional information on sampling and nonsampling error, response rates, and definitions																																																																																																																																		
may be found at:																																																																																																																																		
http://www2.census.gov/govs/state/17_methodology.pdf		and	http://www2.census.gov/govs/local/2017_local_finance_methodology.pdf																																																																																																																															

    '''
    ),
    html.H4(['Questions, comments or feedback are welcome! ', 
            html.A('email', href='mailto:awardapps@fastmail.com?subject=cool')]),
    


], className='m5 p-5')

