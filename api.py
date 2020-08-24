import logging
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify
from joblib import load


# carrega modelo
model = load('model.joblib')

# carrega banco de dados de empresas
db = pd.read_parquet('data/estaticos_market.parquet')

# inicializa log
logger = logging.Logger('root')

# inicializa API
server = Flask(__name__)


@server.route('/test')
def hello():
    return 'Olá, mundo!'


@server.route('/predict', methods=['POST'])
def predict():
    '''Retorna as previsões do modelo.

    :return: JSON com as ids de empresas previstas.
    :rtype: dict
    '''

    request_raw = request.get_json(force=True)
    ids = request_raw['ids']
    n_rec = request_raw['n']

    # debug
    print(ids)
    print(n_rec)

    # inicializa JSON de saída
    output = {}

    left = pd.DataFrame(ids, columns=['id'])

    # consulta o portfolio no banco de dados de mercado
    try:
        full_data = pd.merge(left, db, on='id')

    except Exception as e:
        output['status'] = 'Falha'
        output['reason'] = 'Nenhuma empresa do portfolio foi encontrada no banco de dados.'
        logger.error(f'Em {datetime.now().isoformat()}: {e.args}')

        return jsonify(output)

    def recommendations(ids: list, n: int):

        # subconjunto com o portfolio informado
        tmp = db[db.index.isin(ids)]

        # obtem as previsoes do modelo
        distances, indexes = model.named_steps['model'].kneighbors(
            model.named_steps['data_tr'].transform(tmp), n
        )

        return distances, indexes

    # chama a função
    try:
        output['distances'], output['ids'] = recommendations(ids, n_rec)
        output['status'] = 'Sucesso'
        logger.info(f'Em {datetime.now().isoformat()}: Sucesso')

    except Exception as e:
        output['status'] = 'Falha'
        output['reason'] = 'Falha nas recomendações do modelo.'
        logger.error(f'Em {datetime.now().isoformat()}: {e.args}')

    return jsonify(output)
