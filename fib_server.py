#!/usr/bin/env python3
import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='haq_jobs')

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)

def on_request(ch, method, props, body):
    n = int(body)

    response = fib(n)
    print(" [%s] fib(%s)=%d" % (timestamp(), n, response))

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id = props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume('haq_jobs', on_request)

print(" [%s] Awaiting RPC requests" % timestamp())
channel.start_consuming()
