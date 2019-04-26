from Houdini import Handlers
from Houdini.Handlers import XMLPacket
from Houdini.Converters import VersionChkConverter


@Handlers.handler(XMLPacket('verChk'))
async def handle_version_check(p, version: VersionChkConverter):
    if not version == 153:
        await p.send_xml({'body': {'action': 'apiKO', 'r': '0'}})
        await p.close()
    else:
        await p.send_xml({'body': {'action': 'apiOK', 'r': '0'}})


@Handlers.handler(XMLPacket('rndK'))
async def handle_random_key(p, data):
    await p.send_xml({'body': {'action': 'rndK', 'r': '-1'}, 'k': 'houdini'})
