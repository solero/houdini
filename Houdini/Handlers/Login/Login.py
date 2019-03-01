from Houdini import Handlers
from Houdini.Handlers import XTPacket, XMLPacket
from Houdini.Converters import CredentialsConverter, CommaConverter


@Handlers.handler(XMLPacket('login'))
async def handle_login(p, credentials: CredentialsConverter):
    username, password = credentials
    p.logger.info('{}:{} is logging in!'.format(username, password))


@Handlers.handler(XTPacket('t', 'c'), pre_login=True)
@Handlers.player_in_room(100)
async def handle_test(p, numbers: CommaConverter):
    print(list(numbers))
