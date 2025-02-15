from flask import Flask, request
from yookassa.domain.exceptions.not_found_error import NotFoundError
from yookassa.domain.response import PaymentResponse
from yookassa import Payment, Configuration
from http import HTTPStatus
import uuid

from yookassa import Configuration, Payment

Configuration.account_id = '1035010'
Configuration.secret_key = 'test_jfNN1ostA8r37elmnp4O-RErXU-TDu3tmLWbdac_B1E'

app = Flask(__name__)

@app.route('/Payment')
def create_payment():
  payment = Payment.create({
    "amount": {
        "value": "100.00",
        "currency": "RUB"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://www.example.com/return_url"
    },
    "capture": True,
    "description": "Заказ №1"
}, uuid.uuid4())