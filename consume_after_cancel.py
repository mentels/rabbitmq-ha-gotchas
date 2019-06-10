#!/usr/bin/env python3
import pika
import sys
import time
import argparse


def determine_after_cancel_callback():
    parser = argparse.ArgumentParser(description=(
        "Consume 'haq' queue and take action on receiving "
        "Consumer Cancel Notification from RabbitMQ"))
    parser.add_argument(
        '--after-cancel',
        choices=['reconsume', 'reopen', 'reconnect', 'crash'],
        default='reconsume')
    return globals()[parser.parse_args().after_cancel]


def consume_args():
    return {'x-cancel-on-ha-failover': True}


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def deliver_callback(ch, method, properties, body):
    print(" [%s] Received %s" % (timestamp(), body))


def cancel_callback(frame):
    print(" [%s] Consumer was canceled by the broker." % timestamp())


def connect(host):
    return pika.BlockingConnection(pika.ConnectionParameters(host))


def create_channel(connection):
    return connection.channel()


def reconsume(conn, channel, consume_args, after_callback):
    consume(conn, channel, consume_args, after_callback)


def consume(conn, channel, consume_args, after_callback):
    channel.basic_consume('haq',
                          deliver_callback,
                          auto_ack=True,
                          arguments=consume_args)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    after_callback(conn, channel, consume_args, after_callback)


def reopen(conn, channel, consume_args, after_callback):
    print(' [%s] Closing old channel' % timestamp())
    channel.close()
    channel = create_channel(conn)
    consume(conn, channel, consume_args, after_callback)


def reconnect(conn, channel, consume_args, after_callback):
    print(' [%s] Closing old connection' % timestamp())
    conn.close()
    conn = connect('localhost')
    channel = create_channel(conn)
    consume(conn, channel, consume_args, after_callback)


def crash(conn, channel, consume_args, after_callback):
    raise Exception(' [%s] misbehaving client' % timestamp())


conn = connect('localhost')
channel = create_channel(conn)
channel.add_on_cancel_callback(cancel_callback)
consume(conn, channel, consume_args(), determine_after_cancel_callback())
