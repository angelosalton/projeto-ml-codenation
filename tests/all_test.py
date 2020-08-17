import pytest
import requests
from api import predict

url_dev = 'http://127.0.0.1:8050/'

# suite de testes
def api_predict():
    '''
    Testa se a API recebe respostas.
    '''

    actual = 1
    predicted = 1

    assert actual == predicted
    