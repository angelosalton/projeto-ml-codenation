import json
import pandas as pd
import pytest
import requests
import time
from api import predict
from ui import app, app_url, app_port

# inicializa o servidor
url_dev = f'http://{app_url}:{app_port}/'

app.run_server()
time.sleep(10)


def test_api_alive():
    '''
    Testa se a API recebe respostas.
    '''

    # uma requisição qualquer
    req = requests.get(url_dev+'hello/')
    time.sleep(1)

    actual = req.status_code
    predicted = 200  # sucesso

    assert actual == predicted


class test_api_db:
    '''
    Testa a leitura do banco de dados.
    '''
    # faz a requisição
    pf1 = pd.read_csv('../data/estaticos_portfolio1.csv')['id'].tolist()
    req = requests.post(url_dev+'get_table/', data=json.dumps({'ids': pf1}))

    def test_api_db1_status(self):
        '''
        Testa resposta da requisição.
        '''
        actual = self.req.status_code
        predicted = 200

        assert actual == predicted


class test_api_recomedacoes:
    '''
    Testa as recomendações do modelo com um portfolio válido.
    '''

    # faz a requisição
    pf1 = pd.read_csv('../data/estaticos_portfolio1.csv')['id'].tolist()
    req = requests.post(url_dev+'predict/', data=json.dumps({'ids': pf1, 'n_rec': 5}))

    def test_api_rec1_status(self):
        '''
        Testa resposta da requisição.
        '''
        actual = self.req.status_code
        predicted = 200

        assert actual == predicted

    def test_api_rec1_dados(self):
        '''
        Testa os dados retornados da requisição.
        '''
        actual = self.req.raw
        # TODO: predicted = 'a'

        assert actual == predicted
