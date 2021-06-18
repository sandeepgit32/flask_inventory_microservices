import pika
import json

# MESSAGE_BODY = json.dumps({
#     "a": "ui",
#     "b": "soe"
# })

def send_message(MESSAGE_BODY):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    channel.basic_publish(
        exchange = '', 
        routing_key = 'hello', 
        body = json.dumps(MESSAGE_BODY),
        properties = pika.BasicProperties(
            delivery_mode = 2,  # make message persistent
        ))
    print(f" [x] Sent {MESSAGE_BODY}")
    connection.close()