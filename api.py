import logging
from datetime import datetime

import os
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
    response = {}

    # consulta o portfolio no banco de dados de mercado
    try:
        db_subset = pd.merge(left, db, on='id')

        # dataframe não vazio
        if db_subset.shape[0] != 0:
            response['status'] = 'Sucesso'
            response['data'] = db_subset.to_json(orient='records')
            logger.info(
                f'Em {datetime.now().isoformat()}: Consulta ao banco de dados de empresas: {db_subset.shape[0]} valores retornados.')

        # dataframe vazio
        else:
            response['status'] = 'Falha'
            response['data'] = None
            logger.error(
                f'Em {datetime.now().isoformat()}: Nenhuma empresa do portfolio encontrada.')

    except Exception as e:
        response['status'] = 'Falha'
        response['data'] = None
        logger.error(f'Em {datetime.now().isoformat()}: {e}')

    return jsonify(response)


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
    n_rec = request_raw['n_rec']

    # leitura dos dados
    left = pd.DataFrame(ids, columns=['id'])
    db_subset = pd.merge(left, db, on='id')

    # inicializa JSON de saída
    response = {}

    def recommendations(ids: list, n: int):
        '''
        Obtém as previsões do modelo.
        '''
        distances, indexes = model.named_steps['model'].kneighbors(
            model.named_steps['data_tr'].transform(db_subset), n)

        data = db.iloc[indexes[:, 0].flatten().tolist(), :].to_json(orient='records')

        return distances, data

    # chama a função
    try:
        _, response['data'] = recommendations(ids, n_rec)
        response['status'] = 'Sucesso'
        logger.info(
            f'Em {datetime.now().isoformat()}: {n_rec} recomendações com sucesso.')

    except Exception as e:
        response['status'] = 'Falha'
        logger.error(f'Em {datetime.now().isoformat()}: {e}')

    return jsonify(response)


@server.route('/train', methods=['GET'])
def train_model():
    '''
    Treina o modelo novamente de acordo com os dados disponíveis.
    '''
    # inicializa saída
    response = {}

    # chama o notebook da modelagem no shell
    try:
        os.system(
            'jupyter nbconvert --execute ./notebooks/model.ipynb')

        response['status'] = 'Sucesso'
        logger.info(
            f'Em {datetime.now().isoformat()}: Modelo treinado com sucesso.')

    except Exception as e:
        response['status'] = 'Falha'
        logger.error(
            f'Em {datetime.now().isoformat()}: Erro no treinamento do modelo: {e}')

    return jsonify(response)
