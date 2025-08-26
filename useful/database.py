import time, sqlite3, os, sys
from useful.termcols import crm_white,end
from useful.update_database import inject_ansi

class Card:
    """"""
class Set:
    """"""

timer_start: float = time.time()
print(f'initializing database, ', end='', flush=True)

class Bag:
    def __init__(self):
        self.cards: list[tuple] = []
        self.processing: list[tuple] = []
        self.prefered: tuple | None = None
        self.is_stupid: bool = True

this_dir: str = __file__[:__file__.rfind(os.sep)]
db_path_card_datas: str = f'{this_dir[:this_dir.rfind(os.sep)]}{os.sep}quick_db.sqlite'

connection = sqlite3.connect(db_path_card_datas)
cursor = connection.cursor()

q: str = 'select * from cards where ansi is not null'
if '--no-ansi' not in sys.argv[1:] and not cursor.execute(q).fetchone():
    inject_ansi(connection, cursor)

q: str = f'PRAGMA table_info(cards)'
[setattr(Card, x[1], x[0]) for x in cursor.execute(q).fetchall()]

q: str = f'PRAGMA table_info(sets)'
[setattr(Set, x[1], x[0]) for x in cursor.execute(q).fetchall()]

q: str = (f'select setcode, releasedate_epoch from sets '
          f'where setcode is not null '
          f'and releasedate_epoch is not null '
          f'and type is not null')

SETCODE_TIME: dict[str, int] = {setcode: release_epoch for setcode, release_epoch in cursor.execute(q).fetchall()}
SETCODES: set = set(SETCODE_TIME.keys())

q: str = 'select * from cards where side is "a" or side is null'
all_cards: list[tuple] = cursor.execute(q).fetchall()
NAME_BAG: dict = {x[Card.name]: Bag() for x in all_cards if x[Card.setcode] in SETCODES}
[NAME_BAG[x[Card.name]].cards.append(x) for x in all_cards if x[Card.setcode] in SETCODES]

placehldrs: str = ','.join(['?'] * len(SETCODES))
q: str = f'select setcode, type from sets where setcode in ({placehldrs})'
setcode_type: dict = {setcode: exptype for setcode, exptype in cursor.execute(q, list(SETCODES)).fetchall()}

q: str = f'select setcode, name from sets where setcode in ({placehldrs})'
SETCODE_EXPNAME: dict = {setcode: expname for setcode, expname in cursor.execute(q, list(SETCODES)).fetchall()}
EXPNAME_SETCODE: dict = {expname: setcode for setcode, expname in SETCODE_EXPNAME.items()}

for name, bag in NAME_BAG.items():
    bag.cards.sort(key=lambda x: SETCODE_TIME[x[Card.setcode]], reverse=True)
    for card in bag.cards:
        if setcode_type[card[Card.setcode]] in ['expansion', 'core']:
            prefered_setcode: str = card[Card.setcode]
            bag.is_stupid = False
            break
    else:
        for card in bag.cards:
            if setcode_type[card[Card.setcode]] in ['draft_innovation', 'masters'] and len(card[Card.setcode]) == 3:
                prefered_setcode: str = card[Card.setcode]
                break
        else:
            for card in bag.cards:
                if len(card[Card.setcode]) == 3:
                    prefered_setcode: str = card[Card.setcode]
                    break
            else:
                prefered_setcode: str = bag.cards[0][Card.setcode]

    cards: list[tuple] = [x for x in bag.cards if x[Card.setcode] == prefered_setcode]
    if len(cards) == 1:
        bag.prefered = cards[0]
    else:
        card_val: list[tuple] = [(card, (card[Card.frame_effects] or '').count(',')) for card in cards]
        card_val.sort(key=lambda x: x[1])
        card_val = [x for x in card_val if x[1] == card_val[0][1]]
        if len(card_val) > 1:
            dual: list[tuple] = []
            for card, _ in card_val:
                digs: str = ''.join([x for x in (card[Card.number] or '') if x.isdigit()] or ['-1'])
                dual.append((card, int(digs)))
            dual.sort(key=lambda x: x[1])
            bag.prefered = dual[0][0]
        else:
            bag.prefered = card_val[0][0]

timer_end: float = time.time() - timer_start
print(f'{crm_white}{len(NAME_BAG)}{end} cards loaded into ram in {crm_white}{round(timer_end, 2)}{end} seconds', flush=True)
