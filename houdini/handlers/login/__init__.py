from houdini import handlers
from houdini.handlers import XMLPacket
from houdini.converters import VersionChkConverter


@handlers.handler(XMLPacket('verChk'))
@handlers.allow_once
async def handle_version_check(p, version: VersionChkConverter):
    if not version == 153:
        await p.send_xml({'body': {'action': 'apiKO', 'r': '0'}})
        await p.close()
    else:
        await p.send_xml({'body': {'action': 'apiOK', 'r': '0'}})


@handlers.handler(XMLPacket('rndK'))
@handlers.allow_once
async def handle_random_key(p, data):
    await p.send_xml({'body': {'action': 'rndK', 'r': '-1'}, 'k': 'houdini'})
