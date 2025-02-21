from flask import Flask, request, jsonify
from yookassa import Payment
from yookassa import Refund
from http import HTTPStatus
import sqlite3
from pay import create_recurrent_payment, retry_payment, schedule_retry
from db import init_db, insert_payment, update_payment
from notification import send_notification
import uuid

app = Flask(__name__)

init_db()

@app.route('/create_payment', methods=['POST'])
def create_payment():
    """Создание платежа"""
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    
    try:
        payment = Payment.create({
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://your-site.com/return"
            },
            "save_payment_method": True,
            "capture": True,
            "description": "Платеж пользователя"
        }, uuid.uuid4())
        
        insert_payment((payment.id, user_id, amount, 'pending', None, None))
        
        send_notification(f'Новый платеж создан! ID: {payment.id}, Сумма: {amount} руб.')
        
        return jsonify({'payment_url': payment.confirmation.confirmation_url, 'payment_id': payment.id})
    except Exception as e:
        send_notification(f"Ошибка создания платежа: {str(e)}")
        return jsonify({'error': str(e)}), HTTPStatus.NOT_FOUND

@app.route('/webhook', methods=['POST'])
def payment_webhook():
    """Обработчик уведомлений от YooKassa"""
    event_json = request.json
    payment_id = event_json['object']['id']
    
    try:
        payment = Payment.find_one(payment_id)
        
        update_payment(payment_id, payment.status, 
                       payment.payment_method.id if payment.payment_method else None)
        
        message = f"Платеж {payment_id}\nСтатус: {payment.status}"
        
        if payment.status == 'failed':
            message += f"\nПричина: {payment.cancellation_details.reason}"
            schedule_retry(payment_id)
        
        send_notification(message)
        
        return '', HTTPStatus.OK
    
    except Exception as e:
        send_notification(f"Ошибка webhook: {str(e)}")
        return '', HTTPStatus.BAD_REQUEST

@app.route('/refund', methods=['POST'])
def refund_payment():
    """Эндпоинт для возврата всего платежа по его ID."""
    data = request.get_json()
    payment_id = data.get('payment_id')
    
    if not payment_id:
        return jsonify({'error': 'укажите payment_id'}), HTTPStatus.BAD_REQUEST
    
    try:
        conn = sqlite3.connect('payments.db')
        c = conn.cursor()
        c.execute('SELECT amount, status FROM payments WHERE id=?', (payment_id,))
        payment = c.fetchone()
        conn.close()
        
        if not payment:
            return jsonify({'error': 'Платеж не найден'}), HTTPStatus.NOT_FOUND
        
        if payment[1] != 'succeeded':
            return jsonify({'error': 'Платеж не завершился'}), HTTPStatus.BAD_REQUEST
        
        refund_amount = payment[0] 
        
        refund = Refund.create({
            "payment_id": payment_id,
            "amount": {
                "value": refund_amount,
                "currency": "RUB"
            }
        }, uuid.uuid4())
        
        send_notification(f'Возврат платежа {payment_id}\nСтатус: {refund.status}')
        
        return jsonify({
            'refund_id': refund.id,
            'status': refund.status
        })
    except Exception as e:
        send_notification(f'Ошибка при возврате платежа: {str(e)}')
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST


if __name__ == '__main__':
    app.run(port=5000, debug=True)