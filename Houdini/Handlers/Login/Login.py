from Houdini import Handlers
from Houdini.Handlers import XMLPacket
from Houdini.Converters import CredentialsConverter


@Handlers.handler(XMLPacket('login'))
async def handle_login(p, credentials: CredentialsConverter):
    username, password = credentials
    p.logger.info('{}:{} is logging in!'.format(username, password))
