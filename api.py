import logging
from datetime import datetime

import pandas as pd
import requests
from flask import Flask, jsonify, request
from flask_caching import Cache
from joblib import load

#from ui import app_port, app_url
app_url = 'localhost'
app_port = '8050'

# carrega modelo
model = load('model.joblib')

# carrega banco de dados de empresas
db = pd.read_parquet('data/estaticos_market.parquet')

# inicializa log
logger = logging.Logger('root')

# configura cache
cache = Cache(config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/data/cache.tmp'
})

# inicializa API
server = Flask(__name__)
cache.init_app(server)


@server.route('/hello')
def hello():
    return 'Olá, mundo!'


@server.route('/get_table', methods=['POST'])
@cache.memoize(50)
def get_table():
    '''Retorna dados de empresas de acordo com os ids.

    :return: Um DataFrame pandas.
    :rtype: pd.DataFrame
    '''
    request_raw = request.get_json(force=True)
    ids = request_raw['ids']

    left = pd.DataFrame(ids, columns=['id'])

    # prepara saída
    output = {}

    # consulta o portfolio no banco de dados de mercado
    try:
        db_subset = pd.merge(left, db, on='id')

        # dataframe não vazio
        if db_subset.shape[0] != 0:
            output['status'] = 'Sucesso'
            output['data'] = db_subset.to_json(orient='records')
            logger.info(
                f'Em {datetime.now().isoformat()}: Consulta ao banco de dados de empresas: {db_subset.shape[0]} valores retornados.')

        # dataframe vazio
        else:
            output['status'] = 'Falha'
            output['data'] = None
            logger.error(
                f'Em {datetime.now().isoformat()}: Nenhuma empresa do portfolio encontrada.')

    except Exception as e:
        output['status'] = 'Falha'
        output['data'] = None
        logger.error(f'Em {datetime.now().isoformat()}: {e.args}')

    return jsonify(output)


@server.route('/predict', methods=['POST'])
@cache.memoize(50)
def predict():
    '''Retorna as previsões do modelo.

    :return: JSON com as ids de empresas previstas.
    :rtype: dict
    '''
    # leitura da request
    request_raw = request.get_json(force=True)
    ids = request_raw['ids']
    n_rec = request_raw['n']

    # consulta os dados (via request a get_table)
    request_data = requests.post(
        url=app_url+'/get_table',
        data={'ids': ids}
    )

    # leitura dos dados
    db_subset = request_data.json()['data']

    # inicializa JSON de saída
    output = {}

    def recommendations(ids: list, n: int):
        '''
        Obtém as previsões do modelo.
        '''
        distances, indexes = model.named_steps['model'].kneighbors(
            model.named_steps['data_tr'].transform(db_subset), n)

        ids = db_subset.iloc[indexes[:, 0].flatten().tolist(), 0]

        return distances, ids

    # chama a função
    try:
        _, output['ids'] = recommendations(ids, n_rec)
        output['status'] = 'Sucesso'
        logger.info(
            f'Em {datetime.now().isoformat()}: {n_rec} recomendações com sucesso.')

    except Exception as e:
        output['status'] = 'Falha'
        logger.error(f'Em {datetime.now().isoformat()}: {e.args}')

    return jsonify(output)
