from useful.termcols import *
from useful.database import Card, SETCODE_TIME,SETCODE_EXPNAME
from useful.termcols import lgt_yellow,lgt_rose,lgt_blue,lgt_green
from useful.breakdown import smartkeys,IntKey,StrKey,BoolKey
import gzip,io,random,time


def spaces(card: tuple, cards: list[tuple], index: int) -> str:
    max_len: int = max(len(x[index] or '') for x in cards)
    return ' ' * (max_len - len(card[index] or ''))

def details_equals(details: str, length: int = 128) -> str:
    beg_num: int = 236
    end_num: int = 255

    half: int = length // 2
    jump: int = half // (end_num - beg_num)
    parts: list[str] = []
    num: int = beg_num
    while num < end_num:
        for n in range(max(jump, 1)):
            parts.append(f'\33[38:5:{num}m')
        num += 1

    return '='.join(parts) + f'[ {details} ]' + '='.join(reversed(parts)) + end


def unpack_ansi(ansi_raw: bytes) -> dict:
    val_char: dict[int, str] = {val: '' for val in range(256)}
    chars: list[str] = list('Iiîï1lĺÛüÜû')
    random.seed('SAME CHAR EACH TIME')
    for val in val_char:
        ix: int = random.randint(a=0, b=len(chars) - 1)
        val_char[val]: str = chars[ix]

    input_buffer = io.BytesIO(ansi_raw)
    with gzip.GzipFile(fileobj=input_buffer, mode="rb") as gz:
        raw_string: str = gz.read().decode("utf-8")
        raw_rows: list[str] = raw_string.split(',')
        rows: dict = {n: [int(x) for x in row.split()] for n, row in enumerate(raw_rows)}
        for y, cols in rows.items():
            for n, col in enumerate(cols):
                cols[n]: str = f'\033[38;5;{col}m{val_char[col]}'

        return rows

def printout_name_and_setcodes(bag: object, card: tuple, cards: list):
    codes_col: str = very_drk_gray
    this_code_col: str = salmon if not bag.is_stupid else drk_orange

    setcodes: list[str] = list({x[Card.setcode] for x in bag.cards})
    setcodes.sort(key=lambda x: SETCODE_TIME[x])

    if len(setcodes) > 10:
        if card[Card.setcode] in setcodes[:5]:
            tmp: list = [f'{codes_col if x != card[Card.setcode] else this_code_col}{x}{end}' for x in setcodes[:5]]
            printings: str = f'{codes_col}, '.join(tmp)
            printings += f' {codes_col}...{len(setcodes) - 5} MORE!{end}'
        else:
            ix: int = max(n for n, setcode in enumerate(setcodes) if setcode == card[Card.setcode])
            tmp: list = [f'{codes_col if x != card[Card.setcode] else this_code_col}{x}{end}' for x in
                         setcodes[ix - 3: ix + 3]]
            printings: str = f'{codes_col}.... ' + f'{codes_col}, '.join(tmp)
            printings += f' {codes_col}....{len(setcodes) - ((ix + 2) - (ix - 2))} MORE!{end}'
    else:
        tmp: list = [f'{codes_col if x != card[Card.setcode] else this_code_col}{x}' for x in setcodes]
        printings: str = f'{codes_col}, '.join(tmp)

    spc1: str = spaces(card, cards, Card.name)
    print(f'{crm_white}{card[Card.name]} {spc1} {printings}{end}')

def trimmed_text(text: str, x1: int, x2: int) -> str:
    text_len: int = x2 - x1
    while 4 > len(text) > text_len:
        text = text[:-4] + '...'
    return text

def title_coords(card: tuple, rows: dict, *args, **kwargs) -> tuple[int, int, int, int]:
    bleed: int = 6
    x1: int = bleed - 1
    x2: int = len(rows[0]) - bleed
    y1: int = 2
    y2: int = y1
    return x1, y1, x2, y2

def type_coords(card: tuple, rows: dict, *args, **kwargs) -> tuple[int, int, int, int]:
    bleed: int = 6
    x1: int = bleed - 1
    x2: int = len(rows[0]) - bleed
    y1: int = int(len(rows) * 0.59)
    y2: int = y1
    return x1, y1, x2, y2

def power_tougness_coords(card: tuple, rows: dict, *args, **kwargs) -> tuple[int, int, int, int]:
    bleed: int = 6
    x1: int = bleed - 1
    x2: int = len(rows[0]) - bleed
    y1: int = len(rows) - 3
    y2: int = y1
    return x1, y1, x2, y2

def manacost_coords(card: tuple, rows: dict, *args, **kwargs) -> tuple[int, int, int, int]:
    bleed: int = 4
    x1: int = bleed - 1
    x2: int = len(rows[0]) - bleed
    y1: int = 1
    y2: int = y1
    return x1, y1, x2, y2

def text_coords(card: tuple, rows: dict, *args, **kwargs) -> tuple[int, int, int, int]:
    _, y1, _, _ = type_coords(card, rows)
    bleed: int = 6
    x1: int = bleed - 1
    x2: int = len(rows[0]) - bleed
    y1: int = y1 + 2
    y2: int = max(y1, len(rows) - 5)
    return x1, y1, x2, y2

def void_stamp(rows: dict, x1: int, y1: int, x2: int, y2: int, void: str = ' '):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            rows[y][x] = void

def inject_any(rows: dict, text: str, x1: int, y1: int, x2: int, y2: int, color: str = crm_white, center: bool = True):
    jump_in: int = 2
    x_range: int = x2 - x1
    x_shift: int = (x1 + (x_range - len(text)) // 2) if center else (x1 + jump_in)
    y_shift: int = (y2 - y1) // 2
    text = trimmed_text(text, x1, x2)
    for n, char in enumerate(text):
        rows[y1 + y_shift][n + x_shift] = f'{color}{char}'

def inject_title(card: tuple, rows: dict):
    text: str = card[Card.name]
    void_stamp(rows, *title_coords(card, rows))
    inject_any(rows, text, *title_coords(card, rows))

def inject_type(card: tuple, rows: dict):
    text: str = card[Card.type]
    coords = type_coords(card, rows)
    void_stamp(rows, *coords)
    inject_any(rows, text, *coords, center=False)


def inject_rarity(card: tuple, rows: dict):
    rarity: str = (card[Card.rarity] or ':(').upper()
    if rarity in ['MYTHIC']:
        col: str = mythic_col
    elif rarity in ['RARE']:
        col: str = rare_col
    elif rarity in ['UNCOMMON']:
        col: str = uncommon_col
    elif rarity in ['COMMON']:
        col: str = common_col
    else:
        return

    text: str = '{' + rarity + '}'
    x1, y1, x2, y2 = type_coords(card, rows)
    if all(void in ' ' for void in rows[y1][x2 - (1 + len(text))]):
        void_stamp(rows, x2 - (1 + len(text)), y1, x2, y2)
        for n, char in enumerate(text):
            rows[y1][n + (x2 - (1 + len(text)))] = f'{col}{char}{end}'

def inject_textbox(card: tuple, rows: dict):
    texts: list[str] = (card[Card.text] or '').split('\n')
    x1, y1, x2, y2 = text_coords(card, rows)
    text_rows: dict[int, str] = {}
    for text in texts:
        width: int = x2 - x1 - 1
        while len(text) >= width:
            tmp_text: str = text[:width].strip()
            tmp_text = tmp_text[:tmp_text.rfind(' ')].strip() if  ' ' in tmp_text else tmp_text
            text_rows[len(text_rows)]: str = tmp_text
            text = text[len(tmp_text):].strip()

        text_rows[len(text_rows)]: str = text
        text_rows[len(text_rows)]: str = ''

    void_stamp(rows, x1, y1, x2, y2)
    if len(text_rows) <= (y2 - y1):
        in_clamp: bool = False
        for y, text in text_rows.items():
            for n, char in enumerate(text):
                if char in ['{', '}']:
                    in_clamp = not in_clamp
                    color: str = clamp_col

                elif in_clamp:
                    if char in 'W':
                        color: str = w_col
                    elif char in 'U':
                        color: str = u_col
                    elif char in 'B':
                        color: str = b_col
                    elif char in 'R':
                        color: str = r_col
                    elif char in 'G':
                        color: str = g_col
                    else:
                        color: str = crm_white
                else:
                    color: str = crm_white

                rows[y + y1 + 1][x1 + n + 2] = f'{color}{char}'

def inject_pt(card: tuple, rows: dict):
    if card[Card.power] is None or card[Card.toughness] is None:
        if 'Planeswalker' in (card[Card.types] or ''):
            text: str = f' {int(card[Card.loyalty] or 0)} '
            color: str = '\33[38:5:226m'
        else:
            return
    else:
        power: float = card[Card.power]
        toughness: float = card[Card.toughness]
        text: str = f' {int(power)} / {int(toughness)} '
        color: str = '\33[38:5:118m'

    x1, y1, x2, y2 = power_tougness_coords(card, rows)
    x1 = x2 - len(text) - 1
    void_stamp(rows, x1, y1, x2, y2)
    inject_any(rows, text, x1, y1, x2, y2, center=False, color=color)

def inject_manacost(card: tuple, rows: dict):
    if not card[Card.mana_cost]:
        return

    mana_cost: str = card[Card.mana_cost]
    x1, y1, x2, y2 = manacost_coords(card, rows)
    x1 = x2 - len(mana_cost) - 1
    void_stamp(rows, x1, y1, x2, y2)

    for n, char in enumerate(mana_cost):
        if char in 'W':
            color: str = w_col
        elif char in 'U':
            color: str = u_col
        elif char in 'B':
            color: str = b_col
        elif char in 'R':
            color: str = r_col
        elif char in 'G':
            color: str = g_col
        elif char in ['{', '}']:
            color: str = clamp_col
        else:
            color: str = end

        inject_any(rows, char, x1 + n, y1, x2, y2, center=False, color=color)

def printout_ansi(card: tuple):
    rows: dict = unpack_ansi(card[Card.ansi])

    inject_title(card, rows)
    inject_type(card, rows)
    inject_textbox(card, rows)
    inject_rarity(card, rows)
    inject_pt(card, rows)
    inject_manacost(card, rows)

    for y, cols in rows.items():

        void_col: str = '\33[38:5:233m'
        void_char: str = '#'
        cols = [x if ' ' not in x else void_col + void_char for x in cols]  # expose void?

        outline_col: str = '\33[38:5:251m'
        if y == 0:
            line: str = '─' * (len(cols) - 4)
            print(f'{outline_col}┌{line}┐')
        elif y == len(rows) - 1:
            setcode: str = card[Card.setcode]
            expname: str = SETCODE_EXPNAME[setcode]
            line: str = '─' * 2
            line += f'[ {expname} ]'
            line += '─' * ((len(cols) - 4) - len(line))
            print(f'{outline_col}└{line}┘')
        else:
            row: str = ''.join(cols[2:-2]) + end
            print(f'{outline_col}│{row}{outline_col}│{end}')

def findings_printout_v1(findings: list):
    findings.sort(key=lambda x: x[1][Card.setcode])
    findings.sort(key=lambda x: x[1][Card.name])
    cards: list[tuple] = [x[1] for x in findings]
    for bag, card in findings:
        printout_name_and_setcodes(bag, card, cards)

def findings_printout_v2(findings: list):
    findings.sort(key=lambda x: x[1][Card.setcode])
    findings.sort(key=lambda x: x[1][Card.name])
    cards: list[tuple] = [x[1] for x in findings]
    for bag, card in findings:
        printout_name_and_setcodes(bag, card, cards)

    print('')
    for bag, card in findings:
        if card[Card.ansi]:
            printout_ansi(card)
            print('\n')


def top_garret_v1(start_time: float, findings: list):
    timer_end: float = time.time() - start_time
    details: str = f'{lgt_yellow}FOUND {len(findings)} CARDS IN {round(timer_end, 2)}s'
    details_top: str = (f'{details_equals(details, length=128)}\n'
                        )
    print(details_top)

def btm_garret_v1(start_time: float, findings: list):
    timer_end: float = time.time() - start_time
    details: str = f'{lgt_yellow}FOUND {len(findings)} CARDS IN {round(timer_end, 2)}s'
    details_btm: str = (f'{details_equals(details, length=128)}\n'
                        )
    print(details_btm)

def printout_breakdown(breakdown: list):
    outs: dict = {}
    for smv in breakdown:
        key, sep, val = smv
        if key not in outs:
            outs[key]: dict = {}

        if sep not in outs[key]:
            outs[key][sep]: list = []

        outs[key][sep].append(str(val))

    final: str = f'{orange}RECENT TERMS:{end} '
    for n, key in enumerate(outs):
        final += ' ' if n else ''
        for n, sep in enumerate(outs[key]):
            final += ' ' if n else ''
            final += f'{end}{key}{drk_gray}{sep}'
            for n, val in enumerate(outs[key][sep]):
                final += ',' if n else ''
                if ' ' in str(val):
                    final += f'{drk_white}"{val}"{end}'
                else:
                    final += f'{drk_white}{val}{end}'

    print(final, end='', flush=True)

def printout_help():
    print(details_equals(' ' * len('SEARCH AHEAD MOTHERFCKR')))

    intkeys: list = [smk for smk in smartkeys if isinstance(smk, IntKey)]
    strkeys: list = [smk for smk in smartkeys if isinstance(smk, StrKey)]
    boolkeys: list = [smk for smk in smartkeys if isinstance(smk, BoolKey)]
    [keylist.sort(key=lambda x: x.key) for keylist in (intkeys, strkeys, boolkeys)]

    key_col: str = lgt_blue
    sep_col: str = lgt_rose
    txt_col: str = salmon

    for keylist in [strkeys, intkeys, boolkeys]:

        keywords: list = [x.key for x in keylist]
        seps: tuple = keylist[0].seps
        print(f'KEYWORDS: {key_col}{" ".join(keywords)}{end}')
        print(f'SEPARATORS: {sep_col}{" ".join(seps)}{end}')

        if isinstance(keylist[0], StrKey):
            print(f'EXAMPLE: {key_col}name{sep_col}={txt_col}emrakul,the{end} or {key_col}name{sep_col}={txt_col}"emrakul, the" {key_col}artist{sep_col}={txt_col}mark_tedin{end}')

        elif isinstance(keylist[0], IntKey):
            print(f'EXAMPLE: {key_col}pow{sep_col}<={txt_col}8 {key_col}tough{sep_col}={txt_col}5 {key_col}cmc{sep_col}!=5{end}')

        else:
            print(f'EXAMPLE: {key_col}inst{sep_col}={txt_col}false{end} or just lone {key_col}inst{end} which defaults to true')
        print('')

    print(f'\nA-NOTE: name is the default keyword that text that cannot be matched elsewhere automatically defaults to meaning: {txt_col}emrakul the a tor{end} will be read as {key_col}name{sep_col}={txt_col}emrakul_the_a_tor{end} which returns {crm_white}Emrakul, the Aeons Torn{end}')
    print(f'SAMPLE: {lgt_green}type!=instant creature ra k l p>=10 em t=15 cmc>10 cmc!=14 artist=tedin creature keyw=flying,an,tor text=cast_when_turn_extra{end} will return {crm_white}Emrakul, the Aeons Torn{end}')
    print(details_equals(' ' * len('SEARCH AHEAD MOTHERFCKR')))



