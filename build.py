#!/usr/bin/env python3
"""
Flyover Con — static site generator for flyovercon.ink
Run:  python3 build.py      →  regenerates the entire ./site/ directory
Never edit ./site/ by hand; it is wiped and rebuilt on every run.
"""
import json, os, re, shutil, sys

# ---------------------------------------------------------------- constants
BASE            = "https://www.flyovercon.ink"
SITE_NAME       = "Flyover Con"
TAGLINE         = "The Midwest's conference for screen printers and decorators."
EMAIL           = "ryan@flyovercon.ink"
TODAY           = "2026-08-03"
UPDATED_HUMAN   = "August 2026"
PARENT_NAME     = "P&amp;M Apparel"
PARENT_URL      = "https://www.pmapparel.com"
PARENT_ADDR     = "1100 S 5th St, Polk City, IA 50226"
IG              = "https://www.instagram.com/flyover_con/"
FB              = "https://www.facebook.com/profile.php?id=61556233233152"
OUT             = "site"

NAV = [("index.html","Home"),("about.html","About"),("years-past.html","Years Past"),
       ("speakers.html","Speakers"),("location.html","Location")]

SPEAKERS = [
  {
    "badge": "RT",
    "name": "Ryan Toney",
    "role": "Owner &middot; P&amp;M Apparel",
    "bio": "Co-owner of P&amp;M Apparel, a third-generation, family-run decorated apparel company in Iowa. Focuses on long-term strategy, systems, and sales, building scalable processes that support both clients and the internal team. Previously served on the Gildan Board of Decorators and currently serves on the Chipply Client Council.",
    "years": [
      "2026"
    ],
    "photo": "ryan-toney"
  },
  {
    "badge": "MG",
    "name": "Megan Griffith",
    "role": "Owner &amp; Art Director &middot; P&amp;M Apparel",
    "bio": "Co-owner and Art Director of P&amp;M Apparel, overseeing design, production, and day-to-day operations. Named a Screen Printing Magazine Rising Star and recognized as one of the Six Women in Screen Printing in 2024.",
    "years": [
      "2026"
    ],
    "photo": "megan-griffith"
  },
  {
    "badge": "AC",
    "name": "Amanda Clark",
    "role": "Financials Manager &middot; P&amp;M Apparel",
    "bio": "Oversees financial operations at P&amp;M Apparel, ensuring accuracy, efficiency, and clarity across the business. Self-taught in the intricacies of taxes and QuickBooks.",
    "years": [
      "2026"
    ],
    "photo": "amanda-clark"
  },
  {
    "badge": "AD",
    "name": "Alexis Davis",
    "role": "Account Manager &middot; P&amp;M Apparel",
    "bio": "Works closely with clients to manage orders, timelines, and communication from start to finish. Known for organization, responsiveness, and an approach to selling with empathy.",
    "years": [
      "2026"
    ],
    "photo": "alexis-davis"
  },
  {
    "badge": "CS",
    "name": "Christy Shellenberger",
    "role": "Owner &amp; VP of Sales &middot; Rock Hill Screen Printing",
    "bio": "Brings extensive hands-on experience in shop operations, customer relationships, and sales strategy. Recognized as a Women in Screen Printing honoree in 2023.",
    "years": [
      "2026"
    ],
    "photo": "christy-shellenberger"
  },
  {
    "badge": "AW",
    "name": "Anna Wardenburg",
    "role": "Events Specialist &middot; Iowa Donor Network",
    "bio": "Leads planning and execution of signature events honoring donors and celebrating the gift of life, including the Rose Parade and Team Iowa programs. Also oversees the Iowa Donor Network apparel store.",
    "years": [
      "2026"
    ],
    "photo": "anna-wardenburg"
  },
  {
    "badge": "AH",
    "name": "Ali Hansen",
    "role": "Owner &middot; Pat Barton Dance Studio",
    "bio": "Has led Pat Barton Dance Studio for the past 10 years, bringing over 25 years of dance experience. Holds degrees in Business Management and Marketing and previously co-owned a high-performance racing motorcycle company.",
    "years": [
      "2026"
    ],
    "photo": "ali-hansen"
  },
  {
    "badge": "AB",
    "name": "Amy Benton",
    "role": "Director of Marketing &middot; MH Equipment",
    "bio": "Leads strategy across digital marketing, lead generation, events, and communications, having built teams that contributed to a 10X increase in revenue.",
    "years": [
      "2026"
    ],
    "photo": None
  },
  {
    "badge": "MB",
    "name": "Meghan Brazzelle",
    "role": "Senior Manager, Sales &amp; Operations &middot; Chipply",
    "bio": "20-year printwear industry veteran with experience across leading apparel suppliers, pairing deep product knowledge with technology and process strategy for scalable sales growth.",
    "years": [
      "2026"
    ],
    "photo": "meghan-brazzelle"
  },
  {
    "badge": "PA",
    "name": "Paul A. Gormley",
    "role": "Digital Marketing &amp; Innovation &middot; CIRAS",
    "bio": "Former electrical engineer turned innovation consultant, having worked with more than 200 companies on product development, market messaging, and internet-based marketing strategy.",
    "years": [
      "2026"
    ],
    "photo": None
  },
  {
    "badge": "JS",
    "name": "Justin Sebren",
    "role": "Co-Owner &middot; Lucid Ink",
    "bio": "Co-owner of Lucid Ink in Pearl, Mississippi, specializing in screen printing, heat pressing, and in-house DTF transfer production. Over ten years of print experience.",
    "years": [
      "2026"
    ],
    "photo": "justin-sebren"
  },
  {
    "badge": "MB",
    "name": "Mark Bailey",
    "role": "Sr Manager &middot; SanMar",
    "bio": "Began in the promotional products industry in 1985 and joined SanMar in 1998. Since 2009 has focused exclusively on supporting the decorator community, and serves on the Board of the Printing United Alliance.",
    "years": [
      "2026"
    ],
    "photo": "mark-bailey"
  },
  {
    "badge": "RS",
    "name": "Ryan Snaadt",
    "role": "Owner &middot; Snaadt Media Group",
    "bio": "Owner of a Central Iowa business helping brands connect with their audience via video, podcasts, and content marketing, with a podcast reaching 1.5M+ views and a 94,000+ member Facebook group.",
    "years": [
      "2026"
    ],
    "photo": "ryan-snaadt"
  },
  {
    "badge": "CC",
    "name": "Chris Clark",
    "role": "Territory Manager &middot; SanMar",
    "bio": "Supports decorators and distributors across Nebraska and Iowa, working closely with shop owners to navigate product selection, operational challenges, and growth opportunities.",
    "years": [
      "2026"
    ],
    "photo": "chris-clark"
  },
  {
    "badge": "MR",
    "name": "Matt Richardson",
    "role": "Co-Owner &middot; Atonal Headwear / Relentless Merchandising",
    "bio": "Co-Owner of Atonal Headwear and VP of Operations at Relentless Merchandising, with over a decade of experience in operations, product development, and building scalable systems.",
    "years": [
      "2026"
    ],
    "photo": "matt-richardson"
  },
  {
    "badge": "NR",
    "name": "Nathan Richardson",
    "role": "Owner &middot; Atonal Headwear / Relentless Merchandising",
    "bio": "Owner of Atonal Headwear and Co-Founder of Relentless Merchandising, focused on business development, brand strategy, and long-term growth.",
    "years": [
      "2026"
    ],
    "photo": "nathan-richardson"
  },
  {
    "badge": "SC",
    "name": "Spencer Chernoff",
    "role": "Founder &amp; CEO &middot; Limitless Transfers",
    "bio": "Founder of Limitless Transfers, back-to-back Best DTF award winner in 2024. Educator and content creator known for breaking down complex concepts into practical, shop-ready insights.",
    "years": [
      "2026"
    ],
    "photo": "spencer-chernoff"
  },
  {
    "badge": "AE",
    "name": "Ashleigh &amp; Elena Leon",
    "role": "Owners &middot; The Side Garage",
    "bio": "Own The Side Garage, a screen print and design shop in West Des Moines, IA, founded in 2016. Ashleigh leads creative and design; Elena leads production and on-site events.",
    "years": [
      "2026"
    ],
    "photo": "ashleigh-elena-leon"
  },
  {
    "badge": "RC",
    "name": "Russ Corey",
    "role": "Strategic Account Manager &middot; SanMar",
    "bio": "Strategic Account Manager on SanMar's Decorator Solutions Team, based in Michigan and covering the Midwest, with over 30 years of experience in heat application decoration.",
    "years": [
      "2026"
    ],
    "photo": "russ-corey"
  }
]

PAGES = {
  "index": {
    "title": "Flyover Con — The Midwest's Conference for Screen Printers &amp; Decorators",
    "desc": "Flyover Con is a hands-on conference for Midwest screen printers and decorators, hosted by P&amp;M Apparel in Polk City, Iowa. See the FOC26 recap and get notified about what's next.",
    "canon": "https://www.flyovercon.ink/",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Event\", \"name\": \"Flyover Con 2026\", \"startDate\": \"2026-04-17\", \"endDate\": \"2026-04-18\", \"eventAttendanceMode\": \"https://schema.org/OfflineEventAttendanceMode\", \"eventStatus\": \"https://schema.org/EventScheduled\", \"location\": {\"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}}, \"description\": \"The second year of Flyover Con, a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility in Polk City, Iowa.\", \"organizer\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}, \"performer\": [{\"@type\": \"Person\", \"name\": \"Ryan Toney\"}, {\"@type\": \"Person\", \"name\": \"Megan Griffith\"}, {\"@type\": \"Person\", \"name\": \"Amanda Clark\"}, {\"@type\": \"Person\", \"name\": \"Alexis Davis\"}, {\"@type\": \"Person\", \"name\": \"Christy Shellenberger\"}, {\"@type\": \"Person\", \"name\": \"Anna Wardenburg\"}, {\"@type\": \"Person\", \"name\": \"Ali Hansen\"}, {\"@type\": \"Person\", \"name\": \"Amy Benton\"}, {\"@type\": \"Person\", \"name\": \"Meghan Brazzelle\"}, {\"@type\": \"Person\", \"name\": \"Paul A. Gormley\"}, {\"@type\": \"Person\", \"name\": \"Justin Sebren\"}, {\"@type\": \"Person\", \"name\": \"Mark Bailey\"}, {\"@type\": \"Person\", \"name\": \"Ryan Snaadt\"}, {\"@type\": \"Person\", \"name\": \"Chris Clark\"}, {\"@type\": \"Person\", \"name\": \"Matt Richardson\"}, {\"@type\": \"Person\", \"name\": \"Nathan Richardson\"}, {\"@type\": \"Person\", \"name\": \"Spencer Chernoff\"}, {\"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\"}, {\"@type\": \"Person\", \"name\": \"Russ Corey\"}]}]"
    ],
    "main": "\n\n<section class=\"hero\">\n  <div class=\"container hero__inner\">\n    <img class=\"hero__logo\" src=\"assets/img/logo-full.png\" alt=\"Flyover Con 2026 logo\" width=\"260\" height=\"322\">\n    <div class=\"hero__eyebrow\">Status Board &mdash; Polk City, Iowa</div>\n    <h1>The Midwest's conference<br>for people who <span class=\"accent\">actually print.</span></h1>\n    <p class=\"hero__lead\">The Midwest's conference for screen printers and decorators. Hosted inside a working screen print and embroidery shop by P&M Apparel &mdash; no vendor booths, no sales pitches, just the shop floor and the people running it.</p>\n    <div class=\"plaque\" style=\"margin-bottom:28px;\">\n      <p class=\"plaque__text\">Next Departure: TBD &mdash; FOC26 has wrapped</p>\n    </div>\n    <div class=\"hero__actions\">\n      <a class=\"btn btn--gold\" href=\"years-past.html\">See the FOC26 Recap</a>\n      <a class=\"btn btn--outline\" href=\"location.html#updates\">Get Notified for Next Year</a>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">What It Is</span>\n      <h2>Not a trade show. A working shop floor.</h2>\n      <p>Flyover Con is a hands-on conference for screen printers and decorators who want practical learning, real conversations, and a stronger sense of community &mdash; built and hosted by P&amp;M Apparel, right inside their own production facility.</p>\n    </div>\n    <div class=\"stat-strip\">\n      <div class=\"stat\"><span class=\"stat__num\">2</span><span class=\"stat__label\">Years Running</span></div>\n<div class=\"stat\"><span class=\"stat__num\">16</span><span class=\"stat__label\">Sessions at FOC26</span></div>\n<div class=\"stat\"><span class=\"stat__num\">19</span><span class=\"stat__label\">Speakers &amp; Panelists</span></div>\n<div class=\"stat\"><span class=\"stat__num\">2</span><span class=\"stat__label\">Days on the Shop Floor</span></div>\n    </div>\n  </div>\n</section>\n\n<section class=\"section--navy\">\n  <div class=\"container block-grid\">\n    <div class=\"block block--gold\" style=\"grid-column:span 7;\">\n      <span class=\"section-head__eyebrow\" style=\"color:var(--navy-deep);opacity:0.7;\">Why Attend</span>\n      <h3>Practical, Implementable Learning</h3>\n      <p>Sessions on sales, webstores, automation, DTF, multi-decoration workflows, and shop systems. Walk away with at least one idea you can put to work back home.</p>\n    </div>\n    <div class=\"block block--sky\" style=\"grid-column:span 5;\">\n      <h3>Hands-On, Not On A Stage</h3>\n      <p>It happens in the middle of production &mdash; equipment running, workflows in motion, real shop examples the whole time.</p>\n    </div>\n    <div class=\"block block--outline\" style=\"grid-column:span 5;background:transparent;border-color:rgba(255,255,255,0.3);color:#fff;\">\n      <h3>Real Conversations</h3>\n      <p>Speakers are around all event &mdash; coffee, lunch, happy hour, downtime &mdash; not hidden backstage.</p>\n    </div>\n    <div class=\"block block--white\" style=\"grid-column:span 7;\">\n      <h3>Community Over Competition</h3>\n      <p>Flyover Con exists to build a network of decorators who can lean on each other &mdash; relationships that outlast the event itself.</p>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">FOC26 Was Made Possible By</span>\n      <h2>Thank you to our sponsors</h2>\n    </div>\n    <div class=\"sponsor-strip\">\n      <span class=\"sponsor-chip\">SanMar</span>\n<span class=\"sponsor-chip\">Limitless Transfers</span>\n<span class=\"sponsor-chip\">PrintGrip</span>\n<span class=\"sponsor-chip\">Chipply</span>\n<span class=\"sponsor-chip\">S&amp;S Activewear</span>\n<span class=\"sponsor-chip\">SPSI</span>\n<span class=\"sponsor-chip\">Embellishr</span>\n<span class=\"sponsor-chip\">Atonal Headwear</span>\n    </div>\n    <p style=\"margin-top:24px;color:var(--grey);\">Interested in sponsoring the next Flyover Con? Reach out at <a href=\"mailto:ryan@flyovercon.ink\" style=\"color:var(--navy);font-weight:600;\">ryan@flyovercon.ink</a>.</p>\n  </div>\n</section>\n\n"
  },
  "about": {
    "title": "About Flyover Con — A Hands-On Conference for Decorators",
    "desc": "Flyover Con is a hands-on conference for screen printers and decorators, hosted inside a working Iowa print shop. No vendor booths, no sales pitches — just real shop-floor learning.",
    "canon": "https://www.flyovercon.ink/about.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"About\", \"item\": \"https://www.flyovercon.ink/about.html\"}]}]"
    ],
    "main": "\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">About</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">What is Flyover Con?</h1>\n  </div>\n</section>\n\n<section>\n  <div class=\"container two-col\">\n    <div class=\"prose\">\n      <p>Flyover Con is a hands-on conference built for screen printers and decorators who want practical learning, real conversations, and a stronger sense of community.</p>\n      <p>Hosted inside a working print and embroidery shop in Polk City, Iowa, Flyover Con brings together shop owners, managers, and decorators to learn from people who are actively doing the work every day. Sessions focus on real-world challenges and solutions &mdash; what actually works on the shop floor and in the office.</p>\n      <p>Flyover Con is intentionally different from traditional industry events. There are no vendor booths and no sales-driven presentations. Instead, the event is built around education, transparency, and connection. Attendees are encouraged to ask questions, walk the production floor, and engage directly with speakers and fellow decorators.</p>\n      <p>The name reflects a belief that great work is happening everywhere, not just in major markets. The Midwest is full of skilled, hardworking shops doing innovative things, and Flyover Con exists to highlight that work while welcoming decorators from across the country.</p>\n    </div>\n    <div class=\"plaque\" style=\"width:100%;\">\n      <p class=\"plaque__text\" style=\"font-size:0.95rem;line-height:1.6;\">\"The term &lsquo;flyover&rsquo; often describes the Midwest as something to be passed over. For us, it represents the opposite.\"</p>\n    </div>\n  </div>\n</section>\n\n<section class=\"section--navy\">\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">Why Attend</span>\n      <h2>Five reasons decorators keep coming back</h2>\n    </div>\n    <div class=\"card-grid\">\n      <div class=\"card\" style=\"background:var(--navy-deep);border-color:rgba(255,255,255,0.15);\">\n        <h3 style=\"color:#fff;\">Practical, Implementable Learning</h3>\n        <p style=\"color:rgba(255,255,255,0.7);\">Sessions on sales, webstores, automation, DTF accuracy, multi-decoration workflows, and shop systems. The goal: walk away with at least one idea you can implement.</p>\n      </div>\n      <div class=\"card\" style=\"background:var(--navy-deep);border-color:rgba(255,255,255,0.15);\">\n        <h3 style=\"color:#fff;\">Hands-On Experience</h3>\n        <p style=\"color:rgba(255,255,255,0.7);\">The event happens in the middle of production, not on a stage. See equipment running, workflows in action, real examples of day-to-day shop operations.</p>\n      </div>\n      <div class=\"card\" style=\"background:var(--navy-deep);border-color:rgba(255,255,255,0.15);\">\n        <h3 style=\"color:#fff;\">Real Conversations</h3>\n        <p style=\"color:rgba(255,255,255,0.7);\">Speakers are available throughout &mdash; over coffee, lunch, happy hour, downtime &mdash; creating space for honest discussion and shared problem-solving.</p>\n      </div>\n      <div class=\"card\" style=\"background:var(--navy-deep);border-color:rgba(255,255,255,0.15);\">\n        <h3 style=\"color:#fff;\">Community Over Competition</h3>\n        <p style=\"color:rgba(255,255,255,0.7);\">Built around a network of people you can lean on. Attendees leave with connections and relationships that extend beyond the event.</p>\n      </div>\n      <div class=\"card\" style=\"background:var(--navy-deep);border-color:rgba(255,255,255,0.15);\">\n        <h3 style=\"color:#fff;\">An Accessible Experience</h3>\n        <p style=\"color:rgba(255,255,255,0.7);\">Designed to be affordable and approachable &mdash; high-quality education without the pressure or scale of massive trade shows.</p>\n      </div>\n    </div>\n  </div>\n</section>\n\n"
  },
  "years-past": {
    "title": "Years Past — Flyover Con Schedule Archive",
    "desc": "The full session schedule from every Flyover Con, including FOC26: 16 sessions across two days on the P&amp;M Apparel shop floor in Polk City, Iowa.",
    "canon": "https://www.flyovercon.ink/years-past.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Years Past\", \"item\": \"https://www.flyovercon.ink/years-past.html\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Event\", \"name\": \"Flyover Con 2026\", \"startDate\": \"2026-04-17\", \"endDate\": \"2026-04-18\", \"eventAttendanceMode\": \"https://schema.org/OfflineEventAttendanceMode\", \"eventStatus\": \"https://schema.org/EventScheduled\", \"location\": {\"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}}, \"description\": \"The second year of Flyover Con, a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility in Polk City, Iowa.\", \"organizer\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}, \"performer\": [{\"@type\": \"Person\", \"name\": \"Ryan Toney\"}, {\"@type\": \"Person\", \"name\": \"Megan Griffith\"}, {\"@type\": \"Person\", \"name\": \"Amanda Clark\"}, {\"@type\": \"Person\", \"name\": \"Alexis Davis\"}, {\"@type\": \"Person\", \"name\": \"Christy Shellenberger\"}, {\"@type\": \"Person\", \"name\": \"Anna Wardenburg\"}, {\"@type\": \"Person\", \"name\": \"Ali Hansen\"}, {\"@type\": \"Person\", \"name\": \"Amy Benton\"}, {\"@type\": \"Person\", \"name\": \"Meghan Brazzelle\"}, {\"@type\": \"Person\", \"name\": \"Paul A. Gormley\"}, {\"@type\": \"Person\", \"name\": \"Justin Sebren\"}, {\"@type\": \"Person\", \"name\": \"Mark Bailey\"}, {\"@type\": \"Person\", \"name\": \"Ryan Snaadt\"}, {\"@type\": \"Person\", \"name\": \"Chris Clark\"}, {\"@type\": \"Person\", \"name\": \"Matt Richardson\"}, {\"@type\": \"Person\", \"name\": \"Nathan Richardson\"}, {\"@type\": \"Person\", \"name\": \"Spencer Chernoff\"}, {\"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\"}, {\"@type\": \"Person\", \"name\": \"Russ Corey\"}]}]"
    ],
    "main": "\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">Archive</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Years Past</h1>\n    <p class=\"hero__lead\">Every Flyover Con schedule, one flight at a time. For most time blocks, two sessions run at once &mdash; one in Gate A, one in Gate B &mdash; so you could always build a day that fit what you wanted to learn.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"year-tabs\" role=\"tablist\" aria-label=\"Flyover Con years\">\n      <button class=\"year-tab\" data-year=\"2026\" aria-selected=\"true\">FOC26</button>\n      <button class=\"year-tab\" data-year=\"2024\">FOC24</button>\n    </div>\n    <div class=\"year-panel is-active\" data-year=\"2026\">\n      <div class=\"plaque\" style=\"margin-bottom:32px;\">\n        <p class=\"plaque__text\">FOC26 &mdash; April 17\u201318, 2026</p>\n      </div>\n      <p class=\"prose\" style=\"color:var(--grey);max-width:65ch;margin-bottom:40px;\">Flyover Con's second year, and the first with a full two-track schedule.</p>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 1 &mdash; April 17, 2026</h3>\n      <div class=\"slot\">\n        <span class=\"slot__time\">8:00 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4>\n          <p class=\"session__desc\">Doors open. Grab coffee, get checked in, and watch the shop come alive before the first session.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">9:00 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Finding Your Profit Centers</h4>\n        <p class=\"session__speaker\">Christy Shellenberger \u2014 Rock Hill Screen Printing</p>\n        <p class=\"session__desc\">Revenue is fun. Profit is what keeps the lights on. A real shop case study breaking down where the money is actually made, where it's lost, and the decisions that move the needle \u2014 pricing, products, labor, and the difference between being busy and being profitable.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">From the Other Side of the Order</h4>\n        <p class=\"session__speaker\">Megan Griffith (Moderator) \u2014 P&amp;M Apparel, with Anna Wardenburg, Ali Hansen, Amy Benton</p>\n        <p class=\"session__desc\">Real customers on what makes them choose a shop, what keeps them coming back, and what creates frustration along the way \u2014 a moderated conversation on serving, communicating with, and retaining clients.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">10:30 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Building Webstores That Sell</h4>\n        <p class=\"session__speaker\">Meghan Brazzelle \u2014 Chipply</p>\n        <p class=\"session__desc\">How successful shops use webstores to simplify ordering and unlock scalable sales serving teams, schools, and organizations more efficiently.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">AI for Streamlining Business</h4>\n        <p class=\"session__speaker\">Paul Gormley \u2014 CIRAS</p>\n        <p class=\"session__desc\">AI is more than a design tool. How decorators can use it to streamline everyday operations \u2014 marketing, analytics, communication, and decision-making.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">11:45 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Lunch // Provided by PrintGrip</h4>\n          <p class=\"session__desc\">A break to eat, regroup, and keep the shop-floor conversations going.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">1:00 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Making Better Decisions With Data</h4>\n        <p class=\"session__speaker\">Amanda Clark \u2014 P&amp;M Apparel</p>\n        <p class=\"session__desc\">Your business generates more data than you think. How to turn everyday information into actionable insights that improve operations, guide strategy, and drive results.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Serving Your Community</h4>\n        <p class=\"session__speaker\">Justin Sebren \u2014 Lucid Ink</p>\n        <p class=\"session__desc\">Strong community relationships can be one of a shop's greatest advantages. Building local trust, supporting organizations, and turning involvement into lasting growth.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">2:15 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Resources for Decorators</h4>\n        <p class=\"session__speaker\">Mark Bailey \u2014 SanMar</p>\n        <p class=\"session__desc\">Tools, organizations, and industry resources decorators can lean on to improve operations, stay informed, and keep learning.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Relentless Determination</h4>\n        <p class=\"session__speaker\">Matt and Nate Richardson \u2014 Relentless Merchandise</p>\n        <p class=\"session__desc\">The real story behind Relentless Merch's growth \u2014 the obstacles, the mistakes, the risk, and what it actually takes to build something and keep pushing when things get hard.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">3:45 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Why Customers Choose You (And Not the Cheaper Guy)</h4>\n        <p class=\"session__speaker\">Ryan Toney (Moderator) \u2014 P&amp;M Apparel, with Christy Shellenberger, Justin Sebren, Chris Clark</p>\n        <p class=\"session__desc\">A panel on customer experience, professionalism, communication, and the real reasons customers choose one shop over another.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Not All Work Is Good Work (When to Say No)</h4>\n        <p class=\"session__speaker\">Megan Griffith (Moderator) \u2014 P&amp;M Apparel, with Matt and Nate Richardson, Spencer Chernoff</p>\n        <p class=\"session__desc\">Not every order, customer, or opportunity is worth taking. Learning when to say no is often where profitability actually comes from.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">5:00 PM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Happy Hour // Presented by SanMar</h4>\n          <p class=\"session__desc\">Drinks, snacks, and a live band to close out day one.</p>\n        </div></div>\n      </div>\n    </div>\n<div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 2 &mdash; April 18, 2026</h3>\n      <div class=\"slot\">\n        <span class=\"slot__time\">8:00 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4>\n          <p class=\"session__desc\">Doors open for day two, same as day one \u2014 coffee, check-in, and the shop already running.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">9:00 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Mastering DTF: From First Print to Profitable Growth</h4>\n        <p class=\"session__speaker\">Spencer Chernoff \u2014 Limitless Transfers</p>\n        <p class=\"session__desc\">The full DTF journey \u2014 from understanding the technology to running it as a profitable part of the business, with practical tips on artwork, quality control, and avoiding common pitfalls.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">MultiMedia Design and Implementation</h4>\n        <p class=\"session__speaker\">Megan Griffith \u2014 P&amp;M Apparel</p>\n        <p class=\"session__desc\">Combining multiple decoration methods \u2014 screen print, embroidery, transfers, specialty finishes \u2014 to elevate both design and perceived value.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">10:30 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Live Decorating (Shop Wide)</h4>\n          <p class=\"session__desc\">The whole shop floor live and running \u2014 every station, every method, all at once.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">11:45 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Lunch // Provided by SanMar</h4>\n          <p class=\"session__desc\">A break to eat, regroup, and keep the shop-floor conversations going.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">1:00 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Live Activations</h4>\n        <p class=\"session__speaker\">Ashleigh &amp; Elena Leon \u2014 The Side Garage</p>\n        <p class=\"session__desc\">How shops can execute successful live printing activations that engage audiences, create memorable experiences, and build stronger brand connections.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Selling with Empathy</h4>\n        <p class=\"session__speaker\">Alexis Davis \u2014 P&amp;M Apparel</p>\n        <p class=\"session__desc\">Strong sales start with understanding the customer \u2014 how empathy, clear communication, and thoughtful guidance build trust and long-term relationships.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">2:15 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Be Bold. Be Odd. Marketing That Actually Works</h4>\n        <p class=\"session__speaker\">Ryan Snaadt \u2014 Snaadt Media Group</p>\n        <p class=\"session__desc\">Most marketing gets ignored. How to use video, content, and storytelling to get attention, build trust, and create marketing people actually pay attention to.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Selling More Than A Shirt</h4>\n        <p class=\"session__speaker\">Ryan Toney \u2014 P&amp;M Apparel</p>\n        <p class=\"session__desc\">Decorators often have a captive audience. How shops can expand beyond apparel with promotional products that increase order value and strengthen client relationships.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">3:45 PM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Decorator Round Table</h4>\n          <p class=\"session__desc\">An open forum for fellow decorators on the realities of running a shop. Bring your questions, share your experiences, learn from the room.</p>\n        </div></div>\n      </div>\n    </div>\n    </div>\n    <div class=\"year-panel\" data-year=\"2024\">\n      <div class=\"plaque\" style=\"margin-bottom:32px;\">\n        <p class=\"plaque__text\">FOC24 &mdash; April 18&ndash;20, 2024</p>\n      </div>\n      <p class=\"prose\" style=\"color:var(--grey);max-width:65ch;margin-bottom:40px;\">The first Flyover Con &mdash; an open house on the P&amp;M Apparel shop floor. One track, two days, peer-to-peer learning inside a working print shop.</p>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Thursday, April 18 &mdash; VIP Dinner</h3>\n      <div class=\"slot\"><span class=\"slot__time\">Evening</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">VIP Dinner</h4><p class=\"session__desc\">An intimate dinner for invited guests, sponsors, and speakers the night before the main event.</p></div></div></div>\n      </div>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 1 &mdash; Friday, April 19, 2024</h3>\n      <div class=\"slot\"><span class=\"slot__time\">9:00 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4><p class=\"session__desc\">Doors open. Get checked in on the shop floor while the presses run.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">9:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Welcome // P&amp;M Apparel // The Goal of Flyover Con</h4><p class=\"session__speaker\">Jeremy Ray &mdash; P&amp;M Apparel &middot; Christy Shellenberger &mdash; Rock Hill Screen Printing</p><p class=\"session__desc\">Why Flyover Con exists, what makes it different, and what to expect.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">10:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Custom Headwear &amp; Cap America</h4><p class=\"session__speaker\">Randy Argotsinger &mdash; Cap America</p><p class=\"session__desc\">What decorators should know about custom headwear sourcing, decoration, and program design.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">11:45 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Women in Screen Printing</h4><p class=\"session__speaker\">Megan Griffith &mdash; P&amp;M Apparel &middot; Christy Shellenberger &mdash; Rock Hill Screen Printing &middot; Kay Ferin</p><p class=\"session__desc\">A panel conversation on navigating the print industry as women.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">12:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lunch</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">1:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">DTF Printing</h4><p class=\"session__speaker\">Adrienne Palmer &mdash; DTFPrinting.com</p><p class=\"session__desc\">The state of direct-to-film: production, equipment, and where the technology fits in a decorator&rsquo;s service mix.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">2:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Hiring &amp; Retention</h4><p class=\"session__speaker\">Megan Griffith &mdash; P&amp;M Apparel</p><p class=\"session__desc\">Finding good people and keeping them.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">3:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lean Manufacturing</h4><p class=\"session__speaker\">Steve Forbes &mdash; Iowa State University CIRAS</p><p class=\"session__desc\">How lean principles apply to a print shop floor &mdash; eliminating waste, improving throughput, building systems that scale.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">5:00 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Happy Hour // Live Print // Last Call Live Podcast</h4><p class=\"session__desc\">End of day on the shop floor. Presses running, drinks poured, podcast recording live.</p></div></div></div>\n      </div>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 2 &mdash; Saturday, April 20, 2024</h3>\n      <div class=\"slot\"><span class=\"slot__time\">9:00 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Breakfast // Welcome // Registration // Live Decorating</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">10:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Gildan Board of Decorators // Sustainability</h4><p class=\"session__speaker\">Ryan Toney &middot; Christy Shellenberger &mdash; Rock Hill Screen Printing</p><p class=\"session__desc\">Inside the Gildan Board of Decorators program and a conversation about sustainability in decorated apparel.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">11:45 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Trends in Blanks</h4><p class=\"session__speaker\">Jacob Whitman &mdash; SanMar &middot; Taylor Larson</p><p class=\"session__desc\">What&rsquo;s moving in wholesale blanks &mdash; styles, fabrics, and what your customers are actually asking for.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">12:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lunch</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">1:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Printavo</h4><p class=\"session__desc\">Shop management software &mdash; how to run a tighter operation from quote to ship.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">3:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Chipply</h4><p class=\"session__speaker\">Nick Hoffman &mdash; Chipply</p><p class=\"session__desc\">Online team stores and how to build a webstore program that works for your shop and your clients.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">5:00 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Live Decorating</h4><p class=\"session__desc\">Final session closes on the shop floor.</p></div></div></div>\n      </div>\n      <div style=\"margin-top:48px;padding-top:32px;border-top:2px solid var(--grey-light);\">\n        <h3 style=\"font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin-bottom:20px;\">Sponsors</h3>\n        <div style=\"display:flex;flex-wrap:wrap;gap:12px;\"><span class=\"tag\">Anatol</span><span class=\"tag\">Gildan</span><span class=\"tag\">Chipply</span><span class=\"tag\">First Citizens Bank</span><span class=\"tag\">SanMar</span></div>\n      </div>\n    </div>\n  </div>\n</section>\n\n"
  },
  "speakers": {
    "title": "Speakers — Flyover Con Alumni",
    "desc": "Meet the shop owners, operators, and industry partners who've spoken at Flyover Con, the Midwest's hands-on conference for screen printers and decorators.",
    "canon": "https://www.flyovercon.ink/speakers.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Speakers\", \"item\": \"https://www.flyovercon.ink/speakers.html\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ryan Toney\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Megan Griffith\", \"jobTitle\": \"Owner & Art Director\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Amanda Clark\", \"jobTitle\": \"Financials Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Alexis Davis\", \"jobTitle\": \"Account Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Christy Shellenberger\", \"jobTitle\": \"Owner & VP of Sales\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Rock Hill Screen Printing\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Anna Wardenburg\", \"jobTitle\": \"Events Specialist\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Iowa Donor Network\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ali Hansen\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Pat Barton Dance Studio\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Amy Benton\", \"jobTitle\": \"Director of Marketing\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"MH Equipment\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Meghan Brazzelle\", \"jobTitle\": \"Senior Manager, Sales & Operations\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Chipply\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Paul A. Gormley\", \"jobTitle\": \"Digital Marketing & Innovation\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"CIRAS\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Justin Sebren\", \"jobTitle\": \"Co-Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Lucid Ink\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Mark Bailey\", \"jobTitle\": \"Sr Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ryan Snaadt\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Snaadt Media Group\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Chris Clark\", \"jobTitle\": \"Territory Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Matt Richardson\", \"jobTitle\": \"Co-Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Atonal Headwear / Relentless Merchandising\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Nathan Richardson\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Atonal Headwear / Relentless Merchandising\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Spencer Chernoff\", \"jobTitle\": \"Founder & CEO\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Limitless Transfers\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\", \"jobTitle\": \"Owners\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"The Side Garage\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Russ Corey\", \"jobTitle\": \"Strategic Account Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}]"
    ],
    "main": "\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">Alumni</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Speakers</h1>\n    <p class=\"hero__lead\">The shop owners, operators, and industry partners who've stood on the Flyover Con shop floor and shared what actually works.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    __SPEAKER_GRID__\n    </div>\n</section>\n"
  },
  "location": {
    "title": "Location — Flyover Con at P&amp;M Apparel, Polk City, Iowa",
    "desc": "Flyover Con is hosted inside P&amp;M Apparel's 8,000 sq ft production facility in Polk City, Iowa, about 30 minutes from Des Moines. Directions, parking, and nearby hotels.",
    "canon": "https://www.flyovercon.ink/location.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Location\", \"item\": \"https://www.flyovercon.ink/location.html\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}, \"geo\": {\"@type\": \"GeoCoordinates\", \"latitude\": 41.763743, \"longitude\": -93.719835}}]"
    ],
    "main": "\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">The Venue</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">P&amp;M Apparel</h1>\n    <p class=\"hero__lead\">Flyover Con takes place inside P&amp;M Apparel's production facility, built in 2020 and intentionally designed to bring people, process, and production together in one open, transparent space.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container location-grid\">\n    <div>\n      <div class=\"map-embed\">\n        <iframe src=\"https://maps.google.com/maps?q=1100+S+5th+St,+Polk City,+IA+50226,+USA&z=16&output=embed\" loading=\"lazy\" title=\"Map to P&amp;M Apparel, 1100 S 5th St, Polk City, IA 50226\"></iframe>\n      </div>\n      <div class=\"prose\" style=\"margin-top:28px;\">\n        <p>With more than 8,000 square feet, the shop houses all sales, production, and fulfillment operations under one roof &mdash; multiple Anatol automatic presses, an Anatol manual press, a custom-built live screen printing press, an Anatol gas dryer, a Douthitt CTS, a Workhorse LED exposure table, ZSK and Barudan embroidery machines, Stahls Hotronix and MEM heat presses, and in-house digital and prototyping equipment. Every piece is visible, accessible, and actively used during the event.</p>\n        <p>Flyover Con doesn't happen on a stage or inside a conference hall &mdash; it's embedded directly into the shop floor. Attendees walk the same paths as the production team, stand next to presses, and watch garments move through the process end to end.</p>\n        <p>Hosting it in our own space is intentional. It reflects a commitment to transparency and a willingness to open the doors fully, even to potential competitors &mdash; sharing real systems, real decisions, and real lessons learned.</p>\n      </div>\n    </div>\n    <aside>\n      <div class=\"plaque\" style=\"width:100%;margin-bottom:24px;\">\n        <p class=\"plaque__text\" style=\"font-size:0.95rem;\">1100 S 5th St, Polk City, IA 50226</p>\n      </div>\n      <h3 style=\"font-size:1.1rem;\">Getting Here</h3>\n      <div class=\"getting-here\">\n        <div class=\"getting-here__item\">\n          <div class=\"getting-here__icon\">✈</div>\n          <div><strong>By Plane</strong><p style=\"color:var(--grey);margin:2px 0 0;\">Des Moines International Airport (DSM) &mdash; nonstop flights from many major U.S. cities, about a 30-minute drive to Polk City.</p></div>\n        </div>\n        <div class=\"getting-here__item\">\n          <div class=\"getting-here__icon\">→</div>\n          <div><strong>By Car</strong><p style=\"color:var(--grey);margin:2px 0 0;\">About 10 miles west of I-35, accessible via Highway 415 &mdash; an easy drive from Des Moines and the surrounding metro.</p></div>\n        </div>\n      </div>\n      <h3 style=\"font-size:1.1rem;margin-top:32px;\">Need Somewhere to Stay?</h3>\n      <div class=\"hotel\"><h4>Qube Hotel</h4><p>1.3 miles from venue</p><p>300 Boulder Pointe, Polk City, IA 50226</p><p>(515) 984-3092</p></div>\n<div class=\"hotel\"><h4>Tru by Hilton Grimes Des Moines</h4><p>7 miles from venue</p><p>701 NE Gateway Dr, Grimes, IA 50111</p><p>(515) 608-8784</p></div>\n    </aside>\n  </div>\n</section>\n\n<section id=\"updates\" class=\"section--navy\">\n  <div class=\"container\">\n    <div class=\"block-grid\">\n      <div class=\"block block--gold\" style=\"grid-column:1 / -1;text-align:left;\">\n        <span class=\"section-head__eyebrow\" style=\"color:var(--navy-deep);opacity:0.7;\">Status: Next Departure TBD</span>\n        <h2 style=\"color:var(--navy-deep);\">Want to know when FOC27 lands?</h2>\n        <p style=\"max-width:60ch;\">Nothing's booked yet &mdash; but when it is, this is the fastest way to hear about it first. Email us or follow along on Instagram and Facebook.</p>\n        <div style=\"display:flex;gap:16px;flex-wrap:wrap;margin-top:20px;\">\n          <a class=\"btn btn--outline-navy\" href=\"mailto:ryan@flyovercon.ink\">Email ryan@flyovercon.ink</a>\n          <a class=\"btn btn--outline-navy\" href=\"https://www.instagram.com/flyover_con/\" rel=\"noopener\" target=\"_blank\">Follow on Instagram</a>\n        </div>\n      </div>\n    </div>\n  </div>\n</section>\n\n"
  }
}

# ---------------------------------------------------------------- rendering
def head(page, key):
    t, d, canon = page["title"], page["desc"], page["canon"]
    schema = "\n".join('<script type="application/ld+json">%s</script>' % b for b in page["schema"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index, follow">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="assets/img/favicon-192.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}/assets/img/logo-512.png">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
{schema}
</head>
<body>
"""

def nav(key):
    items = ""
    for href, label in NAV:
        cur = ' aria-current="page"' if href == key + ".html" else ""
        items += f'          <li><a href="{href}"{cur}>{label}</a></li>\n'
    return f"""
<header class="site-nav">
  <div class="site-nav__inner">
    <a class="site-nav__logo" href="index.html">
      <img src="assets/img/logo-compact.png" alt="Flyover Con logo" width="48" height="45">
      <span>Flyover Con</span>
    </a>
    <button class="site-nav__toggle" aria-expanded="false" aria-label="Toggle navigation menu">Menu</button>
    <ul class="site-nav__links">
{items}      <li><a class="site-nav__cta" href="location.html#updates">Stay In The Loop</a></li>
    </ul>
  </div>
</header>

<main>
"""

def footer():
    return f"""</main>

<footer class="site-footer">
  <div class="container">
    <div class="site-footer__top">
      <div class="site-footer__logo">
        <img src="assets/img/logo-compact.png" alt="Flyover Con logo" width="120" height="113">
        <p class="site-footer__tagline">{TAGLINE}</p>
        <div class="social-links" style="margin-top:14px;">
          <a href="{IG}" aria-label="Flyover Con on Instagram" rel="noopener" target="_blank">IG</a>
          <a href="{FB}" aria-label="Flyover Con on Facebook" rel="noopener" target="_blank">FB</a>
        </div>
      </div>
      <nav class="site-footer__nav">
        <div class="site-footer__col">
          <h5>Explore</h5>
          <ul>
            <li><a href="about.html">About Flyover Con</a></li>
            <li><a href="years-past.html">Years Past</a></li>
            <li><a href="speakers.html">Speakers</a></li>
            <li><a href="location.html">Location</a></li>
          </ul>
        </div>
        <div class="site-footer__col">
          <h5>Presented By</h5>
          <ul>
            <li><a href="{PARENT_URL}" rel="noopener" target="_blank">{PARENT_NAME}</a></li>
            <li>{PARENT_ADDR}</li>
          </ul>
        </div>
        <div class="site-footer__col">
          <h5>Get In Touch</h5>
          <ul>
            <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          </ul>
        </div>
      </nav>
    </div>
    <div class="site-footer__bottom">
      <span>&copy; 2026 Flyover Con, presented by {PARENT_NAME}. Polk City, Iowa.</span>
      <span>Updated {UPDATED_HUMAN}</span>
    </div>
  </div>
</footer>

<script src="assets/js/main.js"></script>
</body>
</html>
"""

def speaker_grid():
    out = ['<div class="speaker-grid">']
    for s in SPEAKERS:
        if s["photo"]:
            p = s["photo"]
            alt = re.sub(r"&amp;", "and", s["name"])
            head_img = (f'<img class="speaker__photo" src="assets/img/speakers/{p}.jpg" '
                        f'srcset="assets/img/speakers/{p}.jpg 1x, assets/img/speakers/{p}@2x.jpg 2x" '
                        f'alt="{alt}" width="96" height="96" loading="lazy" decoding="async">')
        else:
            head_img = f'<div class="speaker__badge">{s["badge"]}</div>'
        tags = "".join(f'<span class="tag">{y}</span>' for y in s["years"])
        out.append(f"""      <div class="speaker">
        <div class="speaker__head">
          {head_img}
          <div>
            <p class="speaker__name">{s["name"]}</p>
            <p class="speaker__role">{s["role"]}</p>
          </div>
        </div>
        <p class="speaker__bio">{s["bio"]}</p>
        <div class="speaker__years">{tags}</div>
      </div>""")
    out.append("    </div>")
    return "\n".join(out)

def render(key):
    page = PAGES[key]
    body = page["main"].replace("__SPEAKER_GRID__", speaker_grid())
    return head(page, key) + nav(key) + body + footer()

# ---------------------------------------------------------------- side files
def sitemap():
    urls = "".join(
        f'  <url><loc>{PAGES[k]["canon"]}</loc><lastmod>{TODAY}</lastmod></url>\n'
        for k, _ in [(k, 0) for k in PAGES])
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'

def robots():
    agents = ["*", "GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "CCBot", "Applebot-Extended"]
    body = "\n\n".join(f"User-agent: {a}\nAllow: /" for a in agents)
    return f"{body}\n\nSitemap: {BASE}/sitemap.xml\n"

def llms():
    return f"""# Flyover Con

> {TAGLINE} Presented by P&M Apparel, Polk City, Iowa.

Flyover Con is a hands-on, free-to-attend conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility. No vendor booths, no sales pitches — real shop-floor learning from people who run print and embroidery shops every day.

Most recent event: FOC26, April 17-18, 2026, in Polk City, Iowa. 16 sessions across two days, 19 speakers, hosted on the P&M Apparel shop floor.

No future event is scheduled as of {UPDATED_HUMAN}.

- About: {BASE}/about.html
- Years Past (full schedule archive): {BASE}/years-past.html
- Speakers: {BASE}/speakers.html
- Location: {BASE}/location.html
- Contact: {EMAIL}
- Presented by: P&M Apparel — {PARENT_URL}
"""

VERCEL = json.dumps({"headers":[{"source":"/(.*)","has":[{"type":"host","value":".*\\.vercel\\.app"}],
        "headers":[{"key":"X-Robots-Tag","value":"noindex"}]}]}, indent=2)

# ---------------------------------------------------------------- main
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree("assets", os.path.join(OUT, "assets"))
    for key in PAGES:
        with open(os.path.join(OUT, key + ".html"), "w", encoding="utf-8") as f:
            f.write(render(key))
    for name, content in [("sitemap.xml", sitemap()), ("robots.txt", robots()),
                          ("llms.txt", llms()), ("vercel.json", VERCEL)]:
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
    n_photo = sum(1 for s in SPEAKERS if s["photo"])
    print(f"built {len(PAGES)} pages · {len(SPEAKERS)} speakers ({n_photo} with photos, "
          f"{len(SPEAKERS)-n_photo} on initials) → {OUT}/")

if __name__ == "__main__":
    main()
