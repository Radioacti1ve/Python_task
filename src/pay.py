import uuid
from yookassa import Payment, Configuration
from config import YOO_KASSA_ACCOUNT_ID, YOO_KASSA_SECRET_KEY
from notification import send_notification
from db import insert_payment, get_payment, update_payment
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

Configuration.account_id = YOO_KASSA_ACCOUNT_ID
Configuration.secret_key = YOO_KASSA_SECRET_KEY

scheduler = BackgroundScheduler()
scheduler.start()

def create_recurrent_payment(user_id: str, amount: float, payment_method_id: str):
    """Создание рекуррентного платежа"""
    try:
        payment = Payment.create({
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "payment_method_id": payment_method_id,
            "capture": True,
            "description": "Рекуррентный платеж"
        }, uuid.uuid4())
        
        return payment
    except Exception as e:
        send_notification(f"Ошибка рекуррентного платежа: {str(e)}")
        return None

def schedule_retry(payment_id: str):
    """Планирование повторной попытки платежа"""
    scheduler.add_job(
        id=f'retry_{payment_id}',
        func=retry_payment,
        args=[payment_id],
        trigger='date',
        run_date=datetime.now() + timedelta(days=1)
    )

def retry_payment(payment_id: str):
    """Повторная попытка платежа"""
    payment = get_payment(payment_id)
    
    if payment and payment[3] == 'failed':
        new_payment = create_recurrent_payment(
            payment[1], 
            payment[2],  
            payment[4]  
        )
        
        if new_payment and new_payment.status == 'succeeded':
            send_notification("Повторный платеж успешен!")
            update_payment(payment_id, 'succeeded', payment[4])
        else:
            send_notification("Повторный платеж не удался. Новая попытка через день")
            schedule_retry(payment_id)
