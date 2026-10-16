#!/usr/bin/env python3
"""
Builds the Windsor Place of Wilmington static site.

    python3 build.py           # build
    python3 build.py --serve   # build, then preview at http://localhost:8000

Reads page bodies from content/*.html, wraps them in the shared header/footer,
adds SEO tags and structured data, copies static/ assets, and writes everything
to public/ — that folder is what you upload to your host.

No dependencies beyond Python 3.8+.
"""
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "public"

# ---------------------------------------------------------------------------
# Site facts — change these in one place.
# ---------------------------------------------------------------------------
SITE = {
    "name": "Windsor Place of Wilmington",
    # Full address of the site's home page. Any path after the domain (GitHub Pages puts the repo
    # name there) is added to every link automatically. With a custom domain, use e.g.
    # "https://www.windsorplaceofwilmington.com".
    "domain": "https://mattmartin1919.github.io/windsorplaceofwilmington.com",
    # True keeps search engines from indexing the site. Set to False at launch.
    "noindex": True,
    # Placeholder numbers (555-01xx is reserved for fiction). Real ones: 978-988-2300, fax 978-988-2333.
    "phone": "978-555-0100",
    "tel": "+19785550100",
    "fax": "978-555-0101",
    "fax_tel": "+19785550101",
    "street": "92 West Street",
    "city": "Wilmington",
    "region": "MA",
    "zip": "01887",
    "maps": "https://maps.app.goo.gl/R5K6SDRBok8Wr7iu6",
    "facebook": "https://www.facebook.com/WindsorPlaceOfWilmington",
    # Analytics and Search Console are off for now. To turn them back on, paste the old values in:
    #   gtm: "GTM-NH26X2S"   google_verify: "LDWsxNNOIrc_Pk7oG-ZYqnnKVJUTg5uaBsOPofjoQPA"
    "gtm": "",
    "google_verify": "",
    "facebook_verify": "0usht0l71j7mznqfh35cgms1oclnd3",
    "areas": ["Wilmington", "Reading", "North Reading", "Stoneham", "Woburn", "Burlington",
              "Andover", "North Andover", "Tewksbury", "Wakefield", "Melrose", "Malden",
              "Lowell", "Lexington", "Boston"],
}

NAV = [
    ("Care options", "/care-options/"),
    ("Assisted living", "/assisted-living/"),
    ("Memory care", "/memory-care/"),
    ("Residences", "/residences/"),
    ("Life here", "/lifestyle/"),
    ("About us", "/about/"),
    ("FAQ", "/faq/"),
]

# Old URLs from the previous site → new pages (written to public/_redirects).
REDIRECTS = {
    "/home-old-changed-old": "/",
    "/place": "/residences/",
    "/place/apartments": "/residences/",
    "/place/floor-plans": "/residences/#floor-plans",
    "/place/home-amenities": "/residences/#amenities",
    "/place/technology_advantages": "/residences/#technology",
    "/place/environmentally-friendly": "/residences/#green-building",
    "/lifestyle": "/lifestyle/",
    "/lifestyle/your-community": "/lifestyle/#location",
    "/lifestyle/activities": "/lifestyle/#activities",
    "/lifestyle/dining": "/lifestyle/#dining",
    "/lifestyle/exercise-wellness": "/lifestyle/#wellness",
    "/lifestyle/photos": "/lifestyle/#photos",
    "/service": "/care-options/",
    "/service/independence-plan": "/independent-living/",
    "/service/assisted-living-plan": "/assisted-living/",
    "/service/enhanced-care-plan": "/assisted-living/#enhanced-care",
    "/service/alzheimers-care": "/memory-care/",
    "/service/respite-care": "/respite-care/",
    "/service/medication-management": "/care-options/#medication-management",
    "/service/30-day-trial": "/respite-care/#trial-stay",
    "/benefits": "/about/",
    "/benefits/for-residents": "/assisted-living/",
    "/benefits/for-families": "/about/#families",
    "/benefits/for-professionals": "/about/#professionals",
    "/about-us": "/about/",
    "/about-us/employment": "/careers/",
    "/about-us/directions": "/contact/#directions",
    "/about-us/testimonials": "/about/#families-say",
    "/testimonial": "/about/#families-say",
    "/about-us/resources": "/faq/",
    "/contact": "/contact/",
    "/contact-us": "/contact/",
    "/copy-of-test-popup-paperform4377026c": "/contact/",
}

# ---------------------------------------------------------------------------
# Reusable blocks — use {{name}} inside content files.
# ---------------------------------------------------------------------------
ICON_PHONE = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
ICON_CAL = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>'


def img(name, alt, sizes="100vw", eager=False, cls=""):
    """Responsive <img>. Expects static/img/<name>.jpg and <name>-sm.jpg (made by get-images.sh)."""
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="/img/{name}.jpg" srcset="/img/{name}-sm.jpg 800w, /img/{name}.jpg 1920w" '
            f'sizes="{sizes}" alt="{html.escape(alt)}" {loading}>')


QUOTES_ALL = [
    ("The staff at Windsor Place is kind and extremely helpful and will do almost anything to help a resident.", "Karen R."),
    ("The loving care you give to my mother and other residents every day is exceptional.", "Carol P."),
    ("He is happy, cleaner, well-fed and enjoying Windsor Place, so we really can't ask for anything more.", "Dale D."),
    ("I am positive that having proactive owners is what makes this place as lovely as it is!", "Alice W."),
    ("The words to describe your wonderful staff are kind, conscientious, and compassionate.", "Lorna T."),
    ("The dining room is beautiful and the food is very good.", "Judy G."),
    ("I am SUPER impressed by the amount of activities you have scheduled for the residents.", "Jackie"),
    ("Our heartfelt thanks for making our dad's life there so enjoyable.", "The Walsh family"),
    ("Windsor Place is a wonderful facility for our loved ones who can't live alone.", "Gail H."),
    ("She loved the staff, people, food and activities.", "Marlene C."),
    ("You are truly dedicated staff and you do your job well.", "Bob O."),
    ("Everyone was so warm and friendly.", "Liz & Mike S."),
    ("I'd like to thank you for all your efforts to keep everyone safe at WP.", "Natalie P."),
    ("Everyone I have met has been PERFECT.", "Mary C."),
    ("We will remember his time at Windsor Place with much fondness.", "Family of Hugh M."),
    ("I like the people and the way that Windsor Place of Wilmington is run.", "Tom"),
]


def quote(q, who):
    return f'<blockquote class="quote"><p>“{html.escape(q)}”</p><footer>{html.escape(who)}</footer></blockquote>'


def blocks():
    s = SITE
    phone_btn = f'<a class="btn btn-primary" href="tel:{s["tel"]}">{ICON_PHONE}Call {s["phone"]}</a>'
    tour_btn = f'<a class="btn btn-outline" href="/contact/">{ICON_CAL}Book a tour</a>'
    b = {
        "phone": s["phone"],
        "tel": s["tel"],
        "fax": s["fax"],
        "phone_btn": phone_btn,
        "tour_btn": tour_btn,
        "cta_buttons": f'<div class="btn-row">{phone_btn}{tour_btn}</div>',
        "quotes": '<div class="quotes">' + "".join(quote(q, w) for q, w in QUOTES_ALL[:3]) + "</div>",
        "quotes_all": '<div class="quote-wall">' + "".join(quote(q, w) for q, w in QUOTES_ALL) + "</div>",
        "cta_band": f'''
<section class="cta-band" aria-labelledby="cta-band-h">
  <div class="wrap">
    <div>
      <h2 id="cta-band-h">Come for lunch. Stay for a tour.</h2>
      <p>Lunch in our dining room is on us any weekday. Call ahead and we'll save you a table and show you around afterward.</p>
    </div>
    <div class="btn-row">
      <a class="btn btn-light" href="tel:{s["tel"]}">{ICON_PHONE}Call {s["phone"]}</a>
      <a class="btn btn-light" href="/contact/">{ICON_CAL}Book a visit</a>
    </div>
  </div>
</section>''',
        "care_table": CARE_TABLE,
        "tour_form": TOUR_FORM,
        "gallery": gallery_html(),
    }
    return b


CARE_TABLE = '''
<table class="care-table">
  <caption class="visually-hidden">How our care options compare</caption>
  <thead>
    <tr><th scope="col">Option</th><th scope="col">Who it suits</th><th scope="col">Personal care included</th><th scope="col">Good to know</th></tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row"><a href="/independent-living/">Independent living</a><span>Independence Plan</span></th>
      <td data-label="Who it suits">People who are managing well but would rather not live alone</td>
      <td data-label="Personal care included">None built in. Staff are on site 24 hours a day if you need them.</td>
      <td data-label="Good to know">Switch to assisted living in the same building if needs change.</td>
    </tr>
    <tr>
      <th scope="row"><a href="/assisted-living/">Assisted living</a><span>Assisted Living Plan</span></th>
      <td data-label="Who it suits">Mostly independent, with some help needed day to day</td>
      <td data-label="Personal care included">Up to 1 hour a day: showers or whirlpool baths, help with daily tasks, medication reminders</td>
      <td data-label="Good to know">Add services any time, short or long term.</td>
    </tr>
    <tr>
      <th scope="row"><a href="/assisted-living/#enhanced-care">Enhanced care</a><span>Enhanced Care Plan</span></th>
      <td data-label="Who it suits">Residents who need more hands-on help</td>
      <td data-label="Personal care included">Up to 2 hours a day of personal care, including showers and medication support</td>
      <td data-label="Good to know">Planned with family, doctors and pharmacists.</td>
    </tr>
    <tr>
      <th scope="row"><a href="/memory-care/">Memory care</a><span>The Carlysle</span></th>
      <td data-label="Who it suits">People living with Alzheimer's disease or other memory loss</td>
      <td data-label="Personal care included">Up to 2 hours a day, with caregivers trained in dementia care on duty around the clock</td>
      <td data-label="Good to know">Secure entrance, private garden, smaller dining room.</td>
    </tr>
  </tbody>
</table>'''

TOUR_FORM = '''
<form class="form-card" name="tour" action="/thank-you/" data-placeholder>
  <h2 class="mt-0" style="font-size:var(--step-2)">Book a tour or ask a question</h2>
  <p class="muted">We'll call you back within one business day. There's no obligation.</p>
  <div class="field-row">
    <div class="field"><label for="f-name">Your name</label><input id="f-name" name="name" autocomplete="name" required></div>
    <div class="field"><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required></div>
  </div>
  <div class="field"><label for="f-email">Email <span class="hint">(optional)</span></label><input id="f-email" name="email" type="email" autocomplete="email"></div>
  <fieldset class="field">
    <legend>Who are you looking for?</legend>
    <div class="choice-row">
      <label><input type="radio" name="for" value="Myself"> Myself</label>
      <label><input type="radio" name="for" value="A parent"> A parent</label>
      <label><input type="radio" name="for" value="A spouse or partner"> A spouse or partner</label>
      <label><input type="radio" name="for" value="A client"> A client</label>
    </div>
  </fieldset>
  <div class="field">
    <label for="f-interest">What would you like to do?</label>
    <select id="f-interest" name="interest">
      <option>Tour the community</option>
      <option>Come for a free weekday lunch</option>
      <option>Ask about assisted living</option>
      <option>Ask about memory care</option>
      <option>Ask about independent living</option>
      <option>Ask about a respite or 30-day trial stay</option>
      <option>Ask about pricing</option>
    </select>
  </div>
  <div class="field"><label for="f-when">Best day or time to visit <span class="hint">(optional)</span></label><input id="f-when" name="preferred_time" placeholder="e.g. Tuesday afternoon"></div>
  <div class="field"><label for="f-msg">Anything we should know? <span class="hint">(optional)</span></label><textarea id="f-msg" name="message"></textarea></div>
  <button class="btn btn-primary" type="submit">Send request</button>
  <p class="form-note">Prefer to talk now? Call <a href="tel:{tel}">{phone}</a>.</p>
</form>'''.format(tel=SITE["tel"], phone=SITE["phone"])


GALLERY_DEFAULT = [
    ("entrance", "The front entrance of Windsor Place"),
    ("dining-entry", "Columned entry to the main dining room"),
    ("patio", "Hydrangeas in bloom on the patio"),
    ("assisted", "A resident sharing a laugh with a caregiver"),
    ("independent", "A couple enjoying a glass of wine"),
    ("family", "A resident with her granddaughter"),
]


def gallery_html():
    """Default photos plus anything placed in static/img/gallery/ (filename becomes the caption)."""
    items = []
    for name, alt in GALLERY_DEFAULT:
        items.append(f'<li><figure>{img(name, alt, "(max-width: 640px) 100vw, 33vw")}</figure></li>')
    gdir = STATIC / "img" / "gallery"
    if gdir.exists():
        for p in sorted(gdir.iterdir()):
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                cap = re.sub(r"[-_]+", " ", re.sub(r"-\d+w$", "", p.stem)).strip().capitalize()
                items.append(f'<li><figure><img src="/img/gallery/{p.name}" alt="{html.escape(cap)}" loading="lazy" decoding="async"><figcaption>{html.escape(cap)}</figcaption></figure></li>')
    return '<ul class="gallery">' + "".join(items) + "</ul>"


# ---------------------------------------------------------------------------
# Structured data
# ---------------------------------------------------------------------------
def org_schema():
    s = SITE
    return {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": s["domain"] + "/#community",
        "name": s["name"],
        "alternateName": "Windsor Place",
        "description": "Family-owned assisted living, memory care and independent living community on 16 wooded acres in Wilmington, Massachusetts.",
        "url": s["domain"] + "/",
        "telephone": s["tel"],
        "faxNumber": s["fax_tel"],
        "image": s["domain"] + "/img/entrance.jpg",
        "logo": s["domain"] + "/img/logo.png",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": s["street"],
            "addressLocality": s["city"],
            "addressRegion": s["region"],
            "postalCode": s["zip"],
            "addressCountry": "US",
        },
        "hasMap": s["maps"],
        "sameAs": [s["facebook"]],
        "areaServed": [{"@type": "City", "name": f"{a}, MA"} for a in s["areas"]],
        "amenityFeature": [
            {"@type": "LocationFeatureSpecification", "name": n, "value": True}
            for n in ["24-hour staff", "Chef-prepared meals", "Scheduled transportation",
                      "Beauty salon", "Fitness area", "Library", "Pub lounge",
                      "Secure memory care garden", "Weekly housekeeping", "Resident parking"]
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Senior living and care",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "url": s["domain"] + u}}
                for n, u in [("Assisted living", "/assisted-living/"), ("Memory care", "/memory-care/"),
                             ("Independent living", "/independent-living/"), ("Respite care", "/respite-care/"),
                             ("Medication management", "/care-options/#medication-management")]
            ],
        },
    }


def breadcrumb_schema(crumbs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE["domain"] + u}
            for i, (n, u) in enumerate(crumbs)
        ],
    }


def faq_schema(body):
    qs = []
    for m in re.finditer(r"<details[^>]*>\s*<summary>(.*?)</summary>\s*<div class=\"answer\">(.*?)</div>\s*</details>", body, re.S):
        q = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        a = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        qs.append({"@type": "Question", "name": html.unescape(q), "acceptedAnswer": {"@type": "Answer", "text": html.unescape(a)}})
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qs} if qs else None


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def header(path):
    items = []
    for label, url in NAV:
        cur = ' aria-current="page"' if path.startswith(url) else ""
        items.append(f'<li><a href="{url}"{cur}>{label}</a></li>')
    items.append('<li class="nav-cta"><a href="/contact/">Book a tour</a></li>')
    s = SITE
    return f'''
<a class="skip-link" href="#main">Skip to main content</a>
<div class="topbar"><div class="wrap">
  <span>Family-owned and operated in Wilmington</span>
  <span>Questions? <a href="tel:{s["tel"]}">{s["phone"]}</a></span>
</div></div>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="{s["name"]} home">
      <span class="brand-name">Windsor Place</span>
      <span class="brand-sub">of Wilmington, Massachusetts</span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      <span class="nav-toggle-label">Menu</span>
    </button>
    <nav class="primary-nav" id="primary-nav" aria-label="Main">
      <ul>{"".join(items)}</ul>
    </nav>
  </div>
</header>'''


def footer():
    s = SITE
    year = date.today().year
    return f'''
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <span class="brand-name">Windsor Place of Wilmington</span>
        <address>
          {s["street"]}<br>{s["city"]}, {s["region"]} {s["zip"]}<br>
          Phone <a href="tel:{s["tel"]}">{s["phone"]}</a><br>
          Fax {s["fax"]}
        </address>
        <ul style="margin-top:1rem"><li><a href="{s["maps"]}" rel="noopener">Get directions</a></li><li><a href="{s["facebook"]}" rel="noopener">Windsor Place on Facebook</a></li></ul>
      </div>
      <div>
        <h2>Care</h2>
        <ul>
          <li><a href="/assisted-living/">Assisted living</a></li>
          <li><a href="/memory-care/">Memory care</a></li>
          <li><a href="/independent-living/">Independent living</a></li>
          <li><a href="/respite-care/">Respite &amp; 30-day trial stays</a></li>
          <li><a href="/care-options/">Compare care options</a></li>
        </ul>
      </div>
      <div>
        <h2>Community</h2>
        <ul>
          <li><a href="/residences/">Residences &amp; floor plans</a></li>
          <li><a href="/lifestyle/">Dining, activities &amp; wellness</a></li>
          <li><a href="/about/">About the family</a></li>
          <li><a href="/faq/">Questions families ask</a></li>
          <li><a href="/careers/">Careers</a></li>
          <li><a href="/contact/">Contact &amp; directions</a></li>
        </ul>
      </div>
    </div>
    <p class="footer-areas">Assisted living and memory care serving {", ".join(s["areas"][:-1])} and greater Boston, about 20 minutes from downtown via I-93.</p>
    <div class="footer-legal">
      <span>© {year} Windsor Place of Wilmington. Certified assisted living residence, Massachusetts Executive Office of Aging &amp; Independence. <a href="/docs/eoai-certificate-2026.pdf">View certificate (PDF)</a></span>
      <span>Equal Opportunity Employer</span>
    </div>
  </div>
</footer>
<div class="action-bar" aria-label="Quick actions">
  <a class="btn btn-primary" href="tel:{s["tel"]}">{ICON_PHONE}Call us</a>
  <a class="btn btn-outline" href="/contact/">{ICON_CAL}Book a tour</a>
</div>'''


def page(meta, body):
    s = SITE
    path = meta["path"]
    url = s["domain"] + path
    title = meta["title"]
    desc = meta["description"]
    og_image = s["domain"] + "/img/" + meta.get("image", "entrance") + ".jpg"
    robots = "noindex,nofollow" if s["noindex"] else meta.get("robots", "index,follow")

    schemas = []
    if path == "/":
        schemas.append(org_schema())
        schemas.append({"@context": "https://schema.org", "@type": "WebSite", "name": s["name"], "url": s["domain"] + "/"})
    else:
        schemas.append({"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url,
                        "about": {"@id": s["domain"] + "/#community"}})
    crumbs = None
    if path != "/" and meta.get("crumb"):
        crumbs = [("Home", "/")]
        if meta.get("parent"):
            p_label, p_url = meta["parent"].split("|")
            crumbs.append((p_label.strip(), p_url.strip()))
        crumbs.append((meta["crumb"], path))
        schemas.append(breadcrumb_schema(crumbs))
    fs = faq_schema(body)
    if fs and meta.get("faq_schema", "yes") == "yes":
        schemas.append(fs)

    # Fill blocks
    b = blocks()
    if crumbs:
        b["breadcrumb"] = '<nav class="breadcrumb" aria-label="Breadcrumb"><ol>' + "".join(
            f'<li><a href="{u}">{html.escape(n)}</a></li>' if i < len(crumbs) - 1 else f'<li aria-current="page">{html.escape(n)}</li>'
            for i, (n, u) in enumerate(crumbs)) + "</ol></nav>"
    else:
        b["breadcrumb"] = ""
    body = re.sub(r"\{\{\s*img\s+(\S+)\s+\"([^\"]*)\"(?:\s+\"([^\"]*)\")?(\s+eager)?\s*\}\}",
                  lambda m: img(m.group(1), m.group(2), m.group(3) or "100vw", bool(m.group(4))), body)
    body = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: b.get(m.group(1), m.group(0)), body)
    desc = desc.replace("{{phone}}", s["phone"])
    leftover = re.findall(r"\{\{[^}]*\}\}", body)
    if leftover:
        raise SystemExit(f"Unknown block(s) in {path}: {leftover}")

    gtm_head = gtm_body = ""
    if s["gtm"]:
        gtm_head = f"""<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{s["gtm"]}');</script>"""
        gtm_body = f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={s["gtm"]}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>'

    preload = ""
    if meta.get("preload"):
        n = meta["preload"]
        preload = f'<link rel="preload" as="image" href="/img/{n}.jpg" imagesrcset="/img/{n}-sm.jpg 800w, /img/{n}.jpg 1920w" imagesizes="(max-width: 860px) 90vw, 45vw">'

    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in schemas)

    return with_base(f'''<!doctype html>
<html lang="en-US" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{s["name"]}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.region" content="US-MA">
<meta name="geo.placename" content="Wilmington, Massachusetts">
<meta name="theme-color" content="#1e3b34">
{f'<meta name="google-site-verification" content="{s["google_verify"]}">' + chr(10) if s["google_verify"] else ""}<meta name="facebook-domain-verification" content="{s["facebook_verify"]}">
<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/fonts/young-serif-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/atkinson-hyperlegible-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/site.css?v={BUILD_ID}">
{preload}
{ld}
{gtm_head}
</head>
<body>
{gtm_body}
{header(path)}
<main id="main">
{body}
</main>
{footer()}
<script src="/js/site.js?v={BUILD_ID}" defer></script>
</body>
</html>
''')


def with_base(doc):
    """Prefix root-relative links ("/about/") with BASE, for hosting under a sub-path."""
    doc = re.sub(r'(\s(?:href|src|action)=")/(?!/)', rf"\1{BASE}/", doc)
    return re.sub(r'(\s(?:srcset|imagesrcset)=")([^"]*)"',
                  lambda m: m.group(1) + re.sub(r"(^|,\s*)/(?!/)", rf"\1{BASE}/", m.group(2)) + '"', doc)


def parse(file):
    text = file.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, text[m.end():]


BUILD_ID = date.today().strftime("%Y%m%d")
BASE = urlparse(SITE["domain"]).path.rstrip("/")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)

    pages = []
    for f in sorted(CONTENT.glob("*.html")):
        meta, body = parse(f)
        path = meta["path"]
        dest = OUT / ("404.html" if path == "/404.html" else path.strip("/") + "/index.html" if path != "/" else "index.html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page(meta, body), encoding="utf-8")
        if meta.get("robots", "index").startswith("index"):
            pages.append((path, meta.get("priority", "0.7")))
        print("built", path)

    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p, pr in sorted(pages, key=lambda x: -float(x[1])):
        sm.append(f"  <url><loc>{SITE['domain']}{p}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    rules = "Disallow: /" if SITE["noindex"] else "Allow: /\nDisallow: /thank-you/"
    (OUT / "robots.txt").write_text(f"User-agent: *\n{rules}\n\nSitemap: {SITE['domain']}/sitemap.xml\n")

    # Netlify / Cloudflare Pages format (GitHub Pages ignores this file)
    lines = ["# Old site URLs → new pages (301 keeps search rankings)"]
    for old, new in REDIRECTS.items():
        lines.append(f"{old}  {new}  301")
        if not old.endswith("/") and old != "/":
            lines.append(f"{old}/  {new}  301")
    lines.append("http://windsorplaceofwilmington.com/*  https://www.windsorplaceofwilmington.com/:splat  301!")
    lines.append("https://windsorplaceofwilmington.com/*  https://www.windsorplaceofwilmington.com/:splat  301!")
    (OUT / "_redirects").write_text("\n".join(lines) + "\n")

    (OUT / "site.webmanifest").write_text(json.dumps({
        "name": SITE["name"], "short_name": "Windsor Place", "start_url": BASE + "/",
        "display": "browser", "background_color": "#f6f7f4", "theme_color": "#1e3b34",
        "icons": [{"src": BASE + "/img/favicon.svg", "sizes": "any", "type": "image/svg+xml"}],
    }, indent=2))

    missing = [n for n in [g[0] for g in GALLERY_DEFAULT] + ["memory"] if not (OUT / "img" / f"{n}.jpg").exists()]
    if missing:
        print("\nNote: photos not found yet:", ", ".join(missing), "— run ./get-images.sh, then build again.")
    print(f"\nDone. Upload the contents of {OUT}/")


def serve(port=8000):
    """Serve public/ under BASE, the way GitHub Pages does."""
    import functools
    import http.server

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if BASE and path.startswith(BASE + "/"):
                path = path[len(BASE):]
            elif BASE and path.split("?")[0] == BASE:
                path = "/"
            return super().translate_path(path)

    print(f"Previewing at http://localhost:{port}{BASE}/  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("", port), functools.partial(Handler, directory=str(OUT))).serve_forever()


if __name__ == "__main__":
    main()
    if "--serve" in sys.argv:
        serve()
