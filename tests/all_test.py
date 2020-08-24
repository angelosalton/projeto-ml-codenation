import pandas as pd
import pytest
import requests
import time
from api import predict
from ui import app

# inicializa o servidor
url_dev = 'http://localhost:8050/'

app.run_server()
time.sleep(10)


def test_api_alive():
    '''
    Testa se a API recebe respostas.
    '''

    # uma requisição qualquer
    req = requests.get(url_dev)
    time.sleep(1)

    actual = req.status_code
    predicted = 200  # sucesso

    assert actual == predicted


class test_api_recomedacoes:
    '''
    Testa as recomendações do modelo com um portfolio válido.
    '''

    # faz a requisição
    pf1 = pd.read_csv('../data/estaticos_portfolio1.csv')['id'].tolist()
    req = requests.post(url_dev+'predict/', json={'ids': pf1, 'n_rec': 5})

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
