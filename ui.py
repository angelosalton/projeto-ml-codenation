from api import server

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


app = dash.Dash(
    __name__,
    server=server,
    routes_pathname_prefix='/welcome/'
)

app.layout = html.Div('Teste!')

# script
if __name__ == '__main__':
    app.run_server(debug=False)
