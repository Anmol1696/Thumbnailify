import pika
import time
import json
import logging

from .thumbnail import thumbnailify
from .utils import config
from .db import Client as RedisDb

queue_config = config.get("queue", {})
service = "worker"

def setup_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=queue_config["host"]))
    channel = connection.channel()
    channel.queue_declare(queue=queue_config["name"], durable=True)
    return channel


def callback(ch, method, properties, body):
    media_id = body.decode("utf-8")  # Will be changed to DB lookup
    media_type = properties.headers["media_type"]
    RedisDb.update_state(
        media_id,
        service=service,
        state="Processing",
        code=102,
        message="Worker Processing"
    )
    logging.info(f"Processing id '{media_id}' with type '{media_type}'")
    try:
        thumbnailify(media_type=media_type, media_id=media_id)
    except Exception as e:
        RedisDb.update_state(
            media_id,
            state="Error",
            code=e.status,
            message=str(e)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        RedisDb.update_state(
            media_id,
            state="Completed",
            code=200,
            message="Completed thumbnail creation"
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    channel = setup_channel()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_config["name"], on_message_callback=callback)
    channel.start_consuming()


if __name__ == "__main__":
    main()
