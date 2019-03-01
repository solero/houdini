import asyncio


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 6112)

    print(f'Send: {message!r}')
    writer.write(message.encode())

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

loop = asyncio.ProactorEventLoop()
asyncio.set_event_loop(loop)

for x in range(1):
    # asyncio.ensure_future(tcp_echo_client('<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[benny]]></nick><pword><![CDATA[pword]]></pword></login></body></msg>\0'))
    asyncio.ensure_future(tcp_echo_client('%xt%s%t#c%-1%1,2,3,4%\0%xt%s%t#c%-1%1,2,3,4%\0'))

loop.run_forever()
