from flask import Flask

server = Flask(__name__)


@server.route("/")
def hello_world():
    return "Hello from test Flask!"


import sys

print(sys.version)
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from page import state, historic


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/page/state":
        return state.layout
    elif pathname == "/page/about":
        return historic.layout
    elif pathname == "/page/wealth":
        return historic.layout
    else:
        return state.layout


if __name__ == "__main__":
    app.run_server(debug=True)


#
# ####################
#
#
# from flask import Flask
#
# server = Flask(__name__)
#
# @server.route('/')
# def hello_world():
#     return 'Hello from test Flask!'
#
# import sys
# print(sys.version)
# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output
#
# from app import app, navbar
# from page import state, historic
#
#
#
# url_bar_and_content_div = html.Div([
#     dcc.Location(id='url', refresh=False),
#     html.Div(id='page-content')
# ])
#
# layout_index= navbar
# layout_page_1 = state.layout
# layout_page_2 = historic.layout
#
# # index layout
# app.layout = url_bar_and_content_div
#
# # "complete" layout
# app.validation_layout = html.Div([
#     url_bar_and_content_div,
#     layout_index,
#     layout_page_1,
#     layout_page_2,
# ])
#
#
#
#
# @app.callback(Output('page-content', 'children'),
#               [Input('url', 'pathname')])
# def display_page(pathname):
#     if pathname == '/page/state':
#         return state.layout
#     elif pathname == '/page/about':
#         return historic.layout
#     elif pathname == '/page/wealth':
#         return historic.layout
#     else:
#         return state.layout
#
# if __name__ == '__main__':
#     app.run_server(debug=True)
#
