
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc


# 3rd party js to export as xlsx for Tabulator
external_scripts = ['https://oss.sheetjs.com/sheetjs/xlsx.full.min.js']

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

external_stylesheets = [
   dbc.themes.SPACELAB, FONT_AWESOME
 # 'https://codepen.io/chriddyp/pen/bWLwgP.css' ,    
]

app = dash.Dash(__name__, external_scripts=external_scripts, external_stylesheets=external_stylesheets, 
                meta_tags=[{"name": "viewport", "content": "width=device-width", "initial-scale" :1,}])



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



footer = html.Div([
    dcc.Markdown( 

    '''
***Data Source: U.S. Census Bureau Annual Surveys of State and Local Government Finances. ***

Data users who create their own estimates using data from this report 																																																																																																																																		
should cite the U.S. Census Bureau as the source of the original data only. The data in this table are based on information from public records and contain no confidential data. 																																																																																																																																		
The state government data in this table are from a survey of all state governments and are not subject to sampling error.  The local government data in this table are from 																																																																																																																																		
a sample of local governments, and as such, are subject to sampling variability. 

Additional information on sampling and nonsampling error, response rates, and definitions																																																																																																																																		
may be found at:																																																																																																																																		
http://www2.census.gov/govs/state/17_methodology.pdf		and	http://www2.census.gov/govs/local/2017_local_finance_methodology.pdf																																																																																																																															


*** Data Source for city markers:  https://simplemaps.com/data/us-zips
    '''
    ),
    html.H4(['Questions, comments or feedback are welcome! ', 
            html.A('email', href='mailto:awardapps@fastmail.com?subject=cool')]),
    


], className='m5 p-5')

################################   Temp  to run wealthdashboard book app here  ###################


navbar3 = dbc.NavbarSimple(
    [
        dbc.NavItem(dbc.NavLink('Historic Returns', href="/page/historic")),
        dbc.NavItem(dbc.NavLink('Stock Quotes', href="/page/quotes")),
        dbc.NavItem(dbc.NavLink('About', href="/page/about")),        
    ],
    brand="Wealth Management Dashboard",
    brand_style={'font-size':'x-large'},
    brand_href="#",
    color="primary",
    fluid=True,
    dark=True,
)


footer3 = html.Div(
        dcc.Markdown( 
        '''
         This information is intended solely as general information for educational
        and entertainment purposes only and is not a substitute for professional advice and
        services from qualified financial services providers familiar with your financial
        situation.

         Questions?  Suggestions? Please don't hesitate to get in touch: [Email](mailto:awardapps@fastmail.com?subject=cool)
        '''
        ),       
        className='m5 pl-5 pr-5 bg-primary text-white'
)


 

######## Markdown content 


asset_allocation_text =  dcc.Markdown(
        """
        **Asset allocation** is one of the main factors that determines your portfolio returns
        and volatility over time.  Play with the app and see for yourself!

        See "My Portfolio",   the dashed line in the graph, and watch how
        your results change as you move the sliders to select different asset
        allocations. You can enter different starting times and dollar amounts too.
        """
    )


backtesting_text = dcc.Markdown(
        """
      
        Past performance certainly does not determine future results.... but you can still
        learn a lot by reviewing how various asset classes have performed over time.

        Use the sliders to change the asset allocation (how much you invest in cash vs
        bonds vs stock) and see how this affects your returns.

        Note that the results shown in "My Portfolio" assumes rebalancing was done at
        the beginning of every year.  Also, this information is based on the S&P 500 index
        as a proxy for "stocks", the 10 year US Treasury Bond for "bonds" and the 3 month
        US Treasury Bill for "cash."  Your results of course,  would be different based
        on your actual holdings.

        This is intended to help you determine your investment philosophy and understand
        what sort of risks and returns you might see for each asset category.

        The  data is from [Aswath Damodaran](http://people.stern.nyu.edu/adamodar/New_Home_Page/home.htm)
        who teaches  corporate finance and valuation at the Stern School of Business
        at New York University.

        Check out his excellent on-line course in
        [Investment Philosophies.](http://people.stern.nyu.edu/adamodar/New_Home_Page/webcastinvphil.htm)
        """
    )

