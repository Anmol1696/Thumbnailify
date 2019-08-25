import aioamqp


class Transport:
    async def __init__(self, queue, **kwargs):
        self.transport, self.protocol = await aioamqp.connect(**kwargs)
        self.channel = await protocol.channel()
        await self.channed.queue_declare(queue_name=queue, durable=True)

    async def close(self):
        await self.protocol.close()
        transport.close()
