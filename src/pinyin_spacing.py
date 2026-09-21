from __future__ import annotations

import unicodedata

SYLLABLES = {
    "a", "ai", "an", "ang", "ao",
    "ba", "bai", "ban", "bang", "bao", "bei", "ben", "beng",
    "bi", "bian", "biang", "biao", "bie", "bin", "bing", "bo", "bu",
    "ca", "cai", "can", "cang", "cao", "ce", "cen", "ceng",
    "cha", "chai", "chan", "chang", "chao", "che", "chen", "cheng",
    "chi", "chong", "chou", "chu", "chua", "chuai", "chuan", "chuang", "chui", "chun", "chuo",
    "ci", "cong", "cou", "cu", "cuan", "cui", "cun", "cuo",
    "da", "dai", "dan", "dang", "dao", "de", "dei", "den", "deng",
    "di", "dia", "dian", "diang", "diao", "die", "ding", "diu",
    "dong", "dou", "du", "duan", "dui", "dun", "duo",
    "e", "ei", "en", "eng", "er",
    "fa", "fan", "fang", "fei", "fen", "feng", "fiao",
    "fo", "fou", "fu", "ga", "gai", "gan", "gang", "gao",
    "ge", "gei", "gen", "geng", "gong", "gou",
    "gu", "gua", "guai", "guan", "guang", "gui", "gun", "guo",
    "ha", "hai", "han", "hang", "hao", "he", "hei", "hen", "heng",
    "hong", "hou", "hu", "hua", "huai", "huan", "huang", "hui", "hun", "huo",
    "ji", "jia", "jian", "jiang", "jiao", "jie", "jin", "jing", "jiong", "jiu", "ju", "juan", "jue", "jun",
    "ka", "kai", "kan", "kang", "kao", "ke", "kei", "ken", "keng",
    "kong", "kou", "ku", "kua", "kuai", "kuan", "kuang", "kui", "kun", "kuo",
    "la", "lai", "lan", "lang", "lao", "le", "lei", "leng",
    "li", "lia", "lian", "liang", "liao", "lie", "lin", "ling", "liu", "long", "lou",
    "lu", "luan", "lue", "lun", "luo",
    "ma", "mai", "man", "mang", "mao", "me", "mei", "men", "meng",
    "mi", "mian", "miao", "mie", "min", "ming", "miu", "mo", "mou", "mu",
    "na", "nai", "nan", "nang", "nao", "ne", "nei", "nen", "neng",
    "ni", "nia", "nian", "niang", "niao", "nie", "nin", "ning", "niu",
    "nong", "nou", "nu", "nuan", "nue", "nun", "nuo",
    "pa", "pai", "pan", "pang", "pao", "pei", "pen", "peng",
    "pi", "pian", "piao", "pie", "pin", "ping", "po", "pou", "pu",
    "qi", "qia", "qian", "qiang", "qiao", "qie",
    "qin", "qing", "qiong", "qiu", "qu", "quan", "que", "qun",
    "ran", "rang", "rao", "re", "ren", "reng", "ri", "rong", "rou",
    "ru", "rua", "ruan", "rui", "run", "ruo",
    "sa", "sai", "san", "sang", "sao", "se", "sei", "sen", "seng",
    "sha", "shai", "shan", "shang", "shao", "she", "shei", "shen", "sheng", "shi",
    "shong", "shou", "shu", "shua", "shuai", "shuan", "shuang", "shui", "shun", "shuo",
    "si", "song", "sou", "su", "suan", "sui", "sun", "suo",
    "ta", "tai", "tan", "tang", "tao", "te", "tei", "teng",
    "ti", "tian", "tiao", "tie", "ting", "tong", "tou",
    "tu", "tuan", "tui", "tun", "tuo",
    "wa", "wai", "wan", "wang", "wei", "wen", "weng", "wo", "wu",
    "xi", "xia", "xian", "xiang", "xiao", "xie", "xin", "xing", "xiong", "xiu", "xu", "xuan", "xue", "xun",
    "ya", "yai", "yan", "yang", "yao", "ye", "yi", "yin", "ying",
    "yo", "yong", "you", "yu", "yuan", "yue", "yun",
    "za", "zai", "zan", "zang", "zao", "ze", "zei", "zen", "zeng",
    "zha", "zhai", "zhan", "zhang", "zhao", "zhe", "zhei", "zhen", "zheng",
    "zhi", "zhong", "zhou", "zhu", "zhua", "zhuai", "zhuan", "zhuang", "zhui", "zhun", "zhuo",
    "zi", "zong", "zou", "zu", "zuan", "zui", "zun", "zuo",
    "n", "ng", "m", "hm", "hng", "o",
}

MAX_SYLLABLE_LEN = max(len(s) for s in SYLLABLES)


def _base_char(c: str) -> str:
    decomposed = unicodedata.normalize("NFD", c)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return (stripped or c).lower()


def _toneless(reading: str) -> str:
    return "".join(_base_char(c) for c in reading)


def _find_split(base: str, target: int) -> list[int] | None:
    n = len(base)
    if n == 0:
        return None
    dp: list[dict[int, int]] = [{} for _ in range(n + 1)]
    dp[0][0] = -1
    for i in range(1, n + 1):
        for j in range(max(0, i - MAX_SYLLABLE_LEN), i):
            if base[j:i] not in SYLLABLES:
                continue
            for count in dp[j]:
                dp[i].setdefault(count + 1, j)
    if target not in dp[n]:
        return None
    bounds = []
    i, count = n, target
    while i > 0:
        j = dp[i][count]
        bounds.append(i)
        i, count = j, count - 1
    bounds.reverse()
    return bounds[:-1]


def space_pinyin(word: str, reading: str) -> str:
    if not reading or " " in reading:
        return reading
    base = _toneless(reading)
    if not base.isalpha():
        return reading
    n_chars = len(word)
    for target in [n_chars, *range(n_chars - 1, 0, -1)]:
        bounds = _find_split(base, target)
        if bounds is not None:
            parts = []
            start = 0
            for b in bounds:
                parts.append(reading[start:b])
                start = b
            parts.append(reading[start:])
            return " ".join(parts)
    return reading
