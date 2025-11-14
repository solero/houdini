import random
from datetime import datetime

from houdini import handlers
from houdini.constants import ClientType
from houdini.data import db
from houdini.data.igloo import Furniture, Igloo
from houdini.data.item import Item
from houdini.data.redemption import PenguinRedemptionCode, RedemptionAwardCard, \
    RedemptionAwardFlooring, RedemptionAwardFurniture, RedemptionAwardIgloo, RedemptionAwardItem, \
    RedemptionAwardLocation, RedemptionAwardPuffle, RedemptionAwardPuffleItem, RedemptionCode
from houdini.handlers import XTPacket
from houdini.penguin import Penguin


TreasureUnlockCount = 3
NinjaRankUpChoice = 1
FireNinjaRankUpChoice = 3
WaterNinjaRankUpChoice = 4
SnowNinjaRankUpChoice = 5

CardRewards = [4025, 4026, 4027, 4028, 4029, 4030, 4031, 4032, 4033, 104, 6077, 4380, 2033, 1271]
CardPostcards = {0: 177, 4: 178, 8: 179}
CardStamps = {0: 230, 4: 232, 8: 234, 9: 236}

FireRewards = [6025, 4120, 2013, 1086, 3032]
FireStamps = {1: 256, 3: 262}

WaterRewards = [6026, 4121, 2025, 1087, 3032]
WaterStamps = {1: 278, 3: 282, 4: 284}

SnowRewards = {
    0: None,
    1: None,  # Movie 1
    2: 6163,  # Glacial Sandals
    3: None,  # Movie 2
    4: None,  # Movie 3
    5: 4834,  # Coat of Frost
    6: None,  # Movie 4
    7: None,  # Movie 5
    8: 2119,  # Icy Mask
    9: None,  # Movie 6
    10: None, # Movie 7
    11: 1581, # Blizzard Helmet
    12: None, # Movie 8
    13: None, # Snow Gem - NOTE: awarded outside of the game server by a popup within Flash
    14: 1582, # Black Ice Headband
    15: 4835, # Frozen Armor
    16: 5223, # Ice Cap Cuffs
    17: 4836, # Black Ice Training Plates
    18: 1583, # The Flurry
    19: 6164, # Cold Snap Sandals
    20: 4837, # Snowstorm Gi
    21: 5224, # Storm Cloud Bracers,
    22: 5225, # Snow Shuriken
    23: 5226, # Fire Nunchaku
    24: 5227  # Water Hammer
}

# Importing from houdini.handlers.games.ninja does not work due to room stamp groups
async def ninja_rank_up(p: Penguin, ranks: int = 1) -> bool:
        """
        Updates a Card-Jitsu rank for a penguin

        Returns whether or not the player was able to rank up
        """
        if p.ninja_rank + ranks > len(CardRewards):
            return False
        for rank in range(p.ninja_rank, p.ninja_rank + ranks):
            await p.add_inventory(
                p.server.items[CardRewards[rank]], cost=0, notify=False
            )
            if rank in CardStamps:
                await p.add_stamp(p.server.stamps[CardStamps[rank]])
            if rank in CardPostcards:
                await p.add_inbox(p.server.postcards[CardPostcards[rank]])

        await p.update(ninja_rank=p.ninja_rank + ranks).apply()
        return True

async def fire_ninja_rank_up(p: Penguin, ranks: int = 1) -> bool:
        """
        Updates a Card-Jitsu Fire rank for a penguin

        Returns whether or not the player was able to rank up
        """
        if p.fire_ninja_rank + ranks > len(FireRewards):
            return False
        for rank in range(p.fire_ninja_rank, p.fire_ninja_rank + ranks):
            await p.add_inventory(
                p.server.items[FireRewards[rank]], cost=0, notify=False
            )
            if rank in FireStamps:
                await p.add_stamp(p.server.stamps[FireStamps[rank]])

        await p.update(fire_ninja_rank=p.fire_ninja_rank + ranks).apply()
        return True

async def water_ninja_rank_up(p: Penguin, ranks: int = 1) -> bool:
        """
        Updates a Card-Jitsu Water rank for a penguin

        Returns whether or not the player was able to rank up
        """
        if p.water_ninja_rank + ranks > len(WaterRewards):
            return False
        for rank in range(p.water_ninja_rank, p.water_ninja_rank + ranks):
            await p.add_inventory(
                p.server.items[WaterRewards[rank]], cost=0, notify=False
            )
            if rank in WaterStamps:
                await p.add_stamp(p.server.stamps[WaterStamps[rank]])

        await p.update(water_ninja_rank=p.water_ninja_rank + ranks).apply()
        return True

# Does not exist in Houdini
async def snow_ninja_rank_up(p: Penguin, ranks: int = 1) -> bool:

    """
    Updates a Card-Jitsu Snow rank for a penguin

    Returns whether or not the player was able to rank up
    """
    if p.snow_ninja_rank + ranks >= 13:
        # Unlock "Snow Pro" stamp
        await p.add_stamp(p.server.stamps[487])
    if p.snow_ninja_rank + ranks > len(SnowRewards):
        return False
    for rank in range(p.snow_ninja_rank, p.snow_ninja_rank + ranks):
        if not (item := SnowRewards.get(rank)):
            continue
        await p.add_inventory(
            p.server.items[item], cost=0, notify=False
        )

    await p.update(snow_ninja_rank=p.snow_ninja_rank + ranks).apply()
    return True


@handlers.handler(XTPacket('rsc', ext='red'), pre_login=True, client=ClientType.Legacy)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_code_legacy(p, redemption_code: str):
    query = RedemptionCode.distinct(RedemptionCode.id)\
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id))\
        .query.where(db.func.upper(RedemptionCode.code) == redemption_code.upper())
    codes = await query.gino.all()
    if not codes:
        return await p.send_error(720)

    code = codes[0]
    awards = []

    if code.uses is not None:
        redeemed_count = await db.select([db.func.count(PenguinRedemptionCode.code_id)]).where(
            PenguinRedemptionCode.code_id == code.id).gino.scalar()

        if redeemed_count >= code.uses:
            return await p.send_error(721)

    penguin_redeemed = await PenguinRedemptionCode.query.\
        where((PenguinRedemptionCode.code_id == code.id) &
              (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()
    if penguin_redeemed:
        return await p.send_error(721)

    if code.expires is not None and code.expires < datetime.now():
        return await p.send_error(726)

    if code.type == 'GOLDEN':
        p.server.cache.set(f'{p.id}.{code.code}.golden_code', code)
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank,
                               int(p.fire_ninja_rank > 0), int(p.water_ninja_rank > 0))

    if code.type == 'CARD':
        for award in code.cards:
            awards.append(str(award.card_id))
            await p.add_card(p.server.cards[award.card_id])
    else:
        if code.items:
            for award in code.items:
                awards.append(str(award.item_id))
                await p.add_inventory(p.server.items[award.item_id], notify=False, cost=0)

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)
    await p.update(coins=p.coins + code.coins).apply()
    return await p.send_xt('rsc', code.type, ','.join(map(str, awards)), code.coins)


@handlers.handler(XTPacket('rsc', ext='red'), pre_login=True, client=ClientType.Vanilla)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_code_vanilla(p, redemption_code: str):
    query = RedemptionCode.distinct(RedemptionCode.id) \
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              flooring=RedemptionAwardFlooring.distinct(RedemptionAwardFlooring.flooring_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id))\
        .query.where(db.func.upper(RedemptionCode.code) == redemption_code.upper())
    codes = await query.gino.all()
    if not codes:
        return await p.send_error(720)

    code = codes[0]
    awards = []

    if code.uses is not None:
        redeemed_count = await db.select([db.func.count(PenguinRedemptionCode.code_id)]).where(
            PenguinRedemptionCode.code_id == code.id).gino.scalar()

        if redeemed_count >= code.uses:
            return await p.send_error(721)

    penguin_redeemed = await PenguinRedemptionCode.query.where((PenguinRedemptionCode.code_id == code.id) &
                                                               (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()
    if penguin_redeemed:
        return await p.send_error(721)

    if code.expires is not None and code.expires < datetime.now():
        return await p.send_error(726)

    if code.type == 'CATALOG':
        num_redeemed_codes = await PenguinRedemptionCode.join(RedemptionCode).count().where(
            (PenguinRedemptionCode.penguin_id == p.id) & (RedemptionCode.type == 'CATALOG')).gino.scalar()
        owned_ids = ','.join((str(item.id) for item in p.server.items.treasure if item.id in p.inventory))
        bad_items = 0

        if code.items:
            for award in code.items:
                item_allowed = True
                if award.item_id in p.inventory:
                    item_allowed = False
                    bad_items += 1
                await p.add_inventory(p.server.items[award.item_id], notify=False, cost=0)
                awards.append(f'item{award.item_id},{int(item_allowed)}')
        if code.furniture:
            for award in code.furniture:
                item_allowed = True
                if award.furniture_id in p.furniture:
                    penguin_furniture = p.furniture[award.furniture_id]
                    if penguin_furniture.quantity >= p.server.furniture[award.furniture_id].max_quantity:
                        item_allowed = False
                        bad_items += 1
                await p.add_furniture(p.server.furniture[award.furniture_id], notify=False, cost=0)
                awards.append(f'f{award.furniture_id},{int(item_allowed)}')
        if code.igloos:
            for award in code.igloos:
                item_allowed = True
                if award.igloo_id in p.igloos:
                    item_allowed = False
                    bad_items += 1
                await p.add_igloo(p.server.igloos[award.igloo_id], notify=False, cost=0)
                awards.append(f'g{award.igloo_id},{int(item_allowed)}')
        if code.locations:
            for award in code.locations:
                item_allowed = True
                if award.location_id in p.locations:
                    item_allowed = False
                    bad_items += 1
                await p.add_location(p.server.locations[award.location_id], notify=False, cost=0)
                awards.append(f'loc{award.location_id},{int(item_allowed)}')
        if code.flooring:
            for award in code.flooring:
                item_allowed = True
                if award.flooring_id in p.flooring:
                    item_allowed = False
                    bad_items += 1
                await p.add_flooring(p.server.flooring[award.flooring_id], notify=False, cost=0)
                awards.append(f'flr{award.flooring_id},{int(item_allowed)}')
        if code.puffles:
            for award in code.puffles:
                item_allowed = True
                if len(p.puffles) >= 75:
                    item_allowed = False
                    bad_items += 1
                awards.append(f'p{award.puffle_id},{int(item_allowed)}')
        if code.puffle_items:
            for award in code.puffle_items:
                item_allowed = True
                if award.puffle_item_id in p.puffle_items:
                    penguin_care_item = p.puffle_items[award.puffle_item_id]
                    if penguin_care_item.quantity >= 100:
                        item_allowed = False
                        bad_items += 1
                await p.add_puffle_item(p.server.puffle_items[award.puffle_item_id], notify=False, cost=0)
                awards.append(f'pi{award.puffle_item_id},{int(item_allowed)}')

        p.allowed_redemption_items = TreasureUnlockCount + bad_items + (2 if num_redeemed_codes == 4 else 0)
        p.server.cache.set(f'{p.id}.{code.code}.treasure_code', code)
        return await p.send_xt('rsc', 'treasurebook', p.allowed_redemption_items, owned_ids, num_redeemed_codes, 0, int(len(awards) > 0), '|'.join(awards))

    if code.type == 'GOLDEN':
        p.server.cache.set(f'{p.id}.{code.code}.golden_code', code)
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank, p.snow_ninja_rank,
                               1, 1, 1)

    if code.type == 'INNOCENT':
        innocent_redeemed_items = {item for item in p.server.items.innocent if item.id in p.inventory}
        innocent_redeemed_furniture = {item for item in p.server.furniture.innocent if item.id in p.furniture}
        innocent_redeemed = innocent_redeemed_items.union(innocent_redeemed_furniture)
        innocent_clothing = {item for item in p.server.items.innocent}
        innocent_furniture = {item for item in p.server.furniture.innocent}
        innocent_items = innocent_clothing.union(innocent_furniture)

        innocent_remaining = innocent_items - innocent_redeemed

        choices = random.sample(list(innocent_remaining), min(len(innocent_remaining), 3))
        if len(innocent_redeemed) + 3 == len(innocent_items):
            choices.append(p.server.igloos[53])
        for item in choices:
            if type(item) is Item:
                awards.append(str(item.id))
                await p.add_inventory(item, notify=False, cost=0)
            elif type(item) is Igloo:
                awards.append(f'g{item.id}')
                await p.add_igloo(item, notify=False, cost=0)
            elif type(item) is Furniture:
                awards.append(f'f{item.id}')
                await p.add_furniture(item, notify=False, cost=0)

        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)

        return await p.send_xt('rsc', 'INNOCENT', ','.join(map(str, awards)),
                               len(innocent_redeemed) + len(choices),
                               len(innocent_items))

    if code.type == 'CARD':
        for award in code.cards:
            awards.append(str(award.card_id))
            await p.add_card(p.server.cards[award.card_id])
    else:
        if code.items:
            for award in code.items:
                awards.append(str(award.item_id))
                await p.add_inventory(p.server.items[award.item_id], notify=False, cost=0)
        if code.furniture:
            for award in code.furniture:
                awards.append(f'f{award.furniture_id}')
                await p.add_furniture(p.server.furniture[award.furniture_id], notify=False, cost=0)
        if code.igloos:
            for award in code.igloos:
                awards.append(f'g{award.igloo_id}')
                await p.add_igloo(p.server.igloos[award.igloo_id], notify=False, cost=0)
        if code.locations:
            for award in code.locations:
                awards.append(f'loc{award.location_id}')
                await p.add_location(p.server.locations[award.location_id], notify=False, cost=0)
        if code.flooring:
            for award in code.flooring:
                awards.append(f'flr{award.flooring_id}')
                await p.add_flooring(p.server.flooring[award.flooring_id], notify=False, cost=0)
        if code.puffles:
            for award in code.puffles:
                awards.append(f'p{award.puffle_id}')
        if code.puffle_items:
            for award in code.puffle_items:
                awards.append(f'pi{award.puffle_item_id}')
                await p.add_puffle_item(p.server.puffle_items[award.puffle_item_id], notify=False, cost=0)

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)
    await p.update(coins=p.coins + code.coins).apply()
    return await p.send_xt('rsc', code.type, ','.join(map(str, awards)), code.coins or '')


@handlers.handler(XTPacket('rsgc', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_golden_choice(p, redemption_code: str, choice: int):
    code_key = f'{p.id}.{redemption_code.upper()}.golden_code'
    code = p.server.cache.get(code_key)
    p.server.cache.delete(code_key)
    if not code:
        return await p.close()

    if len(code.cards) < 6:
        p.logger.error("Golden card codes must have exactly 6 cards in redemption_award_card!")
        return await p.close()

    cards = list(code.cards)
    card_ids = [str(card.card_id) for card in cards]

    if choice == NinjaRankUpChoice:
        await ninja_rank_up(p)
        cards = cards[:4]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + str(p.ninja_rank))
    elif choice == FireNinjaRankUpChoice:
        await fire_ninja_rank_up(p)
        cards = cards[:4]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + str(p.fire_ninja_rank))
    elif choice == WaterNinjaRankUpChoice:
        await water_ninja_rank_up(p)
        cards = cards[:4]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + str(p.water_ninja_rank))
    elif choice == SnowNinjaRankUpChoice:
        await snow_ninja_rank_up(p)
        cards = cards[:4]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + str(p.snow_ninja_rank))
    else:
        cards = cards[:4] + cards[-2:]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + ','.join(card_ids[-2:]))

    for card in cards:
        await p.add_card(p.server.cards[card.card_id])

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)


@handlers.handler(XTPacket('rscrt', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_send_cart(p, redemption_code: str, choice: str):
    code_key = f'{p.id}.{redemption_code.upper()}.treasure_code'
    code = p.server.cache.get(code_key)
    p.server.cache.delete(code_key)

    if code is None:
        return await p.close()

    coins = 0
    awards = []
    choices = choice.split(',')

    if len(choices) > p.allowed_redemption_items:
        return await p.close()

    p.allowed_redemption_items = 0

    for choice in choices:
        if choice.startswith('c'):
            coins += 500
        elif choice.startswith('p'):
            awards.append(choice)
        elif choice.isdigit() and p.server.items[int(choice)].treasure:
            awards.append(choice)
            await p.add_inventory(p.server.items[int(choice)], notify=False, cost=0)

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)

    await p.update(coins=p.coins + coins).apply()
    await p.send_xt('rscrt', ','.join(awards), coins or '')


@handlers.handler(XTPacket('rsp', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_redeem_puffle(p, name: str, puffle_type: int):
    if puffle_type not in p.server.puffles:
        return await p.close()

    if not 16 > len(name) >= 3:
        await p.send_xt('rsp', 0)

    if len(p.puffles) >= 75:
        return await p.send_error(440)

    puffle = await p.puffles.insert(puffle_id=puffle_type, name=name)
    await p.add_puffle_item(p.server.puffle_items[3], quantity=5, cost=0)
    await p.add_puffle_item(p.server.puffle_items[79], cost=0)
    await p.add_puffle_item(p.server.puffle_items[p.server.puffles[puffle.puffle_id].favourite_toy])
    await p.add_inbox(p.server.postcards[111], details=puffle.name)
    await p.send_xt('rsp', 1)
