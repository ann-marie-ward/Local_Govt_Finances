
from flask import Flask

server = Flask(__name__)

@server.route('/')
def hello_world():
    return 'Hello from test Flask!'

import sys
print(sys.version)


import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from page import  state_local, historic

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page/local':
        return state_local.layout
    elif pathname == '/page/state':
        return state_local.layout
    elif pathname == '/page/about':
        return historic.layout
    elif pathname == '/page/wealth':
        return historic.layout
    else:
        return state_local.layout

if __name__ == '__main__':
    app.run_server(debug=True)
   
