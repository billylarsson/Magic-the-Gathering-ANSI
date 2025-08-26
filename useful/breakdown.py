class SmartVal:
    def __init__(self, key: str, sep: str, val):
        self.key: str = key
        self.sep: str = '==' if sep in '=' else sep
        self.op, self.operator = self.sep, self.sep  # assuming op/operator would be used by devs
        self.val = val

    def __iter__(self):
        args: tuple = self.key, self.sep, self.val
        return iter(args)


class SmartKey:
    trailing: bool = False
    seps: tuple = '==', '!=', '>=', '<=', '>', '<', '='
    def __init__(self,
                 key: str,
                 keys = None,
                 seps: tuple | None = None,
                 default: bool = False,
                 auto_sep: str | None = '==',
                 min_reach: int = 0,
                 ):
        self.key: str = key
        self.keys: set = {self.key}
        if isinstance(keys, (set, tuple, list, dict)):
            [self.keys.add(key) for key in keys]

        self.seps: tuple = seps or self.seps
        self.default: bool = default
        self.auto_sep: str | None = auto_sep
        self.min_reach: int = max(1, (min_reach or len(self.key)))
        self.min_reach = min(self.min_reach, len(self.key))


    def translate_values(self, *args, **kwargs) -> list[SmartVal]:
        vals: list[SmartVal] = []
        return vals

    def next_fwd_stop(self, text: str) -> int:
        marks: list[str] = [' '] + list(self.seps)
        walls: list[int] = [text.find(mark) for mark in marks if mark in text]
        rgt: int = min(walls) if walls else len(text)
        return rgt

    def enough_key_reach(self, fuzzy_key: str) -> bool:
        for any_key in self.keys:
            arm: int = min(len(fuzzy_key), self.min_reach, len(any_key))
            if arm < self.min_reach:
                continue

            for n, char in enumerate(fuzzy_key):
                if n >= len(any_key) or char not in any_key[n]:
                    break
            else:
                if fuzzy_key[:arm] in any_key[:arm]:
                    return True
        return False


    def get_next_sep(self, text: str) -> str | None:
        for sep in self.seps:
            if text.startswith(sep):
                return sep
        return self.auto_sep


class BoolKey(SmartKey):
    key_type = bool
    trailing: bool = False
    seps: tuple = '==', '!=', '=',

    def translate_values(self, key: str, sep: str, text: str, auto_sep: bool = False, **kwargs) -> list[SmartVal]:
        vals: list[SmartVal] = []

        if auto_sep:
            smartval: SmartVal = SmartVal(key, sep, val=True)
            vals.append(smartval)
        else:
            if text in ['true', 'false']:
                smartval: SmartVal = SmartVal(key, sep, val=text in 'true')
                vals.append(smartval)

        return vals

class IntKey(SmartKey):
    key_type = int
    trailing: bool = True

    def translate_values(self, key: str, sep: str, text: str, limit: int = 100, **kwargs) -> list[SmartVal]:
        vals: list[SmartVal] = []
        if '-' in text:
            parts: list[str] = text.split('-')
            if len(parts) == 2:
                if parts[0].isdigit() and parts[1].isdigit():
                    beg: int = min(int(parts[0]), int(parts[1]))
                    end: int = max(int(parts[0]), int(parts[1]))
                    for val in range(beg, min(end, beg + limit) + 1):
                        smv: SmartVal = SmartVal(key, sep, val=val)
                        vals.append(smv)

        else:
            val = text.strip()
            if val and val.isdigit():
                smv: SmartVal = SmartVal(key, sep, val=int(val))
                vals.append(smv)

        return vals

class StrKey(SmartKey):
    key_type = str
    trailing: bool = False

    def translate_values(self, key: str, sep: str, text: str, **kwargs) -> list[SmartVal]:
        vals: list[SmartVal] = []
        text: str = text.strip()
        if text.startswith('"') and text.endswith('"'):
            if len(text) > 2:
                smv: SmartVal = SmartVal(key, sep, val=text[1: -1])
                vals.append(smv)
        else:
            if text:
                smv: SmartVal = SmartVal(key, sep, val=text)
                vals.append(smv)
        return vals

class SmartArgs:
    results: list[SmartVal] = []
    sep_marks: str = ' _,+'

    def __init__(self, query: str, smartkeys: list[SmartKey], singleton: bool = True):
        self.query: str = query
        self.singleton: bool = singleton

        self.smartkeys: list[SmartKey] = [smartkey for smartkey in smartkeys]
        self.smartkeys.sort(key=lambda x: x.key)

        self.results: list[SmartVal] = self.extract_values()
        for smk in self.smartkeys:
            if smk.default and smk.auto_sep:
                msk_query: str = self.masked_quotations(self.query)
                parts: list[str] = ['']
                for n, char in enumerate(msk_query):
                    if char not in self.sep_marks:
                        parts[-1] += self.query[n]

                    elif parts[-1]:
                        parts.append('')

                parts = [f'{smk.key}{smk.auto_sep}{part}' for part in parts if part.strip()]
                if parts:
                    self.query = ' '.join(parts)
                    self.results += self.extract_values()
                    break

        self.results = self.singleton_results(self.results) if singleton else self.results

    def __iter__(self):
        for smartval in self.results:
            yield smartval

    def singleton_results(self, smartvals: list[SmartVal]) -> list[SmartVal]:
        singletons: list[SmartVal] = []
        breakdown: dict = {}
        for smartval in smartvals:
            key, sep, val = smartval.key, smartval.sep, smartval.val
            if key not in breakdown:
                breakdown[key]: dict = {}
            if sep not in breakdown[key]:
                breakdown[key][sep] = set()
            breakdown[key][sep].add(val)

        sorted_keys: list = sorted(list(breakdown.keys()))
        for key in sorted_keys:
            sorted_operators: list = sorted(list(breakdown[key].keys()))
            for operator in sorted_operators:
                types_singleton: set = {str(type(val)) for val in breakdown[key][operator]}
                sorted_types: dict = {str_type: set() for str_type in sorted(types_singleton)}
                for val in breakdown[key][operator]:
                    sorted_types[str(type(val))].add(val)

                for str_type, vals in sorted_types.items():
                    for sorted_val in tuple(sorted(vals)):
                        smartval: SmartVal = SmartVal(key=key, sep=operator, val=sorted_val)
                        singletons.append(smartval)

        return singletons

    def skip_fwd(self, text: str) -> int:
        """returns how many chars in self.sepmarks from the left that needs to be skipped til relevant char appears"""
        return len(text) - len(text.lstrip(self.sep_marks))

    def extract_values(self) -> list[SmartVal]:
        results: list[SmartVal] = []
        poles: list[int] = self.get_poles()
        always_space: set[int] = set()
        lft: int = 0
        while lft < len(self.query):
            query: str = self.masked_quotations(self.query)
            lft += self.skip_fwd(text=query[lft:])
            rgt_poles: list[int] = [pole - 1 for pole in poles if pole - 1 > lft]
            rgt_wall: int = min(rgt_poles) if rgt_poles else len(query)
            for smk in self.smartkeys:
                rgt: int = lft + smk.next_fwd_stop(query[lft: rgt_wall])
                fuzzy_key: str = self.query[lft: rgt]
                if not smk.enough_key_reach(fuzzy_key):
                    continue

                key_lft: int = lft
                key_rgt: int = rgt

                rgt += self.skip_fwd(text=query[rgt:])
                sep: str | None = smk.get_next_sep(query[rgt: rgt_wall])
                sep_present: bool = sep and query[rgt:].startswith(sep)
                using_auto_sep: bool = sep and not sep_present

                if sep_present:
                    lft = (rgt + query[rgt:].find(sep) + len(sep))
                elif using_auto_sep:
                    lft = rgt if smk.trailing else key_lft
                else:
                    continue

                lft += self.skip_fwd(text=query[lft:])
                text: str = query[lft: rgt_wall]
                if not text.lstrip(self.sep_marks):
                    continue

                if any(mark in text for mark in self.sep_marks):
                    marks: list = [(mark, text.find(mark)) for mark in self.sep_marks if mark in text]
                    marks.sort(key=lambda x: x[1])
                    rgt_sep, rgt_ix = marks[0]
                    text: str = self.query[lft: lft + rgt_ix]
                    space_sep: bool = rgt_sep in ' '
                    if not text.lstrip(self.sep_marks):
                        continue
                else:
                    text: str = self.query[lft: rgt_wall]
                    space_sep: bool = False

                kwgs = dict(key=smk.key, sep=sep, text=text, auto_sep=using_auto_sep, limit=100)
                smartvals: list[SmartVal] = smk.translate_values(**kwgs)
                if not smartvals:
                    continue

                results += smartvals
                if not space_sep or smk.trailing:
                    [always_space.add(ix) for ix in range(key_lft, lft)]
                    spaces: str = ' ' * len(query[lft: lft + len(text)])
                    self.query = self.query[:lft] + spaces + self.query[lft + len(text):]
                    lft = key_lft
                    break
                else:
                    spaces: str = ' ' * len(query[key_lft: lft + len(text)])
                    self.query = self.query[:key_lft] + spaces + self.query[lft + len(text):]
                    lft = key_lft
                    break

            else:
                self.query = ''.join(char if ix not in always_space else ' ' for ix, char in enumerate(self.query))
                lft = rgt_wall

        return results

    def masked_quotations(self, text: str, maskchar: str = 'x') -> str:
        while text.count('"') >= 2:
            lft: int = text.find('"')
            rgt: int = text[lft + 1:].find('"') + lft + 2
            exs: str = maskchar * (rgt - lft)
            text = text[:lft] + exs + text[rgt:]

        return text


    def get_poles(self) -> list[int]:
        lft: int = 0
        poles: list[int] = []
        while lft < len(self.query):
            query: str = self.masked_quotations(self.query)
            lft += self.skip_fwd(text=query[lft:])

            for smk in self.smartkeys:
                rgt: int = lft + smk.next_fwd_stop(query[lft:])
                fuzzy_key: str = self.query[lft: rgt]
                if not smk.enough_key_reach(fuzzy_key):
                    continue

                poles.append(lft)
                lft = rgt
                break

            else:
                if ' ' in query[lft:]:
                    lft += query[lft:].find(' ')
                else:
                    break

        return poles

smartkeys: list[SmartKey] = [
    IntKey(key='power', min_reach=1),
    IntKey(key='toughness', min_reach=1),
    IntKey(key='cmc'),

    StrKey(key='name', min_reach=1, default=True),
    StrKey(key='setcode', keys={'code'}, min_reach=3),
    StrKey(key='type', keys={'spec', 'specbox', 'type'}),
    StrKey(key='expansion', min_reach=3),
    StrKey(key='artist'),
    StrKey(key='colors', min_reach=3, seps=BoolKey.seps),
    StrKey(key='cost', keys={'costs'}, seps=BoolKey.seps),
    StrKey(key='textbox', min_reach=4, seps=BoolKey.seps),
    StrKey(key='keywords', min_reach=3, seps=BoolKey.seps),
    StrKey(key='rarity', seps=BoolKey.seps),

    BoolKey(key='ansi')
]
MTG_TYPES: set[str] = {'artifact', 'battle', 'creature', 'enchantment', 'instant', 'kindred', 'land', 'planeswalker', 'sorcery', 'tribal'}
RARITIES: set[str] = {'mythic', 'rare', 'uncommon', 'common'}
smartkeys += [BoolKey(mtg_type, min_reach=4) for mtg_type in MTG_TYPES]
smartkeys += [BoolKey(rarity, min_reach=4) for rarity in RARITIES]
