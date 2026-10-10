"""MS-102 図解ムック（カード型）の組版スクリプト。

src/mook.css・src/mook.js と、各巻の中身 src/volNN.html から
ms102-mook-volNN-*.html を組み立てる。逆引きドリルは src/drill.html に
全巻の「ここが出る！」を埋め込んで ms102-drill.html を作る。

    python3 ms102/build.py
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=M+PLUS+1:wght@400;500;700;900'
    '&family=Shippori+Mincho+B1:wght@600;800&family=Yusei+Magic&family=Barlow+Condensed:wght@600;800&display=swap">'
)
LEARN = "https://learn.microsoft.com/ja-jp/credentials/certifications/exams/ms-102/"

VOLS = [
    dict(
        key="vol01", no="01", short="テナント", weight="25–30%", chapter="第1章",
        title="MS-102 図解ムック テナント編", out="ms102-mook-vol01-tenant.html",
        feature="テナント運用<br>まるごと図解",
        colors=("#1F57C8", "#D94A14", "#86A8FF", "#FF8248"),
        lines=[
            'すべての章の<em>土台</em>を図で固める',
            "変えられないものは最初に決まる",
            "退職者の処理は順番がすべて",
            "パスワードを戻せるのは誰？",
            "範囲は管理単位、時間は PIM",
        ],
        desc="MS-102 第1章 テナントの展開と管理を、1テーマ1カードの図解ムックにまとめた号。腕試しと暗記カードつき。",
    ),
    dict(
        key="vol02", no="02", short="Entra ID", weight="25–30%", chapter="第2章",
        title="MS-102 図解ムック Entra ID編", out="ms102-mook-vol02-entra.html",
        feature="Entra ID<br>まるごと図解",
        colors=("#0B7A66", "#1F57C8", "#4FD1B5", "#86A8FF"),
        lines=[
            '<em>入口の設計</em>を図で押さえる',
            "同期と認証は、別の話",
            "預ける・聞きに行く・任せる",
            "ブロックが勝ち、除外が勝つ",
            "人が危ないか、今回が怪しいか",
        ],
        desc="MS-102 第2章 Entra ID とアクセス管理を、1テーマ1カードの図解ムックにまとめた号。腕試しと暗記カードつき。",
    ),
    dict(
        key="vol03", no="03", short="Defender XDR", weight="30–35%", chapter="第3章",
        title="MS-102 図解ムック Defender編", out="ms102-mook-vol03-defender.html",
        feature="Defender XDR<br>まるごと図解",
        colors=("#D94A14", "#1C5BD0", "#FF8248", "#82A8FF"),
        lines=[
            '最大の章を<em>図で落とす</em>',
            "4つの Defender、守る相手は1つずつ",
            "メールの守りは「階」で覚える",
            "プリセットはカスタムより強い",
            "「フィッシング＝検疫」の落とし穴",
        ],
        desc="MS-102 第3章 Defender XDR を、1テーマ1カードの図解ムックにまとめた号。腕試しと暗記カードつき。",
    ),
    dict(
        key="vol04", no="04", short="Purview", weight="10–15%", chapter="第4章",
        title="MS-102 図解ムック Purview編", out="ms102-mook-vol04-purview.html",
        feature="Purview<br>まるごと図解",
        colors=("#8A3AA8", "#0B7A66", "#D9A0F2", "#4FD1B5"),
        lines=[
            '紛らわしい用語を<em>図で仕分ける</em>',
            "分類できないものは、守れない",
            "保持の4原則は順番で覚える",
            "30日と93日を混ぜない",
            "操作の記録か、言葉の監視か",
        ],
        desc="MS-102 第4章 Purview とコンプライアンスを、1テーマ1カードの図解ムックにまとめた号。腕試しと暗記カードつき。",
    ),
]

SISTERS = [
    ("hikaeme", "MS-102 控えめの法則", "全章に効く3つの合言葉。最初の1枚に。"),
    ("text", "MS-102 総合テキスト", "このシリーズの底本。細かい条件を確かめたいときに。"),
    ("roles", "M365 ロール百貨店", "誰が何をできるか、ロールの整理に。"),
]


def strip(s):
    s = re.sub(r"<br\s*/?>", " ", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def section(text, name):
    m = re.search(r"<!--%s-->(.*?)<!--/%s-->" % (name, name), text, re.S)
    if not m:
        raise SystemExit("missing section %s" % name)
    return m.group(1).strip()


def color_css(c):
    ls, la, ds, da = c
    return (
        ":root{--spot:%s;--alt:%s}\n"
        '@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--spot:%s;--alt:%s}}\n'
        ':root[data-theme="dark"]{--spot:%s;--alt:%s}\n' % (ls, la, ds, da, ds, da)
    )


CARD_RE = re.compile(r'<article class="card" id="(c\d\d)" data-topic="([^"]+)">(.*?)</article>', re.S)
QA_RE = re.compile(r'<details class="qi"><summary>(.*?)</summary><p class="a">(.*?)</p></details>', re.S)


def parse_cards(cards_html):
    cards = []
    for cid, topic, body in CARD_RE.findall(cards_html):
        q = re.search(r'<h2 class="q">(.*?)</h2>', body, re.S)
        c = re.search(r'<p class="catch">(.*?)</p>', body, re.S)
        if not q or not c:
            raise SystemExit("card %s needs h2.q and p.catch" % cid)
        cards.append(dict(
            id=cid, topic=topic, body=body, q=strip(q.group(1)), catch=strip(c.group(1)),
            qa=[(a.strip(), b.strip()) for a, b in QA_RE.findall(body)],
        ))
    return cards


def vol_link(v, urls, current, cls):
    meta = "配点 %s" % v["weight"]
    inner = "<b>VOL.%s</b><span>%s</span><small>%s%s</small>" % (
        v["no"], v["short"], meta, " ／ 本号" if v is current else "")
    if cls == "vols":
        inner = "VOL.%s %s" % (v["no"], v["short"])
    on = ' class="on"' if v is current else ""
    url = urls.get(v["key"])
    if v is not current and url:
        return '<li%s><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (on, url, inner)
    return "<li%s><span>%s</span></li>" % (on, inner)


def build_vol(v, urls):
    text = (SRC / ("%s.html" % v["key"])).read_text(encoding="utf-8")
    art = section(text, "COVER")
    cards = parse_cards(section(text, "CARDS"))
    quiz = section(text, "QUIZ")
    memo = section(text, "MEMO")
    nq = quiz.count('class="qz"')
    total = len(cards)
    nfig = sum(len(re.findall(r'<span class="no">図', c["body"])) for c in cards)
    nn = lambda i: "%02d" % (i + 1)

    # 上部バー
    chips = "".join('<a href="#%s" aria-label="カード%s">%s</a>' % (c["id"], nn(i), nn(i)) for i, c in enumerate(cards))
    chips += '<a class="txt" href="#quiz">腕試し</a><a class="txt" href="#memo">暗記</a>'
    topbar = (
        '<nav class="topbar" aria-label="カード一覧"><a class="tb-home" href="#top"><b>VOL.%s</b>%s</a>'
        '<div class="tb-chips">%s</div></nav>' % (v["no"], v["short"], chips)
    )

    # 表紙
    vols = "".join(vol_link(x, urls, v, "vols") for x in VOLS)
    lines = '<li class="main"><span>配点 <em>%s</em>、%s</span></li>' % (v["weight"], v["lines"][0])
    lines += "".join("<li><span>%s</span></li>" % s for s in v["lines"][1:])
    lines += "<li><span>巻末 腕試し%d問＋切り取り暗記カード</span></li>" % nq
    cover = f"""<header class="cover" id="top">
  <div class="mast">
    <div class="issue"><b>VOL.{v['no']}</b><span>2026 AUTUMN</span><span>試験対策シリーズ</span></div>
    <div class="logo"><span class="en">MS-102</span><span class="ja">図解ムック</span></div>
    <div class="feature"><span class="kick">特集</span><h1>{v['feature']}</h1></div>
    <ul class="clines">{lines}</ul>
  </div>
  <div class="cover-art">{art}
    <div class="badge" aria-label="保存版"><b>保存版</b><small>図版 {nfig}点</small></div>
  </div>
  <div class="cover-foot">
    <ul class="vols" aria-label="シリーズ">{vols}</ul>
    <span>公式スキル測定 2026.04.28 版準拠 ／ 試験は 2026.11.30 廃止予定</span>
  </div>
</header>"""

    # 目次
    toc = "".join(
        '<li><a href="#%s"><span class="pg">%s</span><span class="tt"><b>%s</b><small>%s</small></span></a></li>'
        % (c["id"], nn(i), html.escape(c["q"]), html.escape(c["catch"])) for i, c in enumerate(cards)
    )
    toc += ('<li class="end"><a href="#quiz"><span class="pg">QZ</span><span class="tt"><b>巻末 腕試し%d問</b>'
            '<small>本試験と同じ形式で、解説つき</small></span></a></li>' % nq)
    toc += ('<li class="end"><a href="#memo"><span class="pg">MC</span><span class="tt"><b>切り取り暗記カード／奥付</b>'
            '<small>直前の見直し用に12枚</small></span></a></li>')
    sis = ""
    if urls.get("drill"):
        sis += ('<a class="hot" href="%s" target="_blank" rel="noopener"><b>MS-102 逆引きドリル</b>'
                '<span>全巻の「ここが出る！」を、間違えたものから繰り返す。</span></a>' % urls["drill"])
    sis += "".join(
        '<a href="%s" target="_blank" rel="noopener"><b>%s</b><span>%s</span></a>' % (urls[k], t, d)
        for k, t, d in SISTERS if urls.get(k)
    )
    contents = f"""<section class="sheet" id="contents" aria-labelledby="h-toc">
  <h2 class="toc-h" id="h-toc">CONTENTS<small>特集 {strip(v['feature'])} ／ {v['chapter']}・配点 {v['weight']}</small></h2>
  <ol class="toc">{toc}</ol>
  <div class="two">
    <div style="display:grid;gap:12px;align-content:start">
      <span class="sub-h">カードの読み方</span>
      <ol class="howto">
        <li><div><b>問いを読んで、答えを予想する</b><span>カードの最初の一行は試験の聞き方。大きな一文がその答えです。</span></div></li>
        <li><div><b>図で形をつかむ</b><span>図版番号の横の一文が、その図の結論です。</span></div></li>
        <li><div><b>押さえどころ3行と「ここが出る！」</b><span>付箋の設問は、答えを思い出してから「答え」を押します。</span></div></li>
      </ol>
    </div>
    <div style="display:grid;gap:12px;align-content:start">
      <span class="sub-h">シリーズの姉妹ページ</span>
      <div class="sister">{sis}</div>
    </div>
  </div>
</section>"""

    # カード
    out_cards = []
    for i, c in enumerate(cards):
        body = c["body"].replace('<h2 class="q">', '<h2 class="q" id="%s-q">' % c["id"], 1)
        prev = '<a href="#%s">← CARD %s</a>' % (cards[i - 1]["id"], nn(i - 1)) if i else ""
        nxt = ('<a class="next" href="#%s">次のカード →</a>' % cards[i + 1]["id"]) if i + 1 < total \
            else '<a class="next" href="#quiz">腕試しへ →</a>'
        out_cards.append(
            '<article class="card" id="%s" aria-labelledby="%s-q">\n'
            '<div class="card-h"><span class="no">CARD <b>%s</b> / %d</span><span class="topic">%s</span></div>\n'
            '%s\n<nav class="card-nav" aria-label="カードの移動">%s<a href="#contents">目次</a>%s</nav>\n</article>'
            % (c["id"], c["id"], nn(i), total, c["topic"], body.strip(), prev, nxt)
        )

    quiz_html = f"""<section class="sheet" id="quiz" aria-labelledby="h-quiz">
  <div class="quiz-h"><div class="kicker"><span class="part">巻末</span><span>腕試し{nq}問</span></div><span class="score" aria-live="polite">正解 <b id="score">0</b> / {nq}</span></div>
  <h2 class="sheet-h" id="h-quiz">選んだ瞬間に、答え合わせ。</h2>
  {quiz}
</section>"""

    series = "".join(vol_link(x, urls, v, "series") for x in VOLS)
    drill_line = ""
    if urls.get("drill"):
        drill_line = ('<div class="sister"><a class="hot" href="%s" target="_blank" rel="noopener"><b>この先は逆引きドリルで</b>'
                      '<span>全巻の「ここが出る！」を、間違えたものから繰り返し出題します。</span></a></div>' % urls["drill"])
    memo_html = f"""<section class="sheet" id="memo" aria-labelledby="h-memo">
  <div class="kicker"><span class="part">付録</span><span>切り取り暗記カード</span></div>
  <h2 class="sheet-h" id="h-memo">直前の10分は、この12枚だけ。</h2>
  <p class="cut">キリトリ</p>
  <div class="cards">{memo}</div>
  <p class="cut">キリトリ</p>
  {drill_line}
  <span class="sub-h">シリーズ構成</span>
  <ul class="series">{series}</ul>
  <div class="okuduke">
    <span class="ttl">MS-102 図解ムック VOL.{v['no']} 特集 {strip(v['feature'])}</span>
    <dl>
      <dt>発行</dt><dd>2026年10月</dd>
      <dt>準拠</dt><dd>Microsoft 公式スキル測定（2026年4月28日版）</dd>
      <dt>底本</dt><dd>MS-102 総合テキスト {v['chapter']}</dd>
      <dt>ご注意</dt><dd>製品名・画面・ライセンス要件は変わることがあります。受験前に Microsoft Learn の学習ガイドで最新の情報を確認してください。MS-102 は 2026年11月30日に廃止予定です。</dd>
    </dl>
  </div>
  <div class="sister">
    <a href="#top"><b>表紙へ戻る</b><span>目次から別のカードへ</span></a>
    <a href="{LEARN}" target="_blank" rel="noopener"><b>試験ページ（Microsoft Learn）</b><span>試験概要と廃止予定日の確認</span></a>
  </div>
</section>"""

    css = (SRC / "mook.css").read_text(encoding="utf-8")
    js = (SRC / "mook.js").read_text(encoding="utf-8")
    page = "\n".join([
        "<title>%s</title>" % v["title"], FONTS,
        "<style>\n%s\n%s</style>" % (css, color_css(v["colors"])),
        topbar, '<main class="book">', cover, contents, "\n".join(out_cards), quiz_html, memo_html, "</main>",
        "<script>\n%s</script>\n" % js,
    ])
    (ROOT / v["out"]).write_text(page, encoding="utf-8")
    qa = [dict(vol=v["no"], card=nn(i), cid=c["id"], topic=c["topic"], title=c["q"],
               q=strip(a), a=strip(b)) for i, c in enumerate(cards) for a, b in c["qa"]]
    print("%s: %d cards, %d figures, %d quiz, %d qa" % (v["out"], total, nfig, nq, len(qa)))
    return qa


def build_drill(all_qa, urls):
    tpl_path = SRC / "drill.html"
    if not tpl_path.exists():
        return
    vols = [dict(no=v["no"], short=v["short"], url=urls.get(v["key"], ""), colors=v["colors"]) for v in VOLS]
    data = json.dumps(dict(items=all_qa, vols=vols), ensure_ascii=False).replace("</", "<\\/")
    page = tpl_path.read_text(encoding="utf-8").replace("/*@@DATA@@*/null", data).replace("@@FONTS@@", FONTS)
    page = page.replace("@@SISTERS@@", "".join(
        '<a href="%s" target="_blank" rel="noopener"><b>%s</b><span>%s</span></a>' % (urls[k], t, d)
        for k, t, d in SISTERS if urls.get(k)))
    (ROOT / "ms102-drill.html").write_text(page, encoding="utf-8")
    print("ms102-drill.html: %d items" % len(all_qa))


def main():
    urls = json.loads((SRC / "urls.json").read_text(encoding="utf-8"))
    all_qa = []
    for v in VOLS:
        if (SRC / ("%s.html" % v["key"])).exists():
            all_qa += build_vol(v, urls)
    build_drill(all_qa, urls)


if __name__ == "__main__":
    main()
