import pandas as pd
from flask import Flask, request, jsonify
from joblib import load


# carrega modelo
model = load('model.joblib')

# carrega banco de dados de empresas
db = pd.read_parquet('data/estaticos_market.parquet')

# inicializa API
server = Flask(__name__)


@server.route('/')
def hello():
    return 'Olá, mundo!'


@server.route('/predict', methods=['POST'])
def predict():
    '''Retorna as previsões do modelo.

    :return: JSON com as ids de empresas previstas.
    :rtype: str
    '''
    ids = request.args.get('ids')

    left = pd.DataFrame(ids, columns=['id'])

    try:
        full_data = pd.merge(left, db, on='id')
    except:
        return None

    output = model.predict(full_data)

    return jsonify(output)
