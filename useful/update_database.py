import sqlite3, os

this_dir: str = __file__[:__file__.rfind(os.sep)]
db_path_card_datas: str = f'{this_dir[:this_dir.rfind(os.sep)]}{os.sep}quick_db.sqlite'
db_path_ansi_datas: str = f'{this_dir[:this_dir.rfind(os.sep)]}{os.sep}ansi_db.sqlite'
db_path_price_datas: str = f'{this_dir[:this_dir.rfind(os.sep)]}{os.sep}prices_db.sqlite'

CARD_COLUMNS: set = {'power', 'toughness', 'cmc', 'name', 'type', 'setcode', 'types', 'text', 'artist', 'scryfall_id',
                     'keywords', 'side', 'frame_effects', 'number', 'loyalty', 'rarity', 'mana_cost', 'colors', 'color_identity'}

SET_COLUMNS: set = {'name', 'releasedate_epoch', 'releasedate_string', 'setcode', 'type'}

# BLOCK STUPID SHIT
BLOCK_KEYWORDS: set = {'The List', 'Mystery Booster', 'Renaissance', 'Rinascimento'}
BLOCK_TYPES: set = {'archenemy', 'arsenal', 'box', 'duel_deck', 'from_the_vault', 'funny', 'memorabilia', 'minigame', 'premium_deck', 'promo', 'spellbook', 'starter', 'token', 'vanguard', 'planechase'}
BLOCK_SETCODES: set = {'4BB', 'FBB'}

def make_quick_db():
    src_db_path: str = '/home/plutonergy/Coding/PLMTG_v4/AllPrintings.sqlite'
    if not os.path.exists(src_db_path):
        return

    class SrcCard:
        """"""

    class SrcSet:
        """"""

    class DstCard:
        """"""

    class DstSet:
        """"""

    dst_connection = sqlite3.connect(db_path_card_datas)
    dst_cursor = dst_connection.cursor()

    src_connection = sqlite3.connect(src_db_path)
    src_cursor = src_connection.cursor()

    q: str = f'PRAGMA table_info(cards)'
    cards_pragma: list[tuple] = src_cursor.execute(q).fetchall()
    [setattr(SrcCard, x[1], x[0]) for x in cards_pragma]

    q: str = f'PRAGMA table_info(sets)'
    sets_pragma: list[tuple] = src_cursor.execute(q).fetchall()
    [setattr(SrcSet, x[1], x[0]) for x in sets_pragma]

    q: str = 'select * from sets where setcode is not null'
    src_sets: list[tuple] = [x for x in src_cursor.execute(q).fetchall()]
    for keyword in BLOCK_KEYWORDS:
        src_sets = [x for x in src_sets if not x[SrcSet.name].startswith(keyword)]
    for block_type in BLOCK_TYPES:
        src_sets = [x for x in src_sets if not x[SrcSet.type] == block_type]
    for block_setcode in BLOCK_SETCODES:
        src_sets = [x for x in src_sets if not x[SrcSet.setcode] == block_setcode]

    good_setcodes: set = {x[SrcSet.setcode] for x in src_sets}
    placehldrs: str = ','.join(['?'] * len(good_setcodes))

    q: str = f'select * from cards where setcode in ({placehldrs})'
    src_cards: list[tuple] = [x for x in src_cursor.execute(q, list(good_setcodes)).fetchall()]

    src_cursor.close()
    src_connection.close()

    card_cols: list[str] = sorted(list(CARD_COLUMNS))
    set_cols: list[str] = sorted(list(SET_COLUMNS))

    with dst_connection:
        colname_type: dict = {x[1]: x[2] for x in sets_pragma if x[1] in card_cols}
        name_type: list[str] = [f'{colname} {colname_type[colname]}' for colname in card_cols]
        q: str = f'create table cards ({",".join(name_type)})'
        dst_cursor.execute(q)

        colname_type: dict = {x[1]: x[2] for x in sets_pragma if x[1] in set_cols}
        name_type: list[str] = [f'{colname} {colname_type[colname]}' for colname in set_cols]
        q: str = f'create table sets ({",".join(name_type)})'
        dst_cursor.execute(q)

    q: str = f'PRAGMA table_info(cards)'
    cards_pragma: list[tuple] = dst_cursor.execute(q).fetchall()
    [setattr(DstCard, x[1], x[0]) for x in cards_pragma]

    q: str = f'PRAGMA table_info(sets)'
    sets_pragma: list[tuple] = dst_cursor.execute(q).fetchall()
    [setattr(DstSet, x[1], x[0]) for x in sets_pragma]

    many_cards: list[tuple] = []
    dst_src: dict[int, int] = {getattr(SrcCard, colname): getattr(DstCard, colname) for colname in CARD_COLUMNS}
    for card in src_cards:
        v: list = [None] * len(card_cols)
        for src_ix, dst_ix in dst_src.items():
            v[dst_ix] = card[src_ix]

        many_cards.append(tuple(v))

    many_sets: list[tuple] = []
    dst_src: dict[int, int] = {getattr(SrcSet, colname): getattr(DstSet, colname) for colname in SET_COLUMNS}
    for setdata in src_sets:
        v: list = [None] * len(SET_COLUMNS)
        for src_ix, dst_ix in dst_src.items():
            v[dst_ix] = setdata[src_ix]

        many_sets.append(tuple(v))

    with dst_connection:
        marks: list = ['?'] * len(card_cols)
        q: str = f'insert into cards values({",".join(marks)})'
        dst_cursor.executemany(q, many_cards)

        marks: list = ['?'] * len(set_cols)
        q: str = f'insert into sets values({",".join(marks)})'
        dst_cursor.executemany(q, many_sets)

    dst_cursor.close()
    dst_connection.close()

def inject_ansi(dst_connection, dst_cursor):
    q: str = 'select * from cards where ansi is not null'
    if not os.path.exists(db_path_ansi_datas) or dst_cursor.execute(q).fetchone():
        return

    Card = lambda: None
    q: str = f'PRAGMA table_info(cards)'
    [setattr(Card, x[1], x[0]) for x in dst_cursor.execute(q).fetchall()]

    src_connection = sqlite3.connect(db_path_ansi_datas)
    src_cursor = src_connection.cursor()
    q: str = 'select scryfall_id, ansi from ansidata'
    id_val: dict = {scryfall_id: ansi for scryfall_id, ansi in src_cursor.execute(q).fetchall()}

    q: str = 'select scryfall_id from cards where ansi is null'
    matches: set = {x[0] for x in dst_cursor.execute(q).fetchall() if x[0] in id_val}
    if not matches:
        return

    q: str = 'select * from cards'
    all_cards: list = [x for x in dst_cursor.execute(q).fetchall()]
    for n, card in enumerate(all_cards):
        scryfall_id: str = card[Card.scryfall_id]
        if scryfall_id not in matches:
            continue

        tmp_card: list = list(card)
        tmp_card[Card.ansi]: bytes = id_val[scryfall_id]
        all_cards[n]: tuple = tuple(tmp_card)

    with dst_connection:
        q: str = 'delete from cards;' # because individually updating takes loads of time without auto_ids
        dst_cursor.execute(q)

        placehldrs: str = ','.join(['?'] * len(all_cards[0]))
        q: str = f'insert into cards values({placehldrs})'
        dst_cursor.executemany(q, all_cards)

def inject_prices(dst_connection, dst_cursor):
    q: str = 'select * from cards where regular_price is not null'
    if not os.path.exists(db_path_price_datas) or dst_cursor.execute(q).fetchone():
        return

    Card = lambda: None
    q: str = f'PRAGMA table_info(cards)'
    [setattr(Card, x[1], x[0]) for x in dst_cursor.execute(q).fetchall()]

    src_connection = sqlite3.connect(db_path_price_datas)
    src_cursor = src_connection.cursor()
    q: str = 'select scryfall_id, regular_price, foil_price from prices'
    id_val: dict = {scryfall_id: (reg, foil) for scryfall_id, reg, foil in src_cursor.execute(q).fetchall()}
    quick_ids: set[str] = set(id_val.keys())

    q: str = 'select * from cards'
    all_cards: list = [x for x in dst_cursor.execute(q).fetchall()]
    update: bool = False
    for n, card in enumerate(all_cards):
        scryfall_id: str = card[Card.scryfall_id]
        if scryfall_id not in quick_ids:
            continue

        reg, foil = id_val[scryfall_id]
        if card[Card.regular_price] == reg and card[Card.foil_price] == foil:
            continue

        tmp_card: list = list(card)
        tmp_card[Card.regular_price]: float | None = reg
        tmp_card[Card.foil_price]: float | None = foil
        all_cards[n]: tuple = tuple(tmp_card)
        update = True

    if update:
        with dst_connection:
            q: str = 'delete from cards;'  # because individually updating takes loads of time without auto_ids
            dst_cursor.execute(q)

            placehldrs: str = ','.join(['?'] * len(all_cards[0]))
            q: str = f'insert into cards values({placehldrs})'
            dst_cursor.executemany(q, all_cards)




































