import dash_tabulator
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from textwrap import dedent as d
import json

# 3rd party js to export as xlsx
external_scripts = ['https://oss.sheetjs.com/sheetjs/xlsx.full.min.js']

# bootstrap css
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css']

# initialize your dash app as normal
app = dash.Dash(__name__, external_scripts=external_scripts, external_stylesheets=external_stylesheets)

styles = {
            'pre': {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll'
            }
        }

# Setup some columns 
# This is the same as if you were using tabulator directly in js 
columns = [
                {"formatter":"printIcon",  "width": 150, "hozAlign":"center"},
                { "title": "Name", "field": "name", "width": 150, "headerFilter":True},


         # If I wanted to use this conditional formatting for the "Name" columns, how would I do it?

                #{"title":"Name", field:"name", "width":150, "formatter":function(cell, formatterParams){
                #    var value = cell.getValue();
                #    if(value.indexOf("o") > 0){
                #        return "<span style='color:red; font-weight:bold;'>" + value + "</span>";
                #    }else{
                #        return value;
                #    }
                #}},


                { "title": "Age", "field": "age", "hozAlign": "left", "formatter": "progress" },
                { "title": "Favourite Color", "field": "col", "headerFilter":True },
                { "title": "Date Of Birth", "field": "dob", "hozAlign": "center" },
                { "title": "Rating", "field": "rating", "hozAlign": "center", "formatter": "star" },
                { "title": "Passed?", "field": "passed", "hozAlign": "center", "formatter": "tickCross" }
              ]

# Setup some data
data = [
                {"id":1, "name":"Oli Bob", "age":"12", "col":"red", "dob":""},
                {"id":2, "name":"Mary May", "age":"1", "col":"blue", "dob":"14/05/1982"},
                {"id":3, "name":"Christine Lobowski", "age":"42", "col":"green", "dob":"22/05/1982"},
                {"id":4, "name":"Brendon Philips", "age":"125", "col":"orange", "dob":"01/08/1980"},
                {"id":5, "name":"Margret Marmajuke", "age":"16", "col":"yellow", "dob":"31/01/1999"},
                {"id":6, "name":"Fred Savage", "age":"16", "col":"yellow", "rating":"1", "dob":"31/01/1999"},
                {"id":6, "name":"Brie Larson", "age":"30", "col":"blue", "rating":"1", "dob":"31/01/1999"},
              ]

# Additional options can be setup here 
# these are passed directly to tabulator
# In this example we are enabling selection
# Allowing you to select only 1 row
# and grouping by the col (color) column 

options = { "groupBy": "col", "selectable":1}

# downloadButtonType
# takes 
#       css     => class names
#       text    => Text on the button
#       type    => type of download (csv/ xlsx / pdf, remember to include appropriate 3rd party js libraries)
#       filename => filename prefix defaults to data, will download as filename.type

downloadButtonType = {"css": "btn btn-primary", "text":"Export", "type":"xlsx"}


# Add a dash_tabulator table
# add empty columns and data arrays to setup the react props
# columns=[],
# data=[], 
# not doing will give you ugly recursive errors
# and nothing will work

app.layout = html.Div([
    dash_tabulator.DashTabulator(
        id='tabulator',
        columns=[],
        data=[],
        options=options,
        downloadButtonType=downloadButtonType,
    ),
    html.Div(id='output'),
    dcc.Interval(
                id='interval-component-iu',
                interval=1*10, # in milliseconds
                n_intervals=0,
                max_intervals=0
            )

])


# dash_tabulator can be populated from a dash callback
@app.callback([ Output('tabulator', 'columns'), 
                Output('tabulator', 'data')],
                [Input('interval-component-iu', 'n_intervals')]) 
def initialize(val):
    return columns, data

# dash_tabulator can register a callback on rowClicked 
# to receive a dict of the row values
@app.callback(Output('output', 'children'), [Input('tabulator', 'rowClicked')])
def display_output(value):
    print(value)
    return 'You have entered {}'.format(value)


if __name__ == '__main__':
    app.run_server(debug=True)
