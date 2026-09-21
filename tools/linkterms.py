# -*- coding: utf-8 -*-
"""本文中の仏教用語の初出を glossary.html の該当項目へリンクする。

使い方（html が並ぶディレクトリで実行する）:
    python3 tools/linkterms.py            # 何をリンクするか一覧表示するだけ
    python3 tools/linkterms.py --write    # 実際にファイルを書き換える

- リンクするのは 1ページにつき用語ごとに初出の1か所だけ。
- すでに <a> になっている箇所、見出し(h1-h3)、SVG、経文の原文(.sutra)、
  アイブロウやカード見出し(.who / .who-sub)は対象外。
- 用語を増やすときは TERMS に (表記, glossary.html の dt id, 追加の正規表現) を足す。
- リンク済みのファイルに再実行しても、既にあるリンクを初出として数えるので増えない。
"""
import re, sys, glob, io

# (表記, 用語集のid, 追加の正規表現パターン or None)
TERMS = [
    ("輪廻","g-rinne",None),("業","g-gou",r"(?<![作事産正営])業"),("解脱","g-gedatsu",None),
    ("ヴェーダ","g-veda",None),("ウパニシャッド","g-upanishad",None),("ブラフマン","g-brahman",None),
    ("アートマン","g-atman",None),("沙門","g-shamon",None),
    ("四聖諦","g-shishotai",None),("四諦","g-shishotai",None),("八正道","g-hasshodo",None),
    ("三法印","g-sanboin",None),("無常","g-mujou",None),("無我","g-muga",None),("縁起","g-engi",None),
    ("無明","g-mumyou",None),("渇愛","g-katsuai",None),("煩悩","g-bonnou",None),("三毒","g-sandoku",None),
    ("五蘊","g-goun",None),("涅槃","g-nehan",None),("阿羅漢","g-arakan",None),("部派","g-buha",None),
    ("アビダルマ","g-abidharma",None),("止観","g-shikan",None),
    ("大乗","g-daijou",None),("菩薩","g-bosatsu",r"(?<![在音蔵])菩薩"),("六波羅蜜","g-ropparamitsu",None),
    ("空","g-kuu",r"空(?![海間])"),("色即是空","g-shikisoku",None),("空即是色","g-shikisoku",None),
    ("般若波羅蜜多","g-hannya",r"般若波羅蜜多?"),("無所得","g-musho",None),("仏性","g-busshou",None),
    ("如来蔵","g-nyoraizou",None),("唯識","g-yuishiki",None),("一乗","g-ichijou",None),
    ("教相判釈","g-kyousou",None),("末法","g-mappou",None),("法身","g-hosshin",None),
    ("十二因縁","g-junikkien",None),("六根","g-rokkon",None),("六境","g-rokkon",None),("十八界","g-rokkon",None),
    ("密教","g-mikkyou",None),("顕教","g-kengyou",None),("大日如来","g-dainichi",None),
    ("即身成仏","g-sokushin",None),("三密","g-sanmitsu",None),("身密","g-sanmitsu",None),
    ("口密","g-sanmitsu",None),("意密","g-sanmitsu",None),
    ("真言","g-shingon",r"真言(?![宗律])"),("印","g-in",r"印(?=を結|契)"),
    ("曼荼羅","g-mandara",r"(?<!立体)曼荼羅"),("マンダラ","g-mandara",None),
    ("胎蔵界","g-taizou",None),("金剛界","g-kongoukai",None),("立体曼荼羅","g-ritsutai",None),
    ("灌頂","g-kanjou",None),("加持","g-kaji",None),("入我我入","g-nyuuga",None),("護摩","g-goma",None),
    ("大欲","g-taiyoku",None),("密厳国土","g-mitsugon",None),("光明真言","g-koumyou",None),
    ("土砂加持","g-doshakaji",None),
    ("自力","g-jiriki",None),("他力","g-tariki",None),("絶対他力","g-zettai",None),
    ("阿弥陀仏","g-amida",None),("本願","g-hongan",None),("念仏","g-nenbutsu",None),
    ("専修念仏","g-senju",None),("往生","g-oujou",None),("浄土","g-jodo",r"浄土(?![宗真三])"),
    ("悪人正機","g-akunin",None),("凡夫","g-bonbu",None),("正信偈","g-shoshinge",None),
    ("坐禅","g-zazen",None),("只管打坐","g-shikan-taza",None),("公案","g-koan",None),
    ("修証一等","g-shushou",None),("分別","g-funbetsu",None),("印可","g-inka",None),
    ("唱題","g-shoudai",None),("題目","g-shoudai",None),("折伏","g-shakubuku",None),
    ("仏国土","g-bukkokudo",None),
    ("法華経","g-hokekyou",None),("般若心経","g-shingyou",None),("大般若経","g-daihannya",None),
    ("大日経","g-dainichikyou",None),("金剛頂経","g-kongouchou",None),("理趣経","g-rishukyou",None),
    ("浄土三部経","g-sanbukyou",None),("即身成仏義","g-sokushingi",None),("十住心論","g-juujuushin",None),
    ("般若心経秘鍵","g-hiken",None),
    ("写経","g-shakyou",None),("三宝","g-sanbou",None),("三阿僧祇劫","g-sanasougi",None),
    ("不動明王","g-fudou",None),("観自在菩薩","g-kanjizai",None),("舎利子","g-sharishi",None),
    ("霊鷲山","g-ryoujusen",None),("究竟涅槃","g-kugyou",None),("心無罣礙","g-shinmu",None),
]
# 長い表記から順に試す
COMPILED = sorted(
    [(t, gid, re.compile(pat if pat else re.escape(t))) for t, gid, pat in TERMS],
    key=lambda x: -len(x[0]))

PROTECT = {"a", "svg", "h1", "h2", "h3", "title", "script", "style"}
# class にこれを含む要素の中身も対象外（経文の原文、アイブロウ、カード見出し）
PROTECT_CLASS = ("sutra", "eyebrow", "who-sub", "who")
VOID = {"br", "hr", "img", "meta", "link", "input", "source", "col"}
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)>")

def linkify(html, report):
    """<main> 内のテキストノードだけを対象に、用語の初出をリンク化する。"""
    m = re.search(r"<main[^>]*>", html)
    if not m:
        return html
    start, end = m.end(), html.rindex("</main>")
    body, out, pos = html[start:end], [], 0
    stack = []          # [(タグ名, 保護するか)]
    # このページで既にリンクした用語id（再実行しても増えないよう既存リンクを拾う）
    used = set(re.findall(r'href="glossary\.html#([^"]+)"', body))

    def protected():
        return any(p for _, p in stack)

    for tag in TAG.finditer(body):
        text = body[pos:tag.start()]
        out.append(text if protected() else scan(text, used, report))
        closing, name, attrs, selfclose = (
            tag.group(1), tag.group(2).lower(), tag.group(3), tag.group(4))
        if closing:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == name:
                    del stack[i:]
                    break
        elif not selfclose and name not in VOID:
            cls = re.search(r'class="([^"]*)"', attrs)
            cls = cls.group(1) if cls else ""
            hit = name in PROTECT or any(c in cls.split() for c in PROTECT_CLASS)
            stack.append((name, hit))
        out.append(tag.group(0))
        pos = tag.end()
    tail = body[pos:]
    out.append(tail if protected() else scan(tail, used, report))
    return html[:start] + "".join(out) + html[end:]

def scan(text, used, report):
    if not text.strip():
        return text
    res, i = [], 0
    while i < len(text):
        hit = None
        for term, gid, rx in COMPILED:
            m = rx.match(text, i)
            if m:
                hit = (m, gid)
                break
        if hit:
            m, gid = hit
            word = m.group(0)
            if gid not in used:
                used.add(gid)
                res.append('<a class="gl" href="glossary.html#%s">%s</a>' % (gid, word))
                report.append((gid, word, text[max(0, i-12):m.end()+12].strip()))
            else:
                res.append(word)          # 長い語に含まれる短い語を二重に拾わない
            i = m.end()
        else:
            res.append(text[i])
            i += 1
    return "".join(res)

if __name__ == "__main__":
    report_all = {}
    for f in sorted(glob.glob("*.html")):
        if f == "glossary.html":
            continue
        s = io.open(f, encoding="utf-8").read()
        rep = []
        new = linkify(s, rep)
        if "--write" in sys.argv:
            io.open(f, "w", encoding="utf-8").write(new)
        report_all[f] = rep
    for f, rep in report_all.items():
        print("=" * 8, f, len(rep))
        for gid, word, ctx in rep:
            print("   %-16s %-8s %s" % (gid, word, ctx.replace("\n", "")))
