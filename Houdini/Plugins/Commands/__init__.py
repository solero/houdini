from Houdini.Handlers import Handlers, XTPacket


class Commands:

    def __init__(self, server):
        self.server = server

    @Handlers.handler(XTPacket('s', 'sm'))
    async def handle_send_message(self, message: str):
        print('Do stuff with {}'.format(message))
