#!/usr/bin/env python3
import pika
import sys
import time
import argparse

host = 'localhost'
port = 5672


class FunctionNameToObject(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(FunctionNameToObject, self).__init__(
            option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, globals()[values])


def determine_after_cancel_callback(args):
    return globals()[args.after_cancel]


def parse_args():
    parser = argparse.ArgumentParser(description=(
        "Consume 'haq' queue and take action on receiving "
        "Consumer Cancel Notification from RabbitMQ"))
    parser.add_argument(
        '--after-cancel',
        help='Behaviour after getting basic.cancel',
        choices=['reconsume', 'reopen', 'reconnect', 'crash'],
        action=FunctionNameToObject,
        default='reconsume')
    parser.add_argument(
        '-s', '--server', type=str, help='Server name', default="localhost")
    parser.add_argument(
        '-p', '--port', type=int, help='Port number', default=5672)
    return parser.parse_args()


def consume_args():
    return {'x-cancel-on-ha-failover': True}


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def deliver_callback(ch, method, properties, body):
    print(" [%s] Received %s" % (timestamp(), body))


def cancel_callback(frame):
    print(" [%s] Consumer was canceled by the broker." % timestamp())


def connect(host, port):
    return pika.BlockingConnection(pika.ConnectionParameters(host, port))


def create_channel(connection):
    return connection.channel()


def reconsume(conn, channel, consume_args, opts):
    consume(conn, channel, consume_args, opts)


def consume(conn, channel, consume_args, opts):
    channel.basic_consume('haq',
                          deliver_callback,
                          auto_ack=True,
                          arguments=consume_args)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    opts.after_cancel(conn, channel, consume_args, opts)


def reopen(conn, channel, consume_args, opts):
    print(' [%s] Closing old channel' % timestamp())
    channel.close()
    channel = create_channel(conn)
    consume(conn, channel, consume_args, opts)


def reconnect(conn, channel, consume_args, opts):
    print(' [%s] Closing old connection' % timestamp())
    conn.close()
    conn = connect(opts.server, opts.port)
    channel = create_channel(conn)
    consume(conn, channel, consume_args, opts)


def crash(conn, channel, consume_args, opts):
    raise Exception(' [%s] misbehaving client' % timestamp())


opts = parse_args()
conn = connect(opts.server, opts.port)
channel = create_channel(conn)
channel.add_on_cancel_callback(cancel_callback)
consume(conn, channel, consume_args(), opts)
