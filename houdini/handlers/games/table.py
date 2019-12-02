from houdini import handlers
from houdini.handlers import XTPacket, check


def table_handler(logic):
    def check_table_game(_, p):
        if p.table is not None and type(p.table.logic) == logic:
            return True
        return False
    return check(check_table_game)


@handlers.handler(XTPacket('a', 'gt'))
async def handle_get_waddle_population(p):
    await p.send_xt('gt', '%'.join(f'{table.id}|{",".join(penguin.safe_name for penguin in table.penguins)}'
                                   for table in p.room.tables.values()))


@handlers.handler(XTPacket('a', 'jt'))
async def handle_join_table(p, table_id: int):
    table = p.room.tables[table_id]
    await table.add(p)
