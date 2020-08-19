from api import server

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import base64
import io
import pandas as pd

# declara o aplicativo
app = dash.Dash(
    __name__,
    server=server,
    # routes_pathname_prefix='/welcome/',
    external_stylesheets=[dbc.themes.PULSE]
)

# layout
navbar = dbc.Navbar([
    dbc.Row([
        dbc.NavbarBrand('projeto-ml-codenation', className='ml-2'),
        html.A([
            html.Img(
                src='https://img.shields.io/github/stars/angelosalton/projeto-ml-codenation', height='20px')
        ],
            href='https://github.com/angelosalton/projeto-ml-codenation/')
    ],
        align='center',
        no_gutters=True)
],
    color='dark',
    dark=True
)

welcome = dbc.Row([
    dcc.Markdown('''
    # Seja bem vindo!

    lalalala...
    ''')
])


options = dbc.Row([
    html.H4('Parâmetros'),
    # recomendações
    html.P('Número de recomendações'),
    dbc.Input(id='input-recomendacoes', type='number',
              min=1, max=100, value=10),
    # portfolio
    html.P('Selecione o portfólio de empresas'),
    dcc.Dropdown(
        id='dropdown-portfolio',
        options=[
            {'label': 'Exemplo 1', 'value': 'ex1'},
            {'label': 'Exemplo 2', 'value': 'ex2'},
            {'label': 'Exemplo 3', 'value': 'ex3'},
            {'label': 'Personalizado', 'value': 'custom'}
        ],
        value='ex1'
    ),
    # inserir portfolio personalizado
    html.Div(id='btn-upload'),
    # gerar recomendações
    html.P(),
    dbc.Button('Gerar recomendações', id='btn-update')
])

view_portfolio = dbc.Row([
    html.Div(id='table-portfolio')
])

view_recommends = dbc.Row([
    html.Div(id='table-recommends')
])

app.layout = dbc.Container([
    # barra superior
    navbar,
    # data stores
    dcc.Store(id='data-store', storage_type='session'),
    dcc.Store(id='recommends-store', storage_type='session'),
    # alertas
    #dbc.Alert("Carga completa!", color="primary", fade=True, duration=3000),
    # inicio da pagina
    dbc.Row([
        # barra lateral
        dbc.Col([
            options
        ], md=3),
        # corpo da pagina
        dbc.Col([
            welcome,
            dcc.Loading([
                view_portfolio
            ]),
            dcc.Loading([
                view_recommends
            ])
        ], md=9)
    ])
])


# callbacks

# inserir portfolio personalizado
@app.callback(
    Output('btn-upload', 'children'),
    [Input('dropdown-portfolio', 'value')])
def upload_portfolio(value):
    '''
    Abre opção de carregar arquivo se portfolio customizado for escolhido.
    '''
    if value == 'custom':
        return html.Div([
            dcc.Upload(
                id='upload-portfolio',
                children=dbc.Row([
                    html.A('Upload *.csv')
                ]),
                multiple=False
            ),
        ])
    else:
        return html.Div()

# carrega arquivo portfoio
def parse_contents(contents, filename):
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # assume que o usuário carregou um arquivo *.csv
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        else:
            return None

    except Exception as e:
        print(e)
        return None

    return df.to_json(orient='records')


@app.callback(Output('data-store', 'data'),
              [Input('upload-portfolio', 'contents')],
              [State('upload-portfolio', 'filename'),
               State('data-store', 'data')])
def update_output(list_of_contents, list_of_names, data):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        return children


# TODO: chamada do modelo

# visualizador portfolio
def _print_table(ts, clicks, df_json):
    '''
    Função auxiliar que retorna uma tabela dos dados em cache.
    '''
    if df_json is None:
        raise PreventUpdate

    df = pd.read_json(df_json, orient='records')

    return dt.DataTable(
        data=df.to_dict(orient='records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        editable=True,
        style_cell={
            'fontSize': 12,
            'font-family': 'Roboto',
            'maxWidth': '40px'
        }
    )

# visualiza portfolio


@app.callback(
    Output('table-portfolio', 'children'),
    [Input('data-store', 'modified_timestamp'),
     Input('btn-update', 'n_clicks')],
    [State('data-store', 'data')])
def print_portfolio(ts, clicks, df_json):
    return _print_table(ts, clicks, df_json)

# visualizador recomendações


@app.callback(
    Output('table-recommends', 'children'),
    [Input('recommends-store', 'modified_timestamp'),
     Input('btn-update', 'n_clicks')],
    [State('recommends-store', 'data')])
def print_recommends(ts, clicks, df_json):
    return _print_table(ts, clicks, df_json)


# script
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port='8050')
