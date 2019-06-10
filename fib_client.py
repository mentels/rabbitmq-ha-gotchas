#!/usr/bin/env python3
import pika
import uuid
import sys
from threading import Thread, Event
import time


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

def open_channel(confirm=False):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    if confirm:
        channel.confirm_delivery()
    return channel

class FibClient(Thread):
    def __init__(self, n, reply_queue, correlation_id):
        Thread.__init__(self)
        self.channel = open_channel(confirm=True)
        self.channel.queue_declare(queue="haq_jobs")
        self.request = str(n)
        self.reply_queue = reply_queue
        self.correlation_id = correlation_id

    def for_response_consumer(self):
        return (self.reply_queue, self.correlation_id)

    def publish(self):
        print(" [%s] About to publish request=%r" %
              (timestamp(), self.request))
        self.channel.basic_publish(exchange='',
                                   routing_key='haq_jobs',
                                   properties=pika.BasicProperties(
                                       reply_to=self.reply_queue,
                                       correlation_id=self.correlation_id
                                   ),
                                   body=self.request)
        print(" [%s] Message ACKed" % timestamp())

    def run(self):
        self.publish()

class ResponseConsumer():
    def __init__(self):
        self.channel = open_channel()
        self.reply_queue = self.channel.queue_declare(
            queue="", exclusive=True).method.queue
        self.correlation_id = str(uuid.uuid4())
        self.response = None
        self.consume()

    def consume(self):
        self.consumer_tag = self.channel.basic_consume(
            self.reply_queue, self.on_response, auto_ack=True)

    def for_client(self):
        return (self.reply_queue, self.correlation_id)

    def start_consuming(self):
        self.channel.start_consuming()

    def on_response(self, channel, method, props, body):
        if props.correlation_id == self.correlation_id:
            print(" [%s] Got response=%d" % (timestamp(), int(body)))
            self.response = int(body)
        else:
            print(" [%s] Got response with unexpected correlation_id=%d"
                  % (timestamp(), props.correlation_id))
        channel.stop_consuming(self.consumer_tag)

n = int(sys.argv[1])

fib_resp_consumer = ResponseConsumer()
(reply_queue, corr_id) = fib_resp_consumer.for_client()
fib_client_thread = FibClient(n, reply_queue, corr_id)

input(" [%s] Press any key to proceed..." % timestamp())
fib_client_thread.start()
fib_resp_consumer.start_consuming()
fib_client_thread.join()
