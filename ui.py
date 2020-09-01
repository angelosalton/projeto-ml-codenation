import base64
import io

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import pandas as pd
import requests
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from api import server

# url
app_url = 'localhost'
app_port = '8050'

# declara o aplicativo
app = dash.Dash(
    __name__,
    server=server,
    # routes_pathname_prefix='/welcome/',
    external_stylesheets=[dbc.themes.FLATLY]
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

welcome = dcc.Markdown('''
    # Seja bem vindo!

    lalalala...

    eaeaaeeaeaea....
    ''')

_styles = {'style':
           {'padding-left': '1em',
            'padding-right': '1em'}
           }

options = dbc.Card([
    # recomendações
    dbc.FormGroup([
        dbc.Label('Número de recomendações'),
        dbc.Input(id='input-recommends', type='number',
                  min=1, max=100, value=10),
    ], **_styles),
    # portfolio
    dbc.FormGroup([
        dbc.Label('Selecione o portfólio de empresas'),
        dcc.Dropdown(
            id='dropdown-portfolio',
            options=[
                {'label': 'Exemplo 1', 'value': 'ex1'},
                {'label': 'Exemplo 2', 'value': 'ex2'},
                {'label': 'Exemplo 3', 'value': 'ex3'},
                {'label': 'Personalizado', 'value': 'custom'}
            ],
            value='ex1',
            searchable=False,
            clearable=False
        )
    ], **_styles),
    # inserir portfolio personalizado
    dbc.FormGroup([
        dcc.Upload(
            id='upload-data',
            children=dbc.Button('Carregar arquivo', outline=True, color='dark')
        )
    ], **_styles),
    # atualizar dados
    dbc.FormGroup([
        dbc.Button('Atualizar portfólio', id='btn-portfolio')
    ], **_styles),
    # gerar recomendações
    dbc.FormGroup([
        dbc.Button('Gerar recomendações', id='btn-update')
    ], **_styles)
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
    dcc.Store('ids-store', storage_type='session'),
    dcc.Store('recommends-store', storage_type='session'),
    # alertas
    # dbc.Alert("Dados carregados com sucesso!", color="success", fade=True, duration=3000),
    # dbc.Alert("Erro na carga dos dados!", color="danger", fade=True, duration=3000),
    # inicio da pagina
    welcome,
    dbc.Row([
        # barra lateral
        dbc.Col([
            options
        ], md=3),
        # corpo da pagina
        dbc.Col([
            dbc.Row([
                dcc.Loading([
                    view_portfolio
                ])
            ]),
            dbc.Row([
                dcc.Loading([
                    view_recommends
                ])
            ])
        ], md=9)
    ])
])

# funções auxiliares --------------------------------------


def _print_table(df_json):
    '''
    Função auxiliar que retorna uma tabela dos dados informados.
    '''
    df = pd.read_json(df_json)
    df = df[['id', 'sg_uf', 'nm_segmento']]

    return dt.DataTable(
        data=df.to_dict(orient='records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        editable=True,
        style_cell={
            'fontSize': 11
        },
        page_size=10
    )


def parse_contents(contents, filename):
    '''
    Faz a leitura do arquivo *.csv.
    '''
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


# callbacks -----------------------------------------------

# TODO: selecionador de portfolio
@app.callback(
    [Output('ids-store', 'data'),
     Output('upload-data', 'style')],
    [Input('btn-portfolio', 'n_clicks')],
    [State('dropdown-portfolio', 'value')])
def select_portfolio(clicks, value):
    '''
    Seleciona o portfolio, retornando a lista de ids para o cache.
    '''
    if value != 'custom':
        ids = {'ids': pd.read_csv(
            f'data/estaticos_portfolio{value[2]}.csv')['id'].tolist()}
        style = {'display': 'none'}

    else:
        ids = {'ids': None}
        style = {'display': 'block'}

    return ids, style


# visualizador portfolio

@app.callback(
    Output('table-portfolio', 'children'),
    [Input('btn-portfolio', 'n_clicks')],
    [State('ids-store', 'data')])
def print_portfolio(clicks, ids):
    '''
    Visualiza o portfólio.
    '''
    if ids is None:
        return html.Div([
            html.H4('Seu portfólio'),
            html.P('Selecione.')
        ])

    # requisição API
    req = requests.post(f'http://{app_url}:{app_port}/get_table',
                        json={'ids': ids['ids']})

    # verifica a resposta
    if req.status_code != 200:
        return html.P('Selecione um portfolio..')

    return html.Div([
        html.H4('Seu portfólio'),
        _print_table(req.json()['data'])
    ])


@app.callback(
    Output('table-recommends', 'children'),
    [Input('btn-update', 'n_clicks')],
    [State('input-recommends', 'value'),
     State('ids-store', 'data')])
def print_recommends(clicks, n_rec, ids_json):
    '''
    Visualiza as empresas recomendadas.
    '''
    if ids_json is None:
        return html.Div([
            html.H4('Recomendações'),
            html.P('Carregue um portfólio e clique em Gerar Recomendações.')
        ])

    # requisição API
    req = requests.post(f'http://{app_url}:{app_port}/predict',
                        json={'ids': ids_json, 'n_rec': n_rec})

    # verifica a resposta
    if req.status_code != 200 or req.json()['status'] != 'Sucesso':
        return html.Div([
            html.H4('Recomendações'),
            html.P('Não há recomendações disponíveis.')
        ])

    return html.Div([
        html.H4('Recomendações'),
        _print_table(req.json()['data'])
    ])


# script
if __name__ == '__main__':
    app.run_server(host=app_url, port=app_port, debug=True)
