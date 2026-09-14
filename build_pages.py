# -*- coding: utf-8 -*-
"""Разбивает одностраничный сайт на отдельные HTML-файлы для поисковых систем."""
import re, os, shutil

SRC = 'v2.src.html'
OUT = 'dist'
DOMAIN = 'https://biblechurch.by'

s = open(SRC, encoding='utf-8').read()

# ---------- страницы: путь -> (файл, заголовок, описание) ----------
PAGES = [
 ('/',             'index.html',        'Библейская церковь | Брест, Беларусь',
  'Брестская Библейская церковь ЕХБ. Воскресные собрания в 11:00, ул. Наганова, 10, Брест. Библейский клуб, изучение Библии, общение и молитва.'),
 ('/about',        'about.html',        'О церкви — вера, ценности, служители | Библейская церковь, Брест',
  'Во что верит Брестская Библейская церковь ЕХБ, что мы ценим, кто служит в общине и как устроен библейский клуб.'),
 ('/visit',        'visit.html',        'Впервые у нас — как проходит собрание | Библейская церковь, Брест',
  'Собрание длится полтора часа: молитва и пение, чтение Писания, евхаристия, проповедь и общение за кофе. Воскресная школа для детей с 10:00. Вход со стороны парка.'),
 ('/webelieve',    'webelieve.html',    'Во что мы верим — исповедание веры | Библейская церковь, Брест',
  'Исповедание веры Брестской Библейской церкви ЕХБ: Писание, Бог, спасение, церковь и второе пришествие Христа — тринадцать пунктов.'),
 ('/weappreciate', 'weappreciate.html', 'Что мы ценим — девять ориентиров | Библейская церковь, Брест',
  'Авторитет Библии, общность церкви, смирение, рост, семья и благодать — девять ценностей Брестской Библейской церкви.'),
 ('/ministers',    'ministers.html',    'Служители — пасторы и диаконы | Библейская церковь, Брест',
  'Пасторы и диаконы Брестской Библейской церкви ЕХБ. К любому из них можно подойти после воскресного собрания.'),
 ('/bibleclub',    'bibleclub.html',    'Библейский клуб — изучение Писания | Библейская церковь, Брест',
  'Группа для изучения Писания в Бресте: читаем Библию книгу за книгой, внимательно и вместе. Клуб открыт для всех.'),
 ('/contacts',     'contacts.html',     'Контакты — как нас найти | Библейская церковь, Брест',
  'Брест, ул. Наганова, 10. Воскресные собрания в 11:00. Напишите нам через форму, на почту или в Instagram.'),
 ('/privacy',      'privacy.html',      'Политика конфиденциальности | Библейская церковь, Брест',
  'Как Библейская церковь г. Бреста обращается с персональными данными посетителей сайта.'),
]
ROUTE2FILE = {p: f for p, f, _, _ in PAGES}

# ---------- разбираем исходник на части ----------
head_css  = s[s.index('<style>'): s.index('</style>') + len('</style>')]
fonts     = re.search(r'<link href="https://fonts\.googleapis[^>]+>', s).group(0)
header    = s[s.index('<header class="header"'): s.index('</header>') + len('</header>')]
footer    = s[s.index('<footer class="footer">'): s.index('</footer>') + len('</footer>')]
totop     = '<button class="to-top" id="toTop" aria-label="Наверх">&#8593;</button>'
analytics = re.search(r'<!-- Cloudflare Web Analytics.*?</script>', s, re.S).group(0)

bodies = {}
for m in re.finditer(r'<div class="page" data-page="([^"]+)">(.*?)\n</div>\n', s, re.S):
    bodies[m.group(1)] = m.group(2)
assert len(bodies) == len(PAGES), f'нашлось {len(bodies)} страниц вместо {len(PAGES)}'

# ---------- общий скрипт ----------
COMMON_JS = """
(function(){
  var header = document.getElementById('siteHeader');
  var nav    = document.getElementById('siteNav');
  var burger = document.getElementById('navToggle');
  var toTop  = document.getElementById('toTop');

  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  function onScroll(){
    var t = window.pageYOffset || document.documentElement.scrollTop;
    header.classList.toggle('is-solid', t > 40);
    toTop.classList.toggle('is-on', t > 700);
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();

  burger.addEventListener('click', function(){
    var open = document.body.classList.toggle('nav-open');
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape'){
      document.body.classList.remove('nav-open');
      burger.setAttribute('aria-expanded','false');
    }
  });

  toTop.addEventListener('click', function(){ window.scrollTo({top:0, behavior:'smooth'}); });

  /* ---- форма обращения ---- */
  var MAIL_TO = 'biblechurch.by@gmail.com';
  var MAIL_ENDPOINT = 'https://formsubmit.co/ajax/' + MAIL_TO;

  [].slice.call(document.querySelectorAll('.js-form')).forEach(function(f){
    var status = f.querySelector('.form-status');
    var btn    = f.querySelector('button[type=submit]');
    var label  = btn ? btn.textContent : '';

    function say(text, state){
      status.textContent = text;
      status.setAttribute('data-state', state);
      status.hidden = false;
    }

    f.addEventListener('submit', function(e){
      e.preventDefault();
      if (f.querySelector('[name=_honey]').value) return;
      if (!f.checkValidity()){
        say('Заполните имя, контакт и текст сообщения.', 'err');
        var bad = f.querySelector(':invalid');
        if (bad) bad.focus();
        return;
      }
      var data = {};
      new FormData(f).forEach(function(v, k){ if (k !== '_honey') data[k] = v; });
      data._captcha = 'false';
      data._template = 'table';

      btn.disabled = true;
      btn.textContent = 'Отправляем…';
      status.hidden = true;

      fetch(MAIL_ENDPOINT, {
        method: 'POST',
        headers: {'Content-Type':'application/json', 'Accept':'application/json'},
        body: JSON.stringify(data)
      })
      .then(function(r){ if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(){
        f.reset();
        say('Спасибо, сообщение отправлено. Мы ответим на указанный вами контакт.', 'ok');
      })
      .catch(function(){
        say('Не удалось отправить. Напишите, пожалуйста, напрямую на ' + MAIL_TO + ' — или попробуйте ещё раз позже.', 'err');
      })
      .finally(function(){
        btn.disabled = false;
        btn.textContent = label;
      });
    });
  });
})();
"""

CAROUSEL_JS = """
(function(){
  var slides = [].slice.call(document.querySelectorAll('.hero-slide'));
  var dots   = [].slice.call(document.querySelectorAll('.hero-dot'));
  if (slides.length < 2) return;

  var cur = 0, timer = null;
  var calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function show(i){
    cur = (i + slides.length) % slides.length;
    slides.forEach(function(el, n){ el.classList.toggle('is-on', n === cur); });
    dots.forEach(function(d, n){
      d.classList.toggle('is-on', n === cur);
      d.setAttribute('aria-selected', n === cur ? 'true' : 'false');
    });
  }
  function play(){ if (!calm){ stop(); timer = setInterval(function(){ show(cur + 1); }, 6000); } }
  function stop(){ if (timer){ clearInterval(timer); timer = null; } }

  dots.forEach(function(d, n){ d.addEventListener('click', function(){ show(n); play(); }); });

  var hero = document.getElementById('homeHero');
  if (hero){
    hero.addEventListener('mouseenter', stop);
    hero.addEventListener('mouseleave', play);
    hero.addEventListener('focusin', stop);
    hero.addEventListener('focusout', play);
  }
  document.addEventListener('visibilitychange', function(){ document.hidden ? stop() : play(); });
  play();
})();
"""

TOC_JS = """
(function(){
  var links = [].slice.call(document.querySelectorAll('.toc-link'));
  if (!links.length || !('IntersectionObserver' in window)) return;
  var seen = new Set();
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if (en.isIntersecting) seen.add(en.target.id); else seen.delete(en.target.id);
    });
    var first = links.find(function(a){ return seen.has(a.getAttribute('href').slice(1)); });
    links.forEach(function(a){ a.classList.toggle('is-active', a === first); });
  }, {rootMargin: '-25% 0px -60% 0px'});
  document.querySelectorAll('.art').forEach(function(el){ io.observe(el); });
})();
"""


SCHEMA = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Church",
  "name": "Библейская церковь г. Бреста",
  "alternateName": "Брестская Библейская церковь ЕХБ",
  "url": "https://biblechurch.by/",
  "logo": "https://biblechurch.by/assets/favicon.png",
  "image": "https://biblechurch.by/assets/favicon.png",
  "email": "biblechurch.by@gmail.com",
  "slogan": "К недоступному Богу, через доступную церковь",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "ул. Наганова, 10",
    "addressLocality": "Брест",
    "addressRegion": "Брестская область",
    "addressCountry": "BY"
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": "Sunday",
      "opens": "11:00",
      "closes": "12:30",
      "description": "Воскресное собрание"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": "Sunday",
      "opens": "10:00",
      "closes": "11:00",
      "description": "Воскресная школа для детей"
    }
  ],
  "sameAs": [
    "https://www.instagram.com/brestbiblechurch/",
    "https://www.facebook.com/brestbiblechurch/",
    "https://www.youtube.com/channel/UCNiK1NCGnS-ebp_00e8JMTg",
    "https://t.me/brestbiblechurch"
  ]
}
</script>"""

# ---------- сборка ----------
os.makedirs(OUT, exist_ok=True)

def fix_links(html, current_file):
    """Хеш-маршруты -> корневые адреса. Корневые нужны, чтобы ссылки
    одинаково работали и на верхнем уровне, и внутри /events/."""
    for route, fname in sorted(ROUTE2FILE.items(), key=lambda kv: -len(kv[0])):
        target = '/' if fname == 'index.html' else '/' + fname
        html = html.replace(f'href="#{route}"', f'href="{target}"')
    html = html.replace('href="#/events"', '/events.html')
    return html

for route, fname, title, desc in PAGES:
    body = bodies[route]

    # оглавление исповедания: настоящие якоря вместо скриптовых переходов
    body = re.sub(r'<a class="toc-link" href="#/webelieve" data-target="(d\d+)">',
                  r'<a class="toc-link" href="#\1">', body)

    nav = header
    cur_target = './' if fname == 'index.html' else fname
    nav = nav.replace(f'href="#{route}"', f'href="{cur_target}" aria-current="page" class="is-current"')

    parts = [
      '<!DOCTYPE html>', '<html lang="ru">', '<head>',
      '<meta charset="utf-8">',
      '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
      f'<title>{title}</title>',
      f'<meta name="description" content="{desc}">',
      f'<link rel="canonical" href="{DOMAIN}/{"" if fname=="index.html" else fname}">',
      '<meta name="theme-color" content="#14120f">',
      f'<meta property="og:title" content="{title}">',
      f'<meta property="og:description" content="{desc}">',
      '<meta property="og:type" content="website">',
      f'<meta property="og:url" content="{DOMAIN}/{"" if fname=="index.html" else fname}">',
      '<meta property="og:locale" content="ru_RU">',
      '<link rel="icon" href="/favicon.ico" sizes="any">',
      '<link rel="icon" type="image/png" sizes="192x192" href="/assets/favicon.png">',
      '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">',
      '<link rel="preconnect" href="https://fonts.googleapis.com">',
      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
      fonts,
      head_css,
      SCHEMA,
      '</head>', '<body>',
      '<a class="skip" href="#main">Перейти к содержанию</a>',
      fix_links(nav, fname),
      '<main id="main">',
      '<div class="page">' + body + '\n</div>',
      '</main>',
      fix_links(footer, fname),
      totop,
      '<script>' + COMMON_JS + '</script>',
    ]
    if route == '/':      parts.append('<script>' + CAROUSEL_JS + '</script>')
    if route == '/webelieve': parts.append('<script>' + TOC_JS + '</script>')
    parts += [analytics, '</body>', '</html>']

    html = '\n'.join(parts)
    html = fix_links(html, fname)

    # картинки — внешними файлами, чтобы браузер кэшировал их между страницами
    for token, path in [('__QR__','assets/erip-qr.png'),
                        ('__LOGO_WHITE__','assets/logo-white.png'),
                        ('__LOGO_BLACK__','assets/logo-black.png'),
                        ('__FAVICON__','assets/favicon.png'),
                        ('__P_SIMONCHIK__','assets/person-simonchik.jpg'),
                        ('__P_KONYUCHKO__','assets/person-konyuchko.jpg'),
                        ('__P_VEREMCHUK_D__','assets/person-veremchuk-d.jpg'),
                        ('__P_DEMIDOVICH__','assets/person-demidovich.jpg'),
                        ('__P_ROY__','assets/person-roy.jpg'),
                        ('__P_VEREMCHUK_DAN__','assets/person-veremchuk-dan.jpg')]:
        html = html.replace(f'src="data:image/png;base64,{token}"', f'src="/{path}"')
        html = html.replace(f'src="data:image/jpeg;base64,{token}"', f'src="/{path}"')

    # страницы больше не переключаются скриптом
    html = html.replace('.page{display:none}\n.page.is-active{display:block}', '.page{display:block}')

    open(os.path.join(OUT, fname), 'w', encoding='utf-8').write(html)
    print(f'{fname:20} {len(html.encode())/1024:6.0f} КБ')

# ---------- картинки ----------
os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
for f in ['logo-white.png','logo-black.png','favicon.png','apple-touch-icon.png','erip-qr.png','person-simonchik.jpg',
          'person-konyuchko.jpg','person-veremchuk-d.jpg','person-demidovich.jpg',
          'person-roy.jpg','person-veremchuk-dan.jpg']:
    shutil.copy(os.path.join('assets', f), os.path.join(OUT, 'assets', f))

shutil.copy('favicon.ico', os.path.join(OUT, 'favicon.ico'))

# файл привязки домена — без него GitHub Pages вернётся на brestchurch.github.io
open(os.path.join(OUT, 'CNAME'), 'w', encoding='utf-8').write('biblechurch.by\n')


# ================= СОБЫТИЯ =================
import json, html as _html
from datetime import date as _date

MONTHS = ['января','февраля','марта','апреля','мая','июня',
          'июля','августа','сентября','октября','ноября','декабря']

def ru_date(iso):
    y, m, d = (int(x) for x in iso.split('-'))
    return f'{d} {MONTHS[m-1]} {y}'

def shell(title, desc, canonical, body_html, schema=SCHEMA, extra_js=''):
    parts = [
      '<!DOCTYPE html>', '<html lang="ru">', '<head>',
      '<meta charset="utf-8">',
      '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
      f'<title>{title}</title>',
      f'<meta name="description" content="{desc}">',
      f'<link rel="canonical" href="{DOMAIN}{canonical}">',
      '<meta name="theme-color" content="#14120f">',
      f'<meta property="og:title" content="{title}">',
      f'<meta property="og:description" content="{desc}">',
      '<meta property="og:type" content="article">',
      f'<meta property="og:url" content="{DOMAIN}{canonical}">',
      '<meta property="og:locale" content="ru_RU">',
      '<link rel="icon" href="/favicon.ico" sizes="any">',
      '<link rel="icon" type="image/png" sizes="192x192" href="/assets/favicon.png">',
      '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">',
      '<link rel="preconnect" href="https://fonts.googleapis.com">',
      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
      fonts, head_css, schema,
      '</head>', '<body>',
      '<a class="skip" href="#main">Перейти к содержанию</a>',
      fix_links(header, ''),
      '<main id="main">', '<div class="page">', body_html, '</div>', '</main>',
      fix_links(footer, ''), totop,
      '<script>' + COMMON_JS + '</script>',
    ]
    if extra_js: parts.append('<script>' + extra_js + '</script>')
    parts += [analytics, '</body>', '</html>']
    out = '\n'.join(parts).replace('.page{display:none}\n.page.is-active{display:block}', '.page{display:block}')
    for token, path in [('__LOGO_WHITE__','assets/logo-white.png'),
                        ('__LOGO_BLACK__','assets/logo-black.png')]:
        out = out.replace(f'src="data:image/png;base64,{token}"', f'src="/{path}"')
    return out

data = json.load(open('events.json', encoding='utf-8'))
events = sorted(data['events'], key=lambda e: e['date'], reverse=True)   # новые сверху

def media_src(v):
    return v if v.startswith('http') else '/assets/' + v

# --- лента ---
rows = []
for e in events:
    thumb = f'<img class="event-thumb" loading="lazy" src="{media_src(e["image"])}" alt="">' if e.get('image') else ''
    rows.append(f"""      <article class="event">
        <div class="event-date">{ru_date(e['date'])}<span class="event-kind">{_html.escape(e.get('kind',''))}</span></div>
        <div>
          {thumb}
          <h3><a href="/events/{e['slug']}.html">{_html.escape(e['title'])}</a></h3>
          <p>{_html.escape(e['summary'])}</p>
          <a class="tlink" href="/events/{e['slug']}.html">Читать</a>
        </div>
      </article>""")

feed = '\n'.join(rows) if rows else '      <p class="events-empty">Пока записей нет.</p>'

events_body = f"""  <section class="hero hero--page hero--flat">
    <div class="wrap">
      <span class="label" style="color:var(--accent)">Что происходило в церкви</span>
      <h1>События</h1>
    </div>
  </section>

  <section class="sec">
    <div class="wrap narrow">
      <div class="events">
{feed}
      </div>
    </div>
  </section>"""

open(os.path.join(OUT, 'events.html'), 'w', encoding='utf-8').write(
  shell('События церкви — проповеди, конференции, встречи | Библейская церковь, Брест',
        'Записи о прошедших событиях Брестской Библейской церкви: проповеди, конференции, крещения и встречи общины.',
        '/events.html', events_body))
print(f'events.html          записей: {len(events)}')

# --- отдельные страницы ---
os.makedirs(os.path.join(OUT, 'events'), exist_ok=True)
for e in events:
    media = ''
    if e.get('image'):
        media = f'<img class="article-media" src="{media_src(e["image"])}" alt="{_html.escape(e["title"])}">'
    paras = '\n      '.join(f'<p>{_html.escape(p)}</p>' for p in e['body'])
    video = ''
    if e.get('video'):
        video = (f'<p style="margin-top:clamp(26px,3vw,36px)">'
                 f'<a class="btn btn--fill" href="{e["video"]}" target="_blank" rel="noopener">Смотреть запись</a></p>')

    ev_schema = ('<script type="application/ld+json">' + json.dumps({
        "@context":"https://schema.org","@type":"Event",
        "name": e['title'],
        "startDate": e['date'],
        "eventStatus":"https://schema.org/EventScheduled",
        "eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",
        "description": e['summary'],
        "url": f"{DOMAIN}/events/{e['slug']}.html",
        "location":{"@type":"Place","name":"Библейская церковь г. Бреста",
                    "address":{"@type":"PostalAddress","streetAddress":"ул. Наганова, 10",
                               "addressLocality":"Брест","addressCountry":"BY"}},
        "organizer":{"@type":"Organization","name":"Библейская церковь г. Бреста","url":DOMAIN+"/"}
    }, ensure_ascii=False, indent=2) + '</script>')

    body = f"""  <section class="hero hero--page hero--flat">
    <div class="wrap">
      <span class="label" style="color:var(--accent)">{_html.escape(e.get('kind',''))} · {ru_date(e['date'])}</span>
      <h1>{_html.escape(e['title'])}</h1>
    </div>
  </section>

  <section class="sec">
    <div class="wrap">
      <div class="article">
      {media}
      <p class="lead">{_html.escape(e['summary'])}</p>
      {paras}
      {video}
      <p class="article-back"><a class="tlink" href="/events.html">← Все события</a></p>
      </div>
    </div>
  </section>"""

    open(os.path.join(OUT, 'events', e['slug'] + '.html'), 'w', encoding='utf-8').write(
      shell(f"{e['title']} | Библейская церковь, Брест", e['summary'],
            f"/events/{e['slug']}.html", body, schema=ev_schema))
    print(f'  events/{e["slug"]}.html')


# ---------- robots.txt и sitemap.xml ----------
open(os.path.join(OUT,'robots.txt'),'w',encoding='utf-8').write(
f"""User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
""")

urls = []
for route, fname, _, _ in PAGES:
    loc = DOMAIN + '/' + ('' if fname=='index.html' else fname)
    pri = '1.0' if fname=='index.html' else ('0.3' if fname=='privacy.html' else '0.8')
    urls.append(f'  <url>\n    <loc>{loc}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>{pri}</priority>\n  </url>')
urls.append(f'  <url>\n    <loc>{DOMAIN}/events.html</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>')
for e in events:
    urls.append(f'  <url>\n    <loc>{DOMAIN}/events/{e["slug"]}.html</loc>\n    <changefreq>yearly</changefreq>\n    <priority>0.6</priority>\n  </url>')
open(os.path.join(OUT,'sitemap.xml'),'w',encoding='utf-8').write(
 '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
 + '\n'.join(urls) + '\n</urlset>\n')

print('\nrobots.txt и sitemap.xml созданы')
