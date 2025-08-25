import sys, os, time
if all(word in ''.join(sys.argv[1:]) for word in ['update', 'database']):
    from useful.update_database import make_quick_db
    make_quick_db()

from useful.thingeys import findings_printout_v1,findings_printout_v2
from useful.breakdown import SmartVal, SmartArgs,smartkeys,MTG_TYPES,RARITIES
from useful.termcols import end, orange
from useful.database import Card,SETCODE_EXPNAME,EXPNAME_SETCODE,NAME_BAG
from useful.thingeys import top_garret_v1,btm_garret_v1,printout_help,printout_breakdown

def tweak_query(text: str) -> str:
    parts: list[str] = []
    for part in [part for part in text.split() if part]:
        if part in ['M']:
            parts.append('rarity=mythic')
        elif part in ['R']:
            parts.append('rarity=rare')
        elif part in ['U']:
            parts.append('rarity=uncommon')
        elif part in ['C']:
            parts.append('rarity=common')

        elif 3 >= len(part) <= 4 and part[0].isupper():
            parts.append(f'setcode={part}')
        elif part[0].isupper() and part[0].isalpha():
            parts.append(f'expansion={part}')

        else:
            parts.append(part)

    return ' '.join(parts).lower()


def get_user_input() -> str:
    return input(f'\n{orange}SEARCH TERMS:{end} ')

CLEAR_SCREEN = lambda: os.system('clear') if os.sep in '/' else os.system('cls')
dev_q: str = '"brokkos,"'
q: str = '//DEV'
CLEAR_SCREEN()
printout_help()

while True:
    q: str = dev_q if '//DEV' in q and os.path.exists('/mnt/ramdisk') else get_user_input()
    q = tweak_query(text=q)
    if not q:
        break

    CLEAR_SCREEN()
    start: float = time.time()
    smvs: list[SmartVal] = SmartArgs(query=q, smartkeys=smartkeys).results
    allowed_setcodes: set[str] = {setcode for setcode in SETCODE_EXPNAME}
    for smv in smvs:
        key, sep, val = smv
        if key in ['expansion']:
            exp_bool: dict = {expname: True for expname in EXPNAME_SETCODE.keys()}
            for expname in exp_bool:
                if '==' in sep:
                    exp_bool[expname] = val in expname.lower()
                elif '!=' in sep:
                    exp_bool[expname] = val not in expname.lower()
                elif '>=' in sep:
                    exp_bool[expname] = val >= expname.lower()
                elif '<=' in sep:
                    exp_bool[expname] = val <= expname.lower()
                elif '>' in sep:
                    exp_bool[expname] = val > expname.lower()
                elif '<' in sep:
                    exp_bool[expname] = val < expname.lower()

            for expname, good in exp_bool.items():
                if not good and EXPNAME_SETCODE[expname] in allowed_setcodes:
                    allowed_setcodes.remove(EXPNAME_SETCODE[expname])

    findings: list[tuple] = []
    for name, bag in NAME_BAG.items():
        card: tuple = bag.prefered
        cards: list = [x for x in bag.cards if x[Card.setcode] in allowed_setcodes]
        good: bool = any(x[Card.setcode] in allowed_setcodes for x in cards)
        for smv in smvs:
            if not good:
                break

            key, sep, val = smv
            if key in ['power', 'toughness', 'cmc']:

                if key in 'power':
                    ix: int = Card.power
                elif key in 'toughness':
                    ix: int = Card.toughness
                else:
                    ix: int = Card.cmc

                if not isinstance(card[ix], (int, float)):
                    good = '!=' in sep
                    continue

                if '==' in sep:
                    good = card[ix] == val
                elif '!=' in sep:
                    good = card[ix] != val
                elif '>=' in sep:
                    good = card[ix] >= val
                elif '<=' in sep:
                    good = card[ix] <= val
                elif '>' in sep:
                    good = card[ix] > val
                elif '<' in sep:
                    good = card[ix] < val

            elif key in ['name', 'specbox', 'type', 'artist']:

                if key in 'name':
                    ix: int = Card.name
                elif key in 'artist':
                    ix: int = Card.artist
                else:
                    ix: int = Card.type

                if not isinstance(card[ix], str):
                    good = '!=' in sep
                    continue

                if '==' in sep:
                    good = val in card[ix].lower()
                elif '!=' in sep:
                    good = val not in card[ix].lower()
                elif '>=' in sep:
                    good = val >= card[ix].lower()
                elif '<=' in sep:
                    good = val <= card[ix].lower()
                elif '>' in sep:
                    good = val > card[ix].lower()
                elif '<' in sep:
                    good = val < card[ix].lower()

            elif key in ['setcode']:
                ix: int = Card.setcode

                if '==' in sep:
                    cards = [x for x in cards if val in x[ix].lower()]
                elif '!=' in sep:
                    cards = [x for x in cards if val not in x[ix].lower()]
                elif '>=' in sep:
                    cards = [x for x in cards if val >= x[ix].lower()]
                elif '<=' in sep:
                    cards = [x for x in cards if val <= x[ix].lower()]
                elif '>' in sep:
                    cards = [x for x in cards if val > x[ix].lower()]
                elif '<' in sep:
                    cards = [x for x in cards if val < x[ix].lower()]

                good = any(cards)


            elif key in MTG_TYPES:
                ix: int = Card.types

                if ('==' in sep and val) or ('!=' in sep and not val):
                    cards = [x for x in cards if key in x[ix].lower()]
                else:
                    cards = [x for x in cards if key not in x[ix].lower()]

                good = any(cards)

            elif key in ['textbox', 'keywords', 'artist', 'flavor', 'colors', 'cost']:
                if key in ['textbox']:
                    ix: int = Card.text
                elif key in ['artist']:
                    ix: int = Card.artist
                elif key in ['flavor']:
                    ix: int = Card.flavor_text
                elif key in ['colors']:
                    ix: int = Card.color_identity
                elif key in ['cost']:
                    ix: int = Card.mana_cost
                else:
                    ix: int = Card.keywords

                if not isinstance(card[ix], str):
                    good = '!=' in sep
                    continue

                if sep in '==':
                    good = val in card[ix].lower()
                else:
                    good = val not in card[ix].lower()

            elif key in ['rarity'] or key in RARITIES:
                ix: int = Card.rarity

                if key in RARITIES:
                    if ('==' in sep and val) or ('!=' in sep and not val):
                        cards = [x for x in cards if x[ix].startswith(key)]
                    else:
                        cards = [x for x in cards if not x[ix].startswith(key)]
                else:
                    if sep in '==':
                        good = val in card[ix].lower()
                    else:
                        good = val not in card[ix].lower()


        if not good or not cards:
            continue
        elif bag.prefered in cards:
            card = bag.prefered
        else:
            card = cards[0]

        findings.append((bag, card))


    show_ansi: bool = '--no-ansi' not in sys.argv[1:]
    show_ansi = len(findings) <= 20 and show_ansi
    show_ansi = any(smv.key in 'ansi' and smv.sep in '==' for smv in smvs) or show_ansi
    if show_ansi:
        top_garret_v1(start, findings)
        findings_printout_v2(findings)
    else:
        findings_printout_v1(findings)
        top_garret_v1(start, findings)

    printout_breakdown(breakdown=smvs)



