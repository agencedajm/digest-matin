"""
Digest Matin DAJM
Design éditorial · 1 colonne · TLDR + expand · Expert insights
"""

import smtplib, json, os, re, subprocess, urllib.request, html as _html
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
FEED_WEB_URL  = os.environ.get("FEED_WEB_URL", "https://mellifluous-crostata-69725a.netlify.app/")
TO_EMAILS     = [
    "arnaud.dajm@gmail.com",
    "aurelie.delettre@dajm.fr",
    "pierre.deman@dajm.fr",
    "guillaume.juliot@dajm.fr",
]

_JOURS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
_MOIS  = ["","Janvier","Février","Mars","Avril","Mai","Juin",
           "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

def date_fr(dt):
    return f"{_JOURS[dt.weekday()]} {dt.day} {_MOIS[dt.month]} {dt.year}"

now         = datetime.now()
TODAY_ISO   = now.strftime("%Y-%m-%d")
TODAY_FR    = date_fr(now)
TODAY_SHORT = now.strftime("%d/%m/%Y")

# ─── SVG illustrations ────────────────────────────────────────────────────────

SVG = {
# STRATÉGIE — fond noir — réseau de nœuds hiérarchique
"strategy": """<svg viewBox="0 0 680 260" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
<rect width="680" height="260" fill="#000000"/>
<circle cx="90" cy="130" r="8" fill="white"/>
<circle cx="250" cy="68" r="5" fill="white" opacity=".7"/>
<circle cx="250" cy="130" r="4" fill="white" opacity=".45"/>
<circle cx="250" cy="192" r="5" fill="white" opacity=".7"/>
<circle cx="400" cy="44" r="3.5" fill="white" opacity=".4"/>
<circle cx="400" cy="100" r="6" fill="white" opacity=".85"/>
<circle cx="400" cy="160" r="6" fill="white" opacity=".85"/>
<circle cx="400" cy="216" r="3.5" fill="white" opacity=".4"/>
<circle cx="545" cy="82" r="5" fill="white" opacity=".6"/>
<circle cx="545" cy="130" r="9" fill="white"/>
<circle cx="545" cy="178" r="5" fill="white" opacity=".6"/>
<circle cx="628" cy="130" r="6" fill="white" opacity=".8"/>
<line x1="90" y1="130" x2="250" y2="68" stroke="white" stroke-width="1" opacity=".22"/>
<line x1="90" y1="130" x2="250" y2="130" stroke="white" stroke-width="1" opacity=".12"/>
<line x1="90" y1="130" x2="250" y2="192" stroke="white" stroke-width="1" opacity=".22"/>
<line x1="250" y1="68" x2="400" y2="100" stroke="white" stroke-width="1" opacity=".25"/>
<line x1="250" y1="130" x2="400" y2="100" stroke="white" stroke-width="1" opacity=".14"/>
<line x1="250" y1="130" x2="400" y2="160" stroke="white" stroke-width="1" opacity=".14"/>
<line x1="250" y1="192" x2="400" y2="160" stroke="white" stroke-width="1" opacity=".25"/>
<line x1="400" y1="100" x2="545" y2="82" stroke="white" stroke-width="1.2" opacity=".3"/>
<line x1="400" y1="100" x2="545" y2="130" stroke="white" stroke-width="1.2" opacity=".38"/>
<line x1="400" y1="160" x2="545" y2="130" stroke="white" stroke-width="1.2" opacity=".38"/>
<line x1="400" y1="160" x2="545" y2="178" stroke="white" stroke-width="1.2" opacity=".3"/>
<line x1="545" y1="130" x2="628" y2="130" stroke="white" stroke-width="1.5" opacity=".5"/>
</svg>""",

# COPYWRITING — fond rouge — ondes concentriques (message qui se propage)
"copywriting": """<svg viewBox="0 0 680 260" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
<rect width="680" height="260" fill="#FF0000"/>
<circle cx="340" cy="130" r="16" fill="white"/>
<circle cx="340" cy="130" r="52" fill="none" stroke="white" stroke-width="1.5" opacity=".75"/>
<circle cx="340" cy="130" r="96" fill="none" stroke="white" stroke-width="1.2" opacity=".52"/>
<circle cx="340" cy="130" r="148" fill="none" stroke="white" stroke-width="1" opacity=".32"/>
<circle cx="340" cy="130" r="210" fill="none" stroke="white" stroke-width=".8" opacity=".18"/>
<circle cx="392" cy="130" r="5" fill="white" opacity=".9"/>
<circle cx="366" cy="85" r="5" fill="white" opacity=".9"/>
<circle cx="314" cy="85" r="5" fill="white" opacity=".9"/>
<circle cx="288" cy="130" r="5" fill="white" opacity=".9"/>
<circle cx="314" cy="175" r="5" fill="white" opacity=".9"/>
<circle cx="366" cy="175" r="5" fill="white" opacity=".9"/>
<circle cx="436" cy="130" r="6" fill="white" opacity=".68"/>
<circle cx="396" cy="47" r="5" fill="white" opacity=".68"/>
<circle cx="244" cy="82" r="5" fill="white" opacity=".68"/>
<circle cx="244" cy="178" r="5" fill="white" opacity=".68"/>
<circle cx="396" cy="213" r="5" fill="white" opacity=".68"/>
<circle cx="488" cy="130" r="5" fill="white" opacity=".45"/>
<circle cx="448" cy="20" r="4" fill="white" opacity=".4"/>
<circle cx="192" cy="130" r="5" fill="white" opacity=".45"/>
<circle cx="232" cy="20" r="4" fill="white" opacity=".4"/>
<circle cx="232" cy="240" r="4" fill="white" opacity=".4"/>
<circle cx="448" cy="240" r="4" fill="white" opacity=".4"/>
<line x1="340" y1="130" x2="392" y2="130" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="340" y1="130" x2="366" y2="85" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="340" y1="130" x2="314" y2="85" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="340" y1="130" x2="288" y2="130" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="340" y1="130" x2="314" y2="175" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="340" y1="130" x2="366" y2="175" stroke="white" stroke-width="1" opacity=".18"/>
</svg>""",

# DIRECTION ARTISTIQUE — fond bleu — cadre composition règle des tiers
"visuals": """<svg viewBox="0 0 680 260" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
<rect width="680" height="260" fill="#0000FF"/>
<rect x="32" y="20" width="616" height="220" fill="none" stroke="white" stroke-width="1.5" opacity=".35"/>
<line x1="237" y1="20" x2="237" y2="240" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="443" y1="20" x2="443" y2="240" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="32" y1="93" x2="648" y2="93" stroke="white" stroke-width="1" opacity=".18"/>
<line x1="32" y1="167" x2="648" y2="167" stroke="white" stroke-width="1" opacity=".18"/>
<circle cx="237" cy="93" r="8" fill="white" opacity=".95"/>
<circle cx="443" cy="93" r="5" fill="white" opacity=".6"/>
<circle cx="237" cy="167" r="5" fill="white" opacity=".6"/>
<circle cx="443" cy="167" r="8" fill="white" opacity=".95"/>
<line x1="32" y1="20" x2="648" y2="240" stroke="white" stroke-width="1" opacity=".1"/>
<line x1="226" y1="82" x2="248" y2="82" stroke="white" stroke-width="2" opacity=".7"/>
<line x1="237" y1="71" x2="237" y2="105" stroke="white" stroke-width="2" opacity=".7"/>
<polyline points="32,44 32,20 56,20" stroke="white" stroke-width="2.5" fill="none" opacity=".65"/>
<polyline points="624,20 648,20 648,44" stroke="white" stroke-width="2.5" fill="none" opacity=".65"/>
<polyline points="32,216 32,240 56,240" stroke="white" stroke-width="2.5" fill="none" opacity=".65"/>
<polyline points="624,240 648,240 648,216" stroke="white" stroke-width="2.5" fill="none" opacity=".65"/>
</svg>""",
}

ARROW = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# ─── Agents experts ───────────────────────────────────────────────────────────

RULES = """Reponds UNIQUEMENT en francais. Pas de generalites connues. Uniquement des insights non-evidents : etudes recentes avec chiffres, decisions de marques peu mediatisees, signaux faibles.
Aucune balise HTML. Aucun markdown. Aucun caractere d'echappement. Du texte brut uniquement, des phrases completes et naturelles.
JSON strict, 3 objets, rien d'autre :
[{"title":"max 8 mots, phrase nominale","tldr":"1 phrase affirmative complete + 1 chiffre cle (max 15 mots)","detail":"2 phrases concretes et lisibles avec la source nommee a la fin","source_name":"nom du media ou de l'institution","source_url":"URL reelle et accessible"}]"""

AGENTS = [
    {
        "id": "strategy",
        "label": "Strategie",
        "cat_bg": "#000000",
        "cat_fg": "#FFFFFF",
        "prompt": f"Expert strategie de communication. Recherche web : 3 insights pointus et inattendus en strategie de marque (90 derniers jours).\n{RULES}",
    },
    {
        "id": "copywriting",
        "label": "Copywriting",
        "cat_bg": "#FF0000",
        "cat_fg": "#FFFFFF",
        "prompt": f"Expert copywriting et publicite. Recherche web : 3 insights pointus sur les campagnes et mecaniques redactionnelles (90 derniers jours).\n{RULES}",
    },
    {
        "id": "visuals",
        "label": "Direction artistique",
        "cat_bg": "#0000FF",
        "cat_fg": "#FFFFFF",
        "prompt": f"Expert direction artistique. Recherche web : 3 tendances visuelles significatives et non-evidentes en communication (90 derniers jours).\n{RULES}",
    },
]


def clean_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', t)
    t = re.sub(r'`([^`]+)`', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
         .replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def research_agent(agent: dict, avoid_titles: list = None) -> list:
    print(f"  {agent['label']}...")
    prompt = agent["prompt"]
    if avoid_titles:
        avoid_block = "Sujets deja traites recemment a eviter absolument : " + " | ".join(avoid_titles)
        prompt = prompt + "\n" + avoid_block
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    m = re.search(r'\[.*?\]', text, re.DOTALL)
    if m:
        try:
            cards = [c for c in json.loads(m.group()) if isinstance(c, dict)][:3]
            for c in cards:
                for key in ("title", "tldr", "detail", "source_name"):
                    c[key] = clean_text(c.get(key, ""))
            return cards
        except Exception:
            pass
    return [{"title": "Veille", "tldr": clean_text(text[:120]), "detail": clean_text(text[:300]), "source_name": "", "source_url": ""}]


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
    img    = card.get("og_image", "")
    url    = card.get("source_url", "")
    detail = _html.escape(clean_text(card.get("detail", "")))
    title  = _html.escape(clean_text(card.get("title", "")))

    color = agent["cat_bg"]
    bar   = f'<div class="c-bar" style="background:{color}"></div>'

    if img:
        media = f'<div class="c-media"><img src="{img}" alt="" loading="lazy" onerror="this.closest(\'.c-media\').remove()"></div>'
    else:
        media = f'<div class="c-svg">{SVG.get(agent["id"],"")}</div>'

    new_badge = '<span class="badge-new">NOUVEAU</span>' if is_new else ""

    return f"""
<article class="card" data-cat="{agent['id']}" data-label="{agent['label'].upper()}" data-src="{url}" data-detail="{detail}" data-title="{title}">
  {bar}
  {media}
  <div class="c-body">
    <div class="c-meta">
      <span class="c-cat" style="background:{color}">{agent['label'].upper()}</span>
      {new_badge}
    </div>
    <h2 class="c-title">{clean_text(card.get('title',''))}</h2>
    <p class="c-tldr">{clean_text(card.get('tldr',''))}</p>
    <button class="btn-expand" onclick="openModal(this.closest('.card'))">
      APPROFONDIR {ARROW}
    </button>
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

/* ── Grille ── */
.cards-grid{{
  display:grid;
  grid-template-columns:1fr;
  gap:16px
}}
@media(min-width:600px){{
  .cards-grid{{
    grid-template-columns:repeat(2,1fr);
    gap:0;
    border-top:3px solid #000;
    border-left:3px solid #000
  }}
}}
@media(min-width:900px){{.cards-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(min-width:1100px){{.cards-grid{{grid-template-columns:repeat(4,1fr)}}}}

/* ── Card ── */
@keyframes fadeUp{{
  from{{opacity:0;transform:translateY(14px)}}
  to{{opacity:1;transform:translateY(0)}}
}}
.card{{
  background:#fff;
  overflow:hidden;
  border:3px solid #000;
  display:flex;flex-direction:column;
  transition:transform .18s ease,box-shadow .18s ease;
  animation:fadeUp .35s ease both;
  animation-delay:calc(var(--ci,0)*.05s)
}}
.card:hover{{
  transform:translate(-3px,-3px);
  box-shadow:3px 3px 0 0 #000
}}
@media(min-width:600px){{
  .card{{
    border:none;
    border-right:3px solid #000;
    border-bottom:3px solid #000
  }}
  .card:hover{{
    transform:translate(-2px,-2px);
    box-shadow:2px 2px 0 0 #000
  }}
}}

/* Barre catégorie — noire, 12px, toujours présente */
.c-bar{{height:12px;background:#000;width:100%;display:block}}

/* Zone visuelle — même hauteur pour photo et SVG */
.c-media,.c-svg{{width:100%;height:180px;overflow:hidden;border-bottom:3px solid #000;line-height:0}}
.c-media img{{width:100%;height:100%;object-fit:cover;display:block}}
.c-svg svg{{width:100%;height:100%;display:block}}

.c-body{{padding:16px;display:flex;flex-direction:column;flex:1}}
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
  margin-bottom:0;flex:1
}}

/* ── Bouton Approfondir — collé en bas ── */
.btn-expand{{
  display:inline-flex;align-items:center;gap:8px;
  font-family:'Work Sans',sans-serif;
  font-size:11px;font-weight:600;
  letter-spacing:2px;text-transform:uppercase;
  color:#000;background:#fff;
  border:3px solid #000;padding:8px 16px;
  cursor:pointer;transition:background .1s,color .1s;
  margin-top:16px;align-self:flex-start
}}
.btn-expand:hover{{background:#000;color:#fff}}

/* ── Modal ── */
.modal-ov{{
  display:none;position:fixed;inset:0;z-index:300;
  background:rgba(0,0,0,.82);
  align-items:center;justify-content:center
}}
.modal-ov.show{{display:flex;animation:fadeUp .22s ease;padding:16px}}
.modal-box{{
  background:#fff;border:3px solid #000;
  max-width:560px;width:100%;
  padding:33px 16px 16px;
  position:relative;
  max-height:85vh;overflow-y:auto
}}
.modal-close{{
  position:absolute;top:16px;right:16px;
  background:#fff;color:#000;
  border:3px solid #000;
  width:36px;height:36px;
  font-size:14px;font-weight:700;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:background .1s,color .1s
}}
.modal-close:hover{{background:#000;color:#fff}}
.modal-cat{{
  font-family:'Space Mono',monospace;
  font-size:10px;letter-spacing:1px;text-transform:uppercase;
  padding:3px 8px;
  background:#000;color:#fff;
  display:inline-block;margin-bottom:16px
}}
.modal-title{{
  font-family:'Archivo Black',sans-serif;
  font-size:28px;line-height:1.1;
  margin-bottom:20px
}}
.modal-detail{{
  font-size:16px;line-height:1.7;color:#000;
  margin-bottom:24px;padding-top:20px;border-top:3px solid #000
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

<div class="modal-ov" id="modal" onclick="mCloseOv(event)">
  <div class="modal-box">
    <button class="modal-close" onclick="mClose()">&#10005;</button>
    <span class="modal-cat" id="m-cat"></span>
    <h2 class="modal-title" id="m-title"></h2>
    <p class="modal-detail" id="m-detail"></p>
    <a class="btn-source" id="m-src" href="#" target="_blank" rel="noopener">LIRE LA SOURCE</a>
  </div>
</div>

<script>
var GH_REPO='agencedajm/digest-matin';
var GH_WORKFLOW='digest.yml';
var _pollRun;

async function doRefresh(){{
  var token=localStorage.getItem('gh_pat');
  if(!token){{
    token=prompt('Token GitHub (une seule fois) :\\nGitHub → Settings → Developer settings → Fine-grained tokens\\nPermission : Actions → Read & write sur digest-matin');
    if(!token)return;
    localStorage.setItem('gh_pat',token.trim());
  }}
  var btn=document.getElementById('btn-refresh');
  btn.disabled=true;btn.textContent='LANCEMENT...';
  document.getElementById('overlay').classList.add('show');
  try{{
    var r=await fetch('https://api.github.com/repos/'+GH_REPO+'/actions/workflows/'+GH_WORKFLOW+'/dispatches',{{
      method:'POST',
      headers:{{'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'}},
      body:JSON.stringify({{ref:'main'}})
    }});
    if(r.status===401){{
      localStorage.removeItem('gh_pat');
      document.getElementById('overlay').classList.remove('show');
      btn.disabled=false;btn.textContent='TOKEN INVALIDE';
      setTimeout(function(){{btn.textContent='ACTUALISER';btn.disabled=false;}},3000);
      return;
    }}
    if(!r.ok)throw new Error('HTTP '+r.status);
    btn.textContent='EN COURS (~3 MIN)';
    // Poll le dernier commit pour detecter la mise a jour
    var initSha=null;
    _pollRun=setInterval(async function(){{
      try{{
        var c=await fetch('https://api.github.com/repos/'+GH_REPO+'/commits/main',{{headers:{{'Authorization':'Bearer '+token}}}});
        var d=await c.json();
        if(!initSha){{initSha=d.sha;return;}}
        if(d.sha!==initSha){{
          clearInterval(_pollRun);
          location.reload();
        }}
      }}catch(e){{}}
    }},10000);
  }}catch(e){{
    document.getElementById('overlay').classList.remove('show');
    btn.disabled=false;btn.textContent='ERREUR';
    setTimeout(function(){{btn.textContent='ACTUALISER';btn.disabled=false;}},3000);
  }}
}}

// Stagger d'entrée sur toutes les cartes
document.querySelectorAll('.card').forEach(function(c,i){{c.style.setProperty('--ci',i)}});

// Modal
var CAT_COLORS={{'strategy':'#000000','copywriting':'#FF0000','visuals':'#0000FF'}};
function openModal(card){{
  var cat=card.dataset.cat||'strategy';
  var color=CAT_COLORS[cat]||'#000';
  var catEl=document.getElementById('m-cat');
  catEl.textContent=card.dataset.label||'';
  catEl.style.background=color;
  document.getElementById('m-title').textContent=card.dataset.title||'';
  document.getElementById('m-detail').textContent=card.dataset.detail||'';
  var src=card.dataset.src||'';
  var el=document.getElementById('m-src');
  el.href=src;el.style.display=src?'inline-block':'none';
  document.getElementById('modal').classList.add('show');
  document.body.style.overflow='hidden';
}}
function mClose(){{
  document.getElementById('modal').classList.remove('show');
  document.body.style.overflow='';
}}
function mCloseOv(e){{if(e.target===document.getElementById('modal'))mClose();}}
document.addEventListener('keydown',function(e){{if(e.key==='Escape')mClose();}});

// Filtre avec fondu
function fil(cat,btn){{
  document.querySelectorAll('.f').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  var visible=0;
  document.querySelectorAll('.card').forEach(function(c){{
    var show=(cat==='all'||c.dataset.cat===cat);
    if(show){{
      c.style.display='';
      var i=visible++;
      c.style.opacity='0';c.style.transform='translateY(8px)';
      setTimeout(function(){{
        c.style.transition='opacity .22s ease,transform .22s ease';
        c.style.opacity='1';c.style.transform='';
      }},i*35);
    }}else{{
      c.style.transition='opacity .14s ease';
      c.style.opacity='0';
      setTimeout(function(){{c.style.display='none';}},140);
    }}
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
    msg["To"] = ", ".join(TO_EMAILS)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.sendmail(GMAIL_USER, TO_EMAILS, msg.as_string())
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

    # Titres des 2 dernières éditions → injectés dans les prompts pour éviter les redites
    past_feed   = load_feed()
    avoid_titles = [
        c.get("title", "")
        for entry in past_feed[:2]
        for c in entry.get("cards", [])
        if c.get("title")
    ]

    for agent in AGENTS:
        cards = research_agent(agent, avoid_titles)
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
