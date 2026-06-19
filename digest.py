"""
Digest Matin DAJM
Design éditorial · 1 colonne · TLDR + expand · Expert insights
"""

import smtplib, json, os, re, subprocess, urllib.request
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import anthropic

# ─── Config ──────────────────────────────────────────────────────────────────

BASE_DIR  = Path(__file__).parent
FEED_JSON = BASE_DIR / "feed.json"
FEED_HTML = BASE_DIR / "feed.html"

def load_env():
    env = BASE_DIR / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

GMAIL_USER    = "arnaud.dajm@gmail.com"
GMAIL_PASS    = os.environ.get("GMAIL_APP_PASSWORD", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FEED_WEB_URL  = os.environ.get("FEED_WEB_URL", "https://agencedajm.github.io/digest-matin/")
TO_EMAIL      = "arnaud.dajm@gmail.com"

now       = datetime.now()
TODAY_ISO = now.strftime("%Y-%m-%d")
TODAY_FR  = now.strftime("%A %d %B %Y").capitalize()
TODAY_SHORT = now.strftime("%d/%m/%Y")

# ─── SVG illustrations ────────────────────────────────────────────────────────

SVG = {
"strategy": """<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg">
<rect width="680" height="260" fill="#0A1628"/>
<circle cx="90" cy="130" r="7" fill="white" opacity=".9"/>
<circle cx="230" cy="75" r="5" fill="white" opacity=".6"/>
<circle cx="230" cy="185" r="5" fill="white" opacity=".6"/>
<circle cx="380" cy="50" r="3.5" fill="white" opacity=".4"/>
<circle cx="380" cy="130" r="7" fill="white" opacity=".85"/>
<circle cx="380" cy="210" r="3.5" fill="white" opacity=".4"/>
<circle cx="530" cy="95" r="5" fill="white" opacity=".6"/>
<circle cx="530" cy="165" r="5" fill="white" opacity=".6"/>
<circle cx="620" cy="130" r="8" fill="white"/>
<line x1="90" y1="130" x2="230" y2="75" stroke="white" stroke-width="1.2" opacity=".18"/>
<line x1="90" y1="130" x2="230" y2="185" stroke="white" stroke-width="1.2" opacity=".18"/>
<line x1="230" y1="75" x2="380" y2="130" stroke="white" stroke-width="1.2" opacity=".2"/>
<line x1="230" y1="185" x2="380" y2="130" stroke="white" stroke-width="1.2" opacity=".2"/>
<line x1="380" y1="130" x2="530" y2="95" stroke="white" stroke-width="1.2" opacity=".2"/>
<line x1="380" y1="130" x2="530" y2="165" stroke="white" stroke-width="1.2" opacity=".2"/>
<line x1="530" y1="95" x2="620" y2="130" stroke="white" stroke-width="1.5" opacity=".35"/>
<line x1="530" y1="165" x2="620" y2="130" stroke="white" stroke-width="1.5" opacity=".35"/>
</svg>""",

"copywriting": """<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg">
<rect width="680" height="260" fill="#FFF6F5"/>
<text x="-20" y="250" font-size="310" font-weight="900" fill="#B91C1C" opacity=".055" font-family="Georgia,serif">AW</text>
<rect x="52" y="105" width="200" height="8" rx="4" fill="#B91C1C"/>
<rect x="52" y="129" width="140" height="8" rx="4" fill="#B91C1C" opacity=".35"/>
<rect x="52" y="153" width="170" height="8" rx="4" fill="#B91C1C" opacity=".18"/>
<rect x="52" y="177" width="100" height="8" rx="4" fill="#B91C1C" opacity=".1"/>
<rect x="468" y="85" width="3" height="110" fill="#B91C1C" opacity=".15"/>
<rect x="498" y="110" width="3" height="65" fill="#B91C1C" opacity=".1"/>
</svg>""",

"visuals": """<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg">
<rect width="680" height="260" fill="#F6F5FF"/>
<rect x="0" y="0" width="226" height="260" fill="#1E1B4B" opacity=".07"/>
<rect x="226" y="0" width="228" height="130" fill="#1E1B4B" opacity=".12"/>
<rect x="454" y="130" width="226" height="130" fill="#1E1B4B" opacity=".05"/>
<circle cx="340" cy="130" r="95" fill="none" stroke="#1E1B4B" stroke-width="1.5" opacity=".12"/>
<circle cx="340" cy="130" r="46" fill="#1E1B4B" opacity=".07"/>
<circle cx="340" cy="130" r="13" fill="#1E1B4B" opacity=".2"/>
<line x1="0" y1="130" x2="680" y2="130" stroke="#1E1B4B" stroke-width="1" opacity=".08"/>
<line x1="340" y1="0" x2="340" y2="260" stroke="#1E1B4B" stroke-width="1" opacity=".08"/>
<rect x="60" y="60" width="70" height="70" fill="none" stroke="#1E1B4B" stroke-width="1.5" opacity=".12" transform="rotate(18 95 95)"/>
<rect x="554" y="148" width="52" height="52" fill="#1E1B4B" opacity=".08" transform="rotate(-12 580 174)"/>
</svg>""",
}

CHEVRON = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 5L7 9L11 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# ─── Agents experts ───────────────────────────────────────────────────────────

RULES = """
REGLE ABSOLUE : Aucune information deja repandue dans les newsletters marketing generalistes, les fils LinkedIn viraux, les rapports Hootsuite / HubSpot / Canva. Ces banalites n'ont aucune valeur.

INTERDIT (exemples) :
- "L'IA transforme le marketing" - evidence
- "L'authenticite est importante" - tout le monde le sait
- "Le SEO evolue" - trop generique

ON VEUT (niveau d'exigence) :
- Une etude primaire des 90 derniers jours avec chiffres precis et contre-intuitifs
- Une decision strategique de marque peu mediatisee avec resultats mesurables
- Un signal faible dans un marche de niche qui prefigure une rupture dans 18 mois
- Une tactique que moins de 3% des professionnels utilisent, avec preuve

FORMAT JSON STRICT, tableau de 4 objets, rien d'autre :
[
  {
    "title": "Titre factuel percutant (max 10 mots, pas de question)",
    "tldr": "1 phrase ultra-courte avec le fait cle et un chiffre si possible (max 18 mots)",
    "detail": "Explication experte en 3 phrases avec nom de marque ou etude precise et resultats.",
    "source_name": "Nom exact du media ou de l'institution",
    "source_url": "URL directe vers l'article ou l'etude (reelle)"
  }
]
REPONDS UNIQUEMENT AVEC LE JSON.
"""

AGENTS = [
    {
        "id": "strategy",
        "label": "Strategie",
        "cat_bg": "#0A1628",
        "cat_fg": "#FFFFFF",
        "prompt": f"Tu es directeur strategie dans un cabinet conseil premium — tu publies dans Harvard Business Review et Les Echos, tu refuses les evidences. Recherche en profondeur les 4 insights les plus pointus et inattendus en strategie de communication de marque publies dans les 90 derniers jours.\n\n{RULES}",
    },
    {
        "id": "copywriting",
        "label": "Copywriting",
        "cat_bg": "#B91C1C",
        "cat_fg": "#FFFFFF",
        "prompt": f"Tu es directeur de creation conception-redaction, tu as travaille chez Ogilvy et BETC, tu juges les Cannes Lions. Tu sais exactement ce qui fait performer un texte publicitaire au niveau metrologique. Recherche en profondeur les 4 insights les plus pointus en copywriting et mecanique de campagne publies dans les 90 derniers jours.\n\n{RULES}",
    },
    {
        "id": "visuals",
        "label": "Direction artistique",
        "cat_bg": "#1E1B4B",
        "cat_fg": "#FFFFFF",
        "prompt": f"Tu es directeur artistique senior, tu distingues une vraie tendance d'un effet de mode Instagram, tu lis les travaux en psychologie de la perception visuelle. Recherche en profondeur les 4 directions artistiques les plus significatives en communication visuelle publiees dans les 90 derniers jours.\n\n{RULES}",
    },
]


def research_agent(agent: dict) -> list:
    print(f"  {agent['label']}...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": agent["prompt"]}],
    )
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    m = re.search(r'\[.*?\]', text, re.DOTALL)
    if m:
        try:
            return [c for c in json.loads(m.group()) if isinstance(c, dict)][:4]
        except Exception:
            pass
    return [{"title": "Veille", "tldr": text[:100], "detail": text[:300], "source_name": "", "source_url": ""}]


def fetch_image(url: str) -> str:
    if not url:
        return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read(30000).decode("utf-8", errors="ignore")
        for pat in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                img = m.group(1).strip()
                if img.startswith("//"): img = "https:" + img
                if img.startswith("http"): return img
    except Exception:
        pass
    return ""


# ─── Feed ─────────────────────────────────────────────────────────────────────

def load_feed() -> list:
    return json.loads(FEED_JSON.read_text(encoding="utf-8")) if FEED_JSON.exists() else []

def save_feed(feed: list):
    FEED_JSON.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")

def add_entry(feed: list, cards: list) -> list:
    return [{"date_iso": TODAY_ISO, "date_fr": TODAY_FR, "cards": cards}] + [e for e in feed if e.get("date_iso") != TODAY_ISO]


# ─── HTML ─────────────────────────────────────────────────────────────────────

def render_card(card: dict, agent: dict, is_new: bool) -> str:
    img = card.get("og_image", "")
    url = card.get("source_url", "")

    visual = (
        f'<div class="c-media"><img src="{img}" alt="" loading="lazy"></div>'
        if img else
        '<div class="c-no-img"></div>'
    )

    new_badge = '<span class="badge-new">NOUVEAU</span>' if is_new else ""
    src_btn = f'<a href="{url}" target="_blank" rel="noopener" class="btn-source">LIRE LA SOURCE</a>' if url else ""

    return f"""
<article class="card" data-cat="{agent['id']}">
  {visual}
  <div class="c-body">
    <div class="c-meta">
      <span class="c-cat">{agent['label'].upper()}</span>
      {new_badge}
    </div>
    <h2 class="c-title">{card.get('title','')}</h2>
    <p class="c-tldr">{card.get('tldr','')}</p>
    <button class="btn-expand" onclick="expand(this)">
      APPROFONDIR {CHEVRON}
    </button>
    <div class="c-detail" hidden>
      <p class="c-detail-text">{card.get('detail','')}</p>
      {src_btn}
    </div>
  </div>
</article>"""


def build_feed_html(feed: list, agents_map: dict) -> str:
    all_sections = []
    for i, entry in enumerate(feed):
        is_new = (i == 0)
        label = "Aujourd'hui" if is_new else entry["date_fr"]
        day_cards = "".join(
            render_card(c, agents_map.get(c.get("agent_id","strategy"), agents_map["strategy"]), is_new)
            for c in entry.get("cards", [])
        )
        cls = "day-today" if is_new else ""
        all_sections.append(f"""
<section class="day" id="{entry['date_iso']}">
  <div class="day-inner">
    <div class="day-header">
      <span class="day-label {cls}">{label}</span>
    </div>
    <div class="cards-grid">{day_cards}</div>
  </div>
</section>""")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover">
<meta name="theme-color" content="#FFFFFF">
<title>Digest Matin</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Work+Sans:wght@400;600&family=Space+Mono&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;border-radius:0!important;box-shadow:none!important}}
html{{scroll-behavior:smooth}}
body{{
  font-family:'Work Sans',sans-serif;
  background:#fff;color:#000;
  -webkit-font-smoothing:antialiased;
  padding-bottom:max(env(safe-area-inset-bottom),64px)
}}
a{{color:#0000FF}}

/* ── Header ── */
.hdr{{
  position:sticky;top:0;z-index:100;
  background:#fff;
  border-bottom:3px solid #000
}}
.hdr-inner{{
  max-width:1280px;margin:0 auto;
  height:64px;padding:0 24px;
  display:flex;align-items:center;justify-content:space-between;gap:16px
}}
.hdr-name{{
  font-family:'Archivo Black',sans-serif;
  font-size:24px;letter-spacing:-.5px
}}
.hdr-right{{display:flex;align-items:center;gap:16px}}
.hdr-date{{font-size:12px;color:#666;line-height:1.4;text-align:right;font-family:'Space Mono',monospace}}

/* ── Bouton Actualiser (toujours visible) ── */
.btn-refresh{{
  font-family:'Work Sans',sans-serif;
  font-size:12px;font-weight:600;
  letter-spacing:2px;text-transform:uppercase;
  padding:10px 24px;cursor:pointer;
  background:#000;color:#fff;
  border:3px solid #000;
  transition:background .1s,color .1s;
  white-space:nowrap
}}
.btn-refresh:hover{{background:#fff;color:#000}}
.btn-refresh:disabled{{background:#fff;color:#000;border-color:#CCC;cursor:default}}

/* ── Filtres ── */
.filters{{
  max-width:1280px;margin:0 auto;
  padding:16px 24px 0;
  display:flex;gap:0;
  border-bottom:3px solid #000;
  overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none
}}
.filters::-webkit-scrollbar{{display:none}}
.f{{
  flex-shrink:0;
  font-family:'Work Sans',sans-serif;
  font-size:10px;font-weight:600;
  letter-spacing:1px;text-transform:uppercase;
  padding:8px 20px;cursor:pointer;
  background:#fff;color:#000;
  border:none;border-right:3px solid #000;
  transition:background .1s,color .1s;
  white-space:nowrap
}}
.f:first-child{{border-left:0}}
.f:last-child{{border-right:0}}
.f:hover,.f.on{{background:#000;color:#fff}}

/* ── Jour ── */
.day-inner{{max-width:1280px;margin:0 auto;padding:0 24px}}
.day-header{{
  padding:32px 0 16px;
  border-top:5px solid #000
}}
.day:first-child .day-header{{border-top:none;padding-top:24px}}
.day-label{{
  font-family:'Archivo Black',sans-serif;
  font-size:32px;line-height:1.0;
  letter-spacing:-.5px
}}
.day-today{{font-size:48px}}

/* ── Grille 5 colonnes — 4 lignes max, flow en colonnes ── */
.cards-grid{{display:block}}

@media(min-width:600px){{
  .cards-grid{{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    grid-template-rows:repeat(4,auto);
    grid-auto-flow:column;
    grid-auto-columns:1fr;
    border-top:3px solid #000;
    border-left:3px solid #000
  }}
}}
@media(min-width:900px){{.cards-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(min-width:1100px){{.cards-grid{{grid-template-columns:repeat(4,1fr)}}}}
@media(min-width:1280px){{.cards-grid{{grid-template-columns:repeat(5,1fr)}}}}

/* ── Card ── */
.card{{
  background:#fff;
  overflow:hidden;
  margin-bottom:3px
}}
@media(min-width:600px){{
  .card{{
    margin-bottom:0;
    border-right:3px solid #000;
    border-bottom:3px solid #000
  }}
}}

.c-media{{width:100%;line-height:0}}
.c-media img{{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;border-bottom:3px solid #000}}
.c-no-img{{height:8px;background:#000}}

.c-body{{padding:16px}}
.c-meta{{display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.c-cat{{
  font-family:'Space Mono',monospace;
  font-size:10px;letter-spacing:1px;text-transform:uppercase;
  padding:3px 8px;
  background:#000;color:#fff
}}
.badge-new{{
  font-family:'Space Mono',monospace;
  font-size:10px;letter-spacing:1px;text-transform:uppercase;
  padding:3px 8px;
  border:2px solid #008000;color:#008000
}}

.c-title{{
  font-family:'Archivo Black',sans-serif;
  font-size:20px;line-height:1.1;
  color:#000;margin-bottom:10px
}}
.c-tldr{{
  font-size:16px;font-weight:400;
  line-height:1.6;color:#000;
  margin-bottom:14px
}}

/* ── Bouton Approfondir ── */
.btn-expand{{
  display:inline-flex;align-items:center;gap:8px;
  font-family:'Work Sans',sans-serif;
  font-size:11px;font-weight:600;
  letter-spacing:2px;text-transform:uppercase;
  color:#000;background:#fff;
  border:3px solid #000;padding:8px 16px;
  cursor:pointer;transition:background .1s,color .1s
}}
.btn-expand:hover,.btn-expand.open{{background:#000;color:#fff}}
.btn-expand svg{{transition:transform .2s ease}}
.btn-expand.open svg{{transform:rotate(180deg)}}

/* ── Detail panel ── */
.c-detail{{
  margin-top:16px;
  padding-top:16px;
  border-top:3px solid #000
}}
.c-detail-text{{
  font-size:15px;line-height:1.6;color:#000;
  margin-bottom:16px
}}

/* ── Bouton Lire la source ── */
.btn-source{{
  display:inline-block;
  font-family:'Work Sans',sans-serif;
  font-size:11px;font-weight:600;
  letter-spacing:2px;text-transform:uppercase;
  padding:10px 24px;
  background:#000;color:#fff;
  border:3px solid #000;
  text-decoration:none;
  transition:background .1s,color .1s
}}
.btn-source:hover{{background:#fff;color:#000}}

/* ── Desktop : titres plus grands ── */
@media(min-width:1280px){{
  .c-title{{font-size:22px}}
  .c-body{{padding:20px}}
}}

/* ── Overlay loading ── */
.overlay{{
  display:none;position:fixed;inset:0;z-index:200;
  background:rgba(255,255,255,.92);
  align-items:center;justify-content:center;
  flex-direction:column;gap:16px
}}
.overlay.show{{display:flex}}
.overlay-text{{
  font-family:'Archivo Black',sans-serif;
  font-size:32px;letter-spacing:-.5px
}}
.overlay-sub{{
  font-family:'Space Mono',monospace;
  font-size:12px;color:#666
}}

/* ── Footer ── */
.site-footer{{
  max-width:1280px;margin:0 auto;
  padding:32px 24px 48px;
  border-top:5px solid #000;
  font-family:'Space Mono',monospace;
  font-size:11px;color:#666;letter-spacing:.5px
}}
</style>
</head>
<body>

<header class="hdr">
  <div class="hdr-inner">
    <span class="hdr-name">DIGEST MATIN</span>
    <div class="hdr-right">
      <button id="btn-refresh" class="btn-refresh" onclick="doRefresh()">Actualiser</button>
      <div class="hdr-date">{TODAY_SHORT}<br>{len(feed)} EDITION{"S" if len(feed)>1 else ""}</div>
    </div>
  </div>
</header>

<div class="filters">
  <button class="f on" onclick="fil('all',this)">Tout</button>
  <button class="f" onclick="fil('strategy',this)">Strategie</button>
  <button class="f" onclick="fil('copywriting',this)">Copywriting</button>
  <button class="f" onclick="fil('visuals',this)">Direction artistique</button>
</div>

{"".join(all_sections)}

<footer class="site-footer">DAJM &middot; DIGEST MATIN &middot; {TODAY_FR.upper()}</footer>

<div class="overlay" id="overlay">
  <div class="overlay-text">RECHERCHE EN COURS</div>
  <div class="overlay-sub">Les agents travaillent... (~2 min)</div>
</div>

<script>
var _poll;
async function doRefresh(){{
  var btn=document.getElementById('btn-refresh');
  btn.disabled=true;
  btn.textContent='RECHERCHE...';
  document.getElementById('overlay').classList.add('show');
  try{{
    var r=await fetch('http://localhost:8765/refresh');
    if(!r.ok)throw new Error();
    _poll=setInterval(async function(){{
      try{{
        var s=await fetch('http://localhost:8765/status');
        var d=await s.json();
        if(!d.running){{clearInterval(_poll);location.reload();}}
      }}catch(e){{}}
    }},5000);
  }}catch(e){{
    document.getElementById('overlay').classList.remove('show');
    btn.disabled=false;
    btn.textContent='SERVEUR NON ACTIF';
    setTimeout(function(){{btn.textContent='ACTUALISER';btn.disabled=false;}},3000);
  }}
}}

function expand(btn){{
  var panel=btn.nextElementSibling;
  var open=!panel.hidden;
  panel.hidden=open;
  btn.classList.toggle('open',!open);
  btn.childNodes[0].textContent=open?'APPROFONDIR ':'REDUIRE ';
}}
function fil(cat,btn){{
  document.querySelectorAll('.f').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  document.querySelectorAll('.card').forEach(c=>{{
    c.style.display=(cat==='all'||c.dataset.cat===cat)?'':'none';
  }});
}}
</script>
</body>
</html>"""


# ─── Email ────────────────────────────────────────────────────────────────────

def build_email(cards: list, agents_map: dict) -> str:
    items = ""
    for c in cards[:9]:
        ag = agents_map.get(c.get("agent_id","strategy"), agents_map["strategy"])
        img = c.get("og_image","")
        url = c.get("source_url","")
        img_h = f'<img src="{img}" style="width:100%;height:180px;object-fit:cover;display:block;" alt="">' if img else ""
        btn_h = f'<a href="{url}" style="display:inline-block;background:#111;color:#fff;font-size:14px;font-weight:600;padding:12px 22px;border-radius:8px;text-decoration:none;margin-top:14px;">Lire la source</a>' if url else ""
        items += f"""
<div style="background:#fff;border-radius:12px;overflow:hidden;margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,.07);">
  {img_h}
  <div style="padding:18px 20px 20px;">
    <span style="display:inline-block;font-size:10px;font-weight:700;letter-spacing:.7px;text-transform:uppercase;padding:3px 9px;border-radius:20px;background:{ag['cat_bg']};color:{ag['cat_fg']};margin-bottom:12px;">{ag['label']}</span>
    <div style="font-size:24px;font-weight:800;line-height:1.15;letter-spacing:-.5px;color:#111;margin-bottom:10px;">{c.get('title','')}</div>
    <div style="font-size:17px;font-weight:500;line-height:1.45;color:#2d2d2d;margin-bottom:10px;">{c.get('tldr','')}</div>
    <div style="font-size:15px;color:#737373;line-height:1.6;">{c.get('detail','')}</div>
    {btn_h}
  </div>
</div>"""

    web = f'<div style="text-align:center;margin:28px 0 12px;"><a href="{FEED_WEB_URL}" style="display:inline-block;background:#111;color:#fff;font-size:15px;font-weight:700;padding:14px 32px;border-radius:10px;text-decoration:none;">Voir le digest complet</a></div>' if FEED_WEB_URL else ""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F5F4F0;margin:0;padding:16px;">
<div style="max-width:560px;margin:0 auto;">
  <div style="text-align:center;padding:32px 0 24px;">
    <div style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#9CA3AF;margin-bottom:8px;">Veille quotidienne</div>
    <div style="font-size:28px;font-weight:800;letter-spacing:-.5px;color:#111;">Digest Matin</div>
    <div style="font-size:13px;color:#9CA3AF;margin-top:5px;">{TODAY_FR}</div>
  </div>
  {items}
  {web}
  <div style="text-align:center;padding:20px 0 8px;font-size:11px;color:#B0B0B0;">DAJM &middot; Digest automatique</div>
</div></body></html>"""


def send_email(cards, agents_map):
    html = build_email(cards, agents_map)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Digest Matin — {TODAY_SHORT}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
    print("  Email envoye")


def push_github():
    try:
        idx = BASE_DIR / "index.html"
        idx.write_text(FEED_HTML.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run(["git","-C",str(BASE_DIR),"add","index.html","feed.json"], check=True)
        subprocess.run(["git","-C",str(BASE_DIR),"commit","-m",f"Digest {TODAY_ISO}"], check=True)
        subprocess.run(["git","-C",str(BASE_DIR),"push"], check=True)
        print(f"  Publie : {FEED_WEB_URL}")
    except subprocess.CalledProcessError as e:
        print(f"  Push echoue : {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\nDigest Matin — {TODAY_FR}")
    print("─" * 44)
    agents_map = {a["id"]: a for a in AGENTS}
    all_cards  = []

    for agent in AGENTS:
        cards = research_agent(agent)
        for c in cards:
            c["agent_id"] = agent["id"]
            c["og_image"] = fetch_image(c.get("source_url",""))
            print(f"  · {c.get('title','')[:55]}")
        all_cards.extend(cards)

    feed = add_entry(load_feed(), all_cards)
    save_feed(feed)

    FEED_HTML.write_text(build_feed_html(feed, agents_map), encoding="utf-8")
    print(f"  {len(feed)} edition(s) · {len(all_cards)} cartes")

    if GMAIL_PASS:
        send_email(all_cards, agents_map)

    push_github()
    print("─" * 44)
    print(f"Termine. {FEED_WEB_URL}\n")


if __name__ == "__main__":
    main()
