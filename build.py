#!/usr/bin/env python3
"""
Flyover Con &ndash; static site generator for flyovercon.ink
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

# TODO: replace with the real Alliteration MailMe signup endpoint for the FOC list once it's live.
MAILME_URL      = "#"

NAV = [("index.html","Home"),("about.html","About"),("schedule.html","Schedule"),
       ("speakers.html","Speakers"),("location.html","Location"),("years-past.html","Years Past")]

SPEAKERS = [
  {
    "badge": "RT",
    "name": "Ryan Toney",
    "role": "Owner &middot; P&amp;M Apparel",
    "bio": "Co-owner of P&amp;M Apparel, a third-generation, family-run decorated apparel company in Iowa. Focuses on long-term strategy, systems, and sales, building scalable processes that support both clients and the internal team. Previously served on the Gildan Board of Decorators and currently serves on the Chipply Client Council.",
    "years": [
      "2024",
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
      "2024",
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
      "2024",
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
    "photo": "amy-benton"
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
    "photo": "paul-gormley"
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
  },
  {
    "badge": "JR",
    "name": "Jeremy Ray",
    "role": "Rock Hill Screen Printing",
    "bio": "Co-host of the first Flyover Con and a leader in the screen printing community, Jeremy brought Flyover Con to life alongside Christy Shellenberger.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "RA",
    "name": "Randy Argotsinger",
    "role": "Cap America",
    "bio": "Randy presented on custom headwear &ndash; sourcing, decoration options, and building headwear programs that work for decorators and their clients.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "KF",
    "name": "Kay Ferin",
    "role": "Screen Printer",
    "bio": "Kay joined Megan Griffith and Christy Shellenberger for the Women in Screen Printing panel at FOC24.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "AP",
    "name": "Adrienne Palmer",
    "role": "DTFPrinting.com",
    "bio": "Adrienne covered the state of direct-to-film printing &ndash; equipment, production workflow, and where DTF fits in a full-service decorator's mix.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "SF",
    "name": "Steve Forbes",
    "role": "Iowa State University CIRAS",
    "bio": "Steve brought lean manufacturing principles to the print shop floor &ndash; eliminating waste, improving throughput, and building scalable systems.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "GS",
    "name": "Grace Schettler",
    "role": "Chipply",
    "bio": "Grace presented on online team stores and how to build a webstore program that creates consistent, scalable revenue for your shop.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "JW",
    "name": "Jacob Whitman",
    "role": "P&amp;M Apparel",
    "bio": "Jacob covered trends in wholesale blanks &ndash; what's moving, what customers are asking for, and how decorators should be thinking about their blank selections.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "TL",
    "name": "Taylor Larson",
    "role": "Authentic Brands",
    "bio": "Taylor joined Jacob Whitman for the Trends in Blanks session, bringing a distributor perspective on where the blank market is heading.",
    "years": [
      "2024"
    ],
    "photo": None
  }
]

PAGES = {
  "index": {
    "title": "Flyover Con | Midwest Screen Printing Conference",
    "desc": "A hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working shop floor in Polk City, Iowa. Modest registration fee.",
    "canon": "https://www.flyovercon.ink/",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Event\", \"name\": \"Flyover Con 2026\", \"startDate\": \"2026-04-17\", \"endDate\": \"2026-04-18\", \"eventAttendanceMode\": \"https://schema.org/OfflineEventAttendanceMode\", \"eventStatus\": \"https://schema.org/EventScheduled\", \"location\": {\"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}}, \"description\": \"The second year of Flyover Con, a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility in Polk City, Iowa.\", \"organizer\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}, \"performer\": [{\"@type\": \"Person\", \"name\": \"Ryan Toney\"}, {\"@type\": \"Person\", \"name\": \"Megan Griffith\"}, {\"@type\": \"Person\", \"name\": \"Amanda Clark\"}, {\"@type\": \"Person\", \"name\": \"Alexis Davis\"}, {\"@type\": \"Person\", \"name\": \"Christy Shellenberger\"}, {\"@type\": \"Person\", \"name\": \"Anna Wardenburg\"}, {\"@type\": \"Person\", \"name\": \"Ali Hansen\"}, {\"@type\": \"Person\", \"name\": \"Amy Benton\"}, {\"@type\": \"Person\", \"name\": \"Meghan Brazzelle\"}, {\"@type\": \"Person\", \"name\": \"Paul A. Gormley\"}, {\"@type\": \"Person\", \"name\": \"Justin Sebren\"}, {\"@type\": \"Person\", \"name\": \"Mark Bailey\"}, {\"@type\": \"Person\", \"name\": \"Ryan Snaadt\"}, {\"@type\": \"Person\", \"name\": \"Chris Clark\"}, {\"@type\": \"Person\", \"name\": \"Matt Richardson\"}, {\"@type\": \"Person\", \"name\": \"Nathan Richardson\"}, {\"@type\": \"Person\", \"name\": \"Spencer Chernoff\"}, {\"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\"}, {\"@type\": \"Person\", \"name\": \"Russ Corey\"}]}]"
    ],
    "main": f"\n\n<section class=\"hero\">\n  <div class=\"container hero__inner\">\n    <img class=\"hero__logo\" src=\"assets/img/logo-compact.png\" alt=\"Flyover Con logo\" width=\"260\" height=\"245\">\n    <div class=\"hero__eyebrow\">Status Board &ndash; Polk&nbsp;City,&nbsp;Iowa</div>\n    <h1>The Midwest's conference<br>for people who <span class=\"accent\">make things.</span></h1>\n    <p class=\"hero__lead\">The Midwest's conference for screen printers and decorators. Hosted inside a working screen print and embroidery shop by P&M Apparel &ndash; no vendor booths, no sales pitches, just the shop floor and the people running it.</p>\n    <div class=\"hero__actions\">\n      <a class=\"btn btn--gold\" href=\"{MAILME_URL}\">Get Notified for FOC27</a>\n      <a class=\"btn btn--outline\" href=\"https://www.youtube.com/watch?v=q7Qx18jLp_o\" rel=\"noopener\" target=\"_blank\">See the FOC26 Recap</a>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">What It Is</span>\n      <h2>Not a trade show. A working shop floor.</h2>\n      <p>Flyover Con is a hands-on conference for screen printers, embroiderers, and decorators who want practical learning, real conversations, and a stronger sense of community &ndash; built and hosted by P&amp;M Apparel, right inside their own working screen print and embroidery facility.</p>\n    </div>\n    <div class=\"stat-strip\">\n      <div class=\"stat\"><span class=\"stat__num\">2</span><span class=\"stat__label\">Years Running</span></div>\n<div class=\"stat\"><span class=\"stat__num\">16</span><span class=\"stat__label\">Sessions at FOC26</span></div>\n<div class=\"stat\"><span class=\"stat__num\">19</span><span class=\"stat__label\">Speakers &amp; Panelists</span></div>\n<div class=\"stat\"><span class=\"stat__num\">2</span><span class=\"stat__label\">Days on the Shop Floor</span></div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">From The Floor</span>\n      <h2>What people actually said.</h2>\n    </div>\n    <div class=\"testimonial-strip\">\n      <div class=\"testimonial\">\n        <p class=\"testimonial__quote\">This was the first time we&rsquo;ve left a show and didn&rsquo;t say &ldquo;I wish they would&rsquo;ve talked about this or that.&rdquo;</p>\n        <div class=\"testimonial__source\">\n          <p class=\"testimonial__name\">Darci</p>\n          <p class=\"testimonial__shop\">Spot On Printing</p>\n        </div>\n      </div>\n      <div class=\"testimonial\">\n        <p class=\"testimonial__quote\">The friendly faces and no-gatekeeping mentality. It was so refreshing.</p>\n        <div class=\"testimonial__source\">\n          <p class=\"testimonial__name\">Emily</p>\n          <p class=\"testimonial__shop\">Sparkling Image</p>\n        </div>\n      </div>\n      <div class=\"testimonial\">\n        <p class=\"testimonial__quote\">Try to keep me away. I dare you.</p>\n        <div class=\"testimonial__source\">\n          <p class=\"testimonial__name\">Peter</p>\n          <p class=\"testimonial__shop\">A&amp;P Graphics</p>\n        </div>\n      </div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">From FOC26</span>\n      <h2>Scenes from the shop floor.</h2>\n    </div>\n    <div class=\"photo-strip\">\n      <img src=\"assets/img/event/foc26-007.jpg\" alt=\"Flyover Con VIP Lounge refreshment station\" loading=\"lazy\" width=\"400\" height=\"220\">\n      <img src=\"assets/img/event/foc26-006.jpg\" alt=\"Attendees talking between sessions at Flyover Con\" loading=\"lazy\" width=\"400\" height=\"220\">\n      <img src=\"assets/img/event/foc26-002.jpg\" alt=\"A speaker presenting to the room at Flyover Con\" loading=\"lazy\" width=\"400\" height=\"220\">\n      <img src=\"assets/img/event/foc26-009.jpg\" alt=\"A speaker presenting near the Gate B sign at Flyover Con\" loading=\"lazy\" width=\"400\" height=\"220\">\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">FOC27</span>\n      <h2>Sponsorship is open.</h2>\n      <p>No sponsors locked in yet for FOC27 &ndash; the floor's wide open. FOC26 was made possible by SanMar, Limitless Transfers, PrintGrip, Chipply, S&amp;S Activewear, SPSI, Embellishr, and Atonal Headwear. Want in early for 2027? Reach out at <a href=\"mailto:ryan@flyovercon.ink\" style=\"color:var(--navy);font-weight:600;\">ryan@flyovercon.ink</a>.</p>\n    </div>\n  </div>\n</section>\n\n"
  },
  "about": {
    "title": "About Flyover Con | Hands-On Decorator Conference",
    "desc": "Flyover Con is a hands-on conference for screen printers and decorators hosted inside a working Iowa print and embroidery shop. No booths, no pitches.",
    "canon": "https://www.flyovercon.ink/about.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"About\", \"item\": \"https://www.flyovercon.ink/about.html\"}]}]"
    ],
    "main": "\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">About</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">What is Flyover Con?</h1>\n  </div>\n</section>\n\n<section>\n  <div class=\"container two-col\">\n    <div class=\"prose\">\n      <p>Flyover Con is a hands-on conference built for screen printers, embroiderers, and decorators who want practical learning, real conversations, and a stronger sense of community.</p>\n      <p>Hosted inside a working print and embroidery shop in Polk City, Iowa, Flyover Con brings together shop owners, managers, and decorators to learn from people who are actively doing the work every day. Sessions focus on real-world challenges and solutions &ndash; what actually works on the shop floor and in the office.</p>\n      <p>Flyover Con is intentionally different from traditional industry events. There are no vendor booths and no sales-driven presentations. Instead, the event is built around education, transparency, and connection. Attendees are encouraged to ask questions, walk the production floor, and engage directly with speakers and fellow decorators.</p>\n      <p>The name reflects a belief that great work is happening everywhere, not just in major markets. The Midwest is full of skilled, hardworking shops doing innovative things, and Flyover Con exists to highlight that work while welcoming decorators from across the country.</p>\n    </div>\n    <div class=\"plaque\" style=\"width:100%;\">\n      <p class=\"plaque__text\" style=\"font-size:0.95rem;line-height:1.6;\">\"The term &lsquo;flyover&rsquo; often describes the Midwest as something to be passed over. For us, it represents the opposite.\"</p>\n    </div>\n  </div>\n</section>\n\n<section class=\"section--navy\">\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">Why Attend</span>\n      <h2>Why decorators keep coming back.</h2>\n    </div>\n    <div class=\"card-grid\">\n      <div class=\"reason-card\">\n        <h3>You leave with something real.</h3>\n        <p>Every session is built around practical, shop-floor challenges &ndash; pricing, webstores, workflows, hiring, data. Not theory. Things you can act on Monday morning.</p>\n        <blockquote class=\"reason-card__quote\">\n          The hands-on learning and transparency of the entire P&amp;M Apparel team.\n          <span class=\"reason-card__attr\">Lynn &ndash; House of Brands</span>\n        </blockquote>\n      </div>\n      <div class=\"reason-card\">\n        <h3>No gatekeeping. No sales pitch.</h3>\n        <p>Speakers share what actually works &ndash; including what didn&rsquo;t. There are no vendor booths, no sponsored talking points, and no one holding back the good stuff.</p>\n        <blockquote class=\"reason-card__quote\">\n          Don&rsquo;t change the vibe. Not feeling like I was being sold to was a big deal to me.\n          <span class=\"reason-card__attr\">Karen &ndash; Get GAPD</span>\n        </blockquote>\n      </div>\n      <div class=\"reason-card\">\n        <h3>It happens on a real shop floor.</h3>\n        <p>Not a convention center. Not a hotel ballroom. The presses run during sessions. You can walk the floor, ask the crew anything, and see a working shop in motion.</p>\n      </div>\n      <div class=\"reason-card\">\n        <h3>The connections are the point.</h3>\n        <p>Small enough that you actually talk to people. Speakers stick around for coffee, lunch, and happy hour. Most attendees leave with contacts they&rsquo;ll actually use.</p>\n        <blockquote class=\"reason-card__quote\">\n          You made each and every one of us feel like family.\n          <span class=\"reason-card__attr\">Angela &ndash; America&rsquo;s Best Apparel</span>\n        </blockquote>\n      </div>\n      <div class=\"reason-card\">\n        <h3>It&rsquo;s built for shops like yours.</h3>\n        <p>Small shop, large shop, one-person operation &ndash; it doesn&rsquo;t matter. Nobody here is too big to share or too small to belong. The Midwest has always worked that way.</p>\n      </div>\n    </div>\n    <div class=\"photo-pair\">\n      <img src=\"assets/img/event/foc26-001.jpg\" alt=\"Attendees examining production work on the Flyover Con shop floor\" loading=\"lazy\">\n      <img src=\"assets/img/event/foc26-008.jpg\" alt=\"An attendee taking notes during a Flyover Con session\" loading=\"lazy\">\n    </div>\n  </div>\n</section>\n\n"
  },
  "schedule": {
    "title": "Schedule | Flyover Con FOC27",
    "desc": "FOC27 schedule is coming soon. Flyover Con is the Midwest's hands-on conference for screen printers and decorators, hosted inside P&M Apparel's working shop floor in Polk City, Iowa.",
    "canon": "https://www.flyovercon.ink/schedule.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Schedule\", \"item\": \"https://www.flyovercon.ink/schedule.html\"}]}]"
    ],
    "main": f"\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">FOC27</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Schedule</h1>\n    <p class=\"hero__lead\">The FOC27 schedule hasn't been built yet. Want to see how past years ran? Check the Years Past archive.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"plaque\" style=\"margin-bottom:24px;\">\n      <p class=\"plaque__text\">Next Departure: FOC27 &ndash; Date TBD</p>\n    </div>\n    <p style=\"max-width:60ch;color:var(--grey);\">Sessions, tracks, and dates for FOC27 will land here once they're locked. <a href=\"{MAILME_URL}\" style=\"color:var(--navy);font-weight:600;\">Join the FOC27 list</a> to hear the moment it's posted.</p>\n    <p style=\"margin-top:24px;\"><a class=\"btn btn--outline\" href=\"years-past.html\">See Past Schedules</a></p>\n  </div>\n</section>\n"
  },
  "years-past": {
    "title": "Years Past | Flyover Con Schedule Archive",
    "desc": "Full session schedules from every Flyover Con. FOC26: 16 sessions, 19 speakers, two days on the P&M Apparel shop floor in Polk City, Iowa.",
    "canon": "https://www.flyovercon.ink/years-past.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Years Past\", \"item\": \"https://www.flyovercon.ink/years-past.html\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Event\", \"name\": \"Flyover Con 2026\", \"startDate\": \"2026-04-17\", \"endDate\": \"2026-04-18\", \"eventAttendanceMode\": \"https://schema.org/OfflineEventAttendanceMode\", \"eventStatus\": \"https://schema.org/EventScheduled\", \"location\": {\"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}}, \"description\": \"The second year of Flyover Con, a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility in Polk City, Iowa.\", \"organizer\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}, \"performer\": [{\"@type\": \"Person\", \"name\": \"Ryan Toney\"}, {\"@type\": \"Person\", \"name\": \"Megan Griffith\"}, {\"@type\": \"Person\", \"name\": \"Amanda Clark\"}, {\"@type\": \"Person\", \"name\": \"Alexis Davis\"}, {\"@type\": \"Person\", \"name\": \"Christy Shellenberger\"}, {\"@type\": \"Person\", \"name\": \"Anna Wardenburg\"}, {\"@type\": \"Person\", \"name\": \"Ali Hansen\"}, {\"@type\": \"Person\", \"name\": \"Amy Benton\"}, {\"@type\": \"Person\", \"name\": \"Meghan Brazzelle\"}, {\"@type\": \"Person\", \"name\": \"Paul A. Gormley\"}, {\"@type\": \"Person\", \"name\": \"Justin Sebren\"}, {\"@type\": \"Person\", \"name\": \"Mark Bailey\"}, {\"@type\": \"Person\", \"name\": \"Ryan Snaadt\"}, {\"@type\": \"Person\", \"name\": \"Chris Clark\"}, {\"@type\": \"Person\", \"name\": \"Matt Richardson\"}, {\"@type\": \"Person\", \"name\": \"Nathan Richardson\"}, {\"@type\": \"Person\", \"name\": \"Spencer Chernoff\"}, {\"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\"}, {\"@type\": \"Person\", \"name\": \"Russ Corey\"}]}]"
    ],
    "main": "\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">Archive</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Years Past</h1>\n    <p class=\"hero__lead\">Every Flyover Con schedule, one flight at a time. For most time blocks, two sessions run at once &ndash; one in Gate A, one in Gate B &ndash; so you could always build a day that fit what you wanted to learn.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <h2 style=\"font-size:1.15rem;margin-bottom:20px;color:var(--ink);\">Session Schedules</h2>\n    <div class=\"year-tabs\" role=\"tablist\" aria-label=\"Flyover Con years\">\n      <button class=\"year-tab\" data-year=\"2026\" aria-selected=\"true\">FOC26</button>\n      <button class=\"year-tab\" data-year=\"2024\">FOC24</button>\n    </div>\n    <div class=\"year-panel is-active\" data-year=\"2026\">\n      <div class=\"plaque\" style=\"margin-bottom:32px;\">\n        <p class=\"plaque__text\">FOC26 &ndash; April 17\u201318, 2026</p>\n      </div>\n      <p class=\"prose\" style=\"color:var(--grey);max-width:65ch;margin-bottom:40px;\">Flyover Con's second year, and the first with a full two-track schedule.</p>\n      <div class=\"photo-single\" style=\"margin-bottom:40px;\">\n        <img src=\"assets/img/event/foc26-004.jpg\" alt=\"A speaker presenting a session at Flyover Con 2026\" loading=\"lazy\">\n      </div>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 1 &ndash; April 17, 2026</h3>\n      <div class=\"slot\">\n        <span class=\"slot__time\">8:00 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4>\n          <p class=\"session__desc\">Doors open. Grab coffee, get checked in, and watch the shop come alive before the first session.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">9:00 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Finding Your Profit Centers</h4>\n        <p class=\"session__speaker\">Christy Shellenberger &ndash; Rock Hill Screen Printing</p>\n        <p class=\"session__desc\">Revenue is fun. Profit is what keeps the lights on. A real shop case study breaking down where the money is actually made, where it's lost, and the decisions that move the needle &ndash; pricing, products, labor, and the difference between being busy and being profitable.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">From the Other Side of the Order</h4>\n        <p class=\"session__speaker\">Megan Griffith (Moderator) &ndash; P&amp;M Apparel, with Anna Wardenburg, Ali Hansen, Amy Benton</p>\n        <p class=\"session__desc\">Real customers on what makes them choose a shop, what keeps them coming back, and what creates frustration along the way &ndash; a moderated conversation on serving, communicating with, and retaining clients.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">10:30 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Building Webstores That Sell</h4>\n        <p class=\"session__speaker\">Meghan Brazzelle &ndash; Chipply</p>\n        <p class=\"session__desc\">How successful shops use webstores to simplify ordering and unlock scalable sales serving teams, schools, and organizations more efficiently.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">AI for Streamlining Business</h4>\n        <p class=\"session__speaker\">Paul Gormley &ndash; CIRAS</p>\n        <p class=\"session__desc\">AI is more than a design tool. How decorators can use it to streamline everyday operations &ndash; marketing, analytics, communication, and decision-making.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">11:45 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Lunch // Provided by PrintGrip</h4>\n          <p class=\"session__desc\">A break to eat, regroup, and keep the shop-floor conversations going.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">1:00 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Making Better Decisions With Data</h4>\n        <p class=\"session__speaker\">Amanda Clark &ndash; P&amp;M Apparel</p>\n        <p class=\"session__desc\">Your business generates more data than you think. How to turn everyday information into actionable insights that improve operations, guide strategy, and drive results.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Serving Your Community</h4>\n        <p class=\"session__speaker\">Justin Sebren &ndash; Lucid Ink</p>\n        <p class=\"session__desc\">Strong community relationships can be one of a shop's greatest advantages. Building local trust, supporting organizations, and turning involvement into lasting growth.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">2:15 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Resources for Decorators</h4>\n        <p class=\"session__speaker\">Mark Bailey &ndash; SanMar</p>\n        <p class=\"session__desc\">Tools, organizations, and industry resources decorators can lean on to improve operations, stay informed, and keep learning.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Relentless Determination</h4>\n        <p class=\"session__speaker\">Matt and Nate Richardson &ndash; Relentless Merchandise</p>\n        <p class=\"session__desc\">The real story behind Relentless Merch's growth &ndash; the obstacles, the mistakes, the risk, and what it actually takes to build something and keep pushing when things get hard.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">3:45 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Why Customers Choose You (And Not the Cheaper Guy)</h4>\n        <p class=\"session__speaker\">Ryan Toney (Moderator) &ndash; P&amp;M Apparel, with Christy Shellenberger, Justin Sebren, Chris Clark</p>\n        <p class=\"session__desc\">A panel on customer experience, professionalism, communication, and the real reasons customers choose one shop over another.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Not All Work Is Good Work (When to Say No)</h4>\n        <p class=\"session__speaker\">Megan Griffith (Moderator) &ndash; P&amp;M Apparel, with Matt and Nate Richardson, Spencer Chernoff</p>\n        <p class=\"session__desc\">Not every order, customer, or opportunity is worth taking. Learning when to say no is often where profitability actually comes from.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">5:00 PM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Happy Hour // Presented by SanMar</h4>\n          <p class=\"session__desc\">Drinks, snacks, and a live band to close out day one.</p>\n        </div></div>\n      </div>\n    </div>\n<div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 2 &ndash; April 18, 2026</h3>\n      <div class=\"slot\">\n        <span class=\"slot__time\">8:00 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4>\n          <p class=\"session__desc\">Doors open for day two, same as day one &ndash; coffee, check-in, and the shop already running.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">9:00 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Mastering DTF: From First Print to Profitable Growth</h4>\n        <p class=\"session__speaker\">Spencer Chernoff &ndash; Limitless Transfers</p>\n        <p class=\"session__desc\">The full DTF journey &ndash; from understanding the technology to running it as a profitable part of the business, with practical tips on artwork, quality control, and avoiding common pitfalls.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">MultiMedia Design and Implementation</h4>\n        <p class=\"session__speaker\">Megan Griffith &ndash; P&amp;M Apparel</p>\n        <p class=\"session__desc\">Combining multiple decoration methods &ndash; screen print, embroidery, transfers, specialty finishes &ndash; to elevate both design and perceived value.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">10:30 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Live Decorating (Shop Wide)</h4>\n          <p class=\"session__desc\">The whole shop floor live and running &ndash; every station, every method, all at once.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">11:45 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Lunch // Provided by SanMar</h4>\n          <p class=\"session__desc\">A break to eat, regroup, and keep the shop-floor conversations going.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">1:00 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Live Activations</h4>\n        <p class=\"session__speaker\">Ashleigh &amp; Elena Leon &ndash; The Side Garage</p>\n        <p class=\"session__desc\">How shops can execute successful live printing activations that engage audiences, create memorable experiences, and build stronger brand connections.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Selling with Empathy</h4>\n        <p class=\"session__speaker\">Alexis Davis &ndash; P&amp;M Apparel</p>\n        <p class=\"session__desc\">Strong sales start with understanding the customer &ndash; how empathy, clear communication, and thoughtful guidance build trust and long-term relationships.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">2:15 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Be Bold. Be Odd. Marketing That Actually Works</h4>\n        <p class=\"session__speaker\">Ryan Snaadt &ndash; Snaadt Media Group</p>\n        <p class=\"session__desc\">Most marketing gets ignored. How to use video, content, and storytelling to get attention, build trust, and create marketing people actually pay attention to.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Selling More Than A Shirt</h4>\n        <p class=\"session__speaker\">Ryan Toney &ndash; P&amp;M Apparel</p>\n        <p class=\"session__desc\">Decorators often have a captive audience. How shops can expand beyond apparel with promotional products that increase order value and strengthen client relationships.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">3:45 PM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Decorator Round Table</h4>\n          <p class=\"session__desc\">An open forum for fellow decorators on the realities of running a shop. Bring your questions, share your experiences, learn from the room.</p>\n        </div></div>\n      </div>\n    </div>\n    \n      <div style=\"margin-top:48px;padding-top:32px;border-top:2px solid var(--grey-light);\">\n        <h3 style=\"font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin-bottom:20px;\">Speakers</h3>\n        __SPEAKERS_2026__\n      </div>\n    </div>\n    <div class=\"year-panel\" data-year=\"2024\">\n      <div class=\"plaque\" style=\"margin-bottom:32px;\">\n        <p class=\"plaque__text\">FOC24 &ndash; April 19&ndash;20, 2024</p>\n      </div>\n      <p class=\"prose\" style=\"color:var(--grey);max-width:65ch;margin-bottom:40px;\">The first Flyover Con &ndash; an open house on the P&amp;M Apparel shop floor. One track, two days, peer-to-peer learning inside a working print shop.</p>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 1 &ndash; Friday, April 19, 2024</h3>\n      <div class=\"slot\"><span class=\"slot__time\">9:00 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4><p class=\"session__desc\">Doors open. Get checked in on the shop floor while the presses run.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">9:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Welcome // P&amp;M Apparel // The Goal of Flyover Con</h4><p class=\"session__speaker\">Jeremy Ray &ndash; Rock Hill Screen Printing &middot; Christy Shellenberger &ndash; Rock Hill Screen Printing</p><p class=\"session__desc\">Why Flyover Con exists, what makes it different, and what to expect.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">10:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Custom Headwear &amp; Cap America</h4><p class=\"session__speaker\">Randy Argotsinger &ndash; Cap America</p><p class=\"session__desc\">What decorators should know about custom headwear sourcing, decoration, and program design.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">11:45 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Women in Screen Printing</h4><p class=\"session__speaker\">Megan Griffith &ndash; P&amp;M Apparel &middot; Christy Shellenberger &ndash; Rock Hill Screen Printing &middot; Kay Ferin</p><p class=\"session__desc\">A panel conversation on navigating the print industry as women.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">12:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lunch</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">1:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">DTF Printing</h4><p class=\"session__speaker\">Adrienne Palmer &ndash; DTFPrinting.com</p><p class=\"session__desc\">The state of direct-to-film: production, equipment, and where the technology fits in a decorator&rsquo;s service mix.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">2:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Hiring &amp; Retention</h4><p class=\"session__speaker\">Megan Griffith &ndash; P&amp;M Apparel</p><p class=\"session__desc\">Finding good people and keeping them.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">3:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lean Manufacturing</h4><p class=\"session__speaker\">Steve Forbes &ndash; Iowa State University CIRAS</p><p class=\"session__desc\">How lean principles apply to a print shop floor &ndash; eliminating waste, improving throughput, building systems that scale.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">5:00 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Happy Hour // Live Print // Last Call Live Podcast</h4><p class=\"session__desc\">End of day on the shop floor. Presses running, drinks poured, podcast recording live.</p></div></div></div>\n      </div>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 2 &ndash; Saturday, April 20, 2024</h3>\n      <div class=\"slot\"><span class=\"slot__time\">9:00 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Breakfast // Welcome // Registration // Live Decorating</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">10:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Gildan Board of Decorators // Sustainability</h4><p class=\"session__speaker\">Ryan Toney &middot; Christy Shellenberger &ndash; Rock Hill Screen Printing</p><p class=\"session__desc\">Inside the Gildan Board of Decorators program and a conversation about sustainability in decorated apparel.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">11:45 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Trends in Blanks</h4><p class=\"session__speaker\">Jacob Whitman &ndash; P&amp;M Apparel &middot; Taylor Larson &ndash; Authentic Brands</p><p class=\"session__desc\">What&rsquo;s moving in wholesale blanks &ndash; styles, fabrics, and what your customers are actually asking for.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">12:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lunch</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">1:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Printavo</h4><p class=\"session__desc\">Shop management software &ndash; how to run a tighter operation from quote to ship.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">3:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Chipply</h4><p class=\"session__speaker\">Grace Schettler &ndash; Chipply</p><p class=\"session__desc\">Online team stores and how to build a webstore program that works for your shop and your clients.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">5:00 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Live Decorating</h4><p class=\"session__desc\">Final session closes on the shop floor.</p></div></div></div>\n      </div>\n      <div style=\"margin-top:48px;padding-top:32px;border-top:2px solid var(--grey-light);\">\n        <h3 style=\"font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin-bottom:20px;\">Speakers</h3>\n        __SPEAKERS_2024__\n      </div>\n    </div>\n  </div>\n</section>\n\n"
  },
  "speakers": {
    "title": "Speakers | Flyover Con",
    "desc": "Meet the shop owners, operators, and industry partners who speak at Flyover Con, the Midwest's hands-on screen printing and embroidery conference.",
    "canon": "https://www.flyovercon.ink/speakers.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Speakers\", \"item\": \"https://www.flyovercon.ink/speakers.html\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ryan Toney\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Megan Griffith\", \"jobTitle\": \"Owner & Art Director\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Amanda Clark\", \"jobTitle\": \"Financials Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Alexis Davis\", \"jobTitle\": \"Account Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Christy Shellenberger\", \"jobTitle\": \"Owner & VP of Sales\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Rock Hill Screen Printing\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Anna Wardenburg\", \"jobTitle\": \"Events Specialist\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Iowa Donor Network\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ali Hansen\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Pat Barton Dance Studio\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Amy Benton\", \"jobTitle\": \"Director of Marketing\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"MH Equipment\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Meghan Brazzelle\", \"jobTitle\": \"Senior Manager, Sales & Operations\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Chipply\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Paul A. Gormley\", \"jobTitle\": \"Digital Marketing & Innovation\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"CIRAS\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Justin Sebren\", \"jobTitle\": \"Co-Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Lucid Ink\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Mark Bailey\", \"jobTitle\": \"Sr Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ryan Snaadt\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Snaadt Media Group\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Chris Clark\", \"jobTitle\": \"Territory Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Matt Richardson\", \"jobTitle\": \"Co-Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Atonal Headwear / Relentless Merchandising\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Nathan Richardson\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Atonal Headwear / Relentless Merchandising\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Spencer Chernoff\", \"jobTitle\": \"Founder & CEO\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Limitless Transfers\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\", \"jobTitle\": \"Owners\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"The Side Garage\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Russ Corey\", \"jobTitle\": \"Strategic Account Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}]"
    ],
    "main": f"\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">FOC27</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Speakers</h1>\n    <p class=\"hero__lead\">Lineup for FOC27 hasn't been announced yet. Want to see who spoke last time? Check the Years Past archive.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"plaque\" style=\"margin-bottom:24px;\">\n      <p class=\"plaque__text\">Speakers TBD</p>\n    </div>\n    <p style=\"max-width:60ch;color:var(--grey);\">We're not booking speakers for FOC27 yet. Know your shop's story is worth sharing? <a href=\"mailto:ryan@flyovercon.ink\" style=\"color:var(--navy);font-weight:600;\">Reach out</a> or <a href=\"{MAILME_URL}\" style=\"color:var(--navy);font-weight:600;\">join the FOC27 list</a> to hear when the call for speakers opens.</p>\n    <p style=\"margin-top:24px;\"><a class=\"btn btn--outline\" href=\"years-past.html\">See Past Speakers</a></p>\n  </div>\n</section>\n"
  },
  "location": {
    "title": "Location | Flyover Con at P&M Apparel, Polk City IA",
    "desc": "Flyover Con is hosted inside P&M Apparel's production facility in Polk City, Iowa, 8,000 sq ft of working screen print and embroidery equipment.",
    "canon": "https://www.flyovercon.ink/location.html",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Location\", \"item\": \"https://www.flyovercon.ink/location.html\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}, \"geo\": {\"@type\": \"GeoCoordinates\", \"latitude\": 41.763743, \"longitude\": -93.719835}}]"
    ],
    "main": f"\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">The Venue</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">P&amp;M Apparel</h1>\n    <p class=\"hero__lead\">Flyover Con takes place inside P&amp;M Apparel's production facility, built in 2020 and intentionally designed to bring people, process, and production together in one open, transparent space.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container location-grid\">\n    <div>\n      <div class=\"map-embed\">\n        <iframe src=\"https://maps.google.com/maps?q=1100+S+5th+St,+Polk City,+IA+50226,+USA&z=16&output=embed\" loading=\"lazy\" title=\"Map to P&amp;M Apparel, 1100 S 5th St, Polk City, IA 50226\"></iframe>\n      </div>\n      <div class=\"prose\" style=\"margin-top:28px;\">\n        <p>With more than 8,000 square feet, the shop houses all sales, production, and fulfillment operations under one roof &ndash; multiple Anatol automatic presses, an Anatol manual press, a custom-built live screen printing press, an Anatol gas dryer, a Douthitt CTS, a Workhorse LED exposure table, ZSK and Barudan embroidery machines, Stahls Hotronix and MEM heat presses, and in-house digital and prototyping equipment. Every piece is visible, accessible, and actively used during the event.</p>\n        <p>Flyover Con doesn't happen on a stage or inside a conference hall &ndash; it's embedded directly into the shop floor. Attendees walk the same paths as the production team, stand next to presses, and watch garments move through the process end to end.</p>\n        <p>Hosting it in our own space is intentional. It reflects a commitment to transparency and a willingness to open the doors fully, even to potential competitors &ndash; sharing real systems, real decisions, and real lessons learned.</p>\n        <div class=\"photo-single\">\n          <img src=\"assets/img/event/foc26-005.jpg\" alt=\"Attendees seated on the Flyover Con shop floor during a session\" loading=\"lazy\">\n        </div>\n      </div>\n    </div>\n    <aside>\n      <div class=\"plaque\" style=\"width:100%;margin-bottom:24px;\">\n        <p class=\"plaque__text\" style=\"font-size:0.95rem;\">1100 S 5th St, Polk City, IA 50226</p>\n      </div>\n      <h3 style=\"font-size:1.1rem;\">Getting Here</h3>\n      <div class=\"getting-here\">\n        <div class=\"getting-here__item\">\n          <div class=\"getting-here__icon\">\u2708</div>\n          <div><strong>By Plane</strong><p style=\"color:var(--grey);margin:2px 0 0;\">Des Moines International Airport (DSM) &ndash; nonstop flights from many major U.S. cities, about a 30-minute drive to Polk City.</p></div>\n        </div>\n        <div class=\"getting-here__item\">\n          <div class=\"getting-here__icon\">\u2192</div>\n          <div><strong>By Car</strong><p style=\"color:var(--grey);margin:2px 0 0;\">About 10 miles west of I-35, accessible via Highway 415 &ndash; an easy drive from Des Moines and the surrounding metro.</p></div>\n        </div>\n      </div>\n      <h3 style=\"font-size:1.1rem;margin-top:32px;\">Need Somewhere to Stay?</h3>\n      <div class=\"hotel\"><h4>Qube Hotel</h4><p>1.3 miles from venue</p><p>300 Boulder Pointe, Polk City, IA 50226</p><p>(515) 984-3092</p></div>\n<div class=\"hotel\"><h4>Tru by Hilton Grimes Des Moines</h4><p>7 miles from venue</p><p>701 NE Gateway Dr, Grimes, IA 50111</p><p>(515) 608-8784</p></div>\n    </aside>\n  </div>\n</section>\n\n<section id=\"updates\" class=\"section--navy\">\n  <div class=\"container\">\n    <div class=\"block-grid\">\n      <div class=\"block block--gold\" style=\"grid-column:1 / -1;text-align:left;\">\n        <span class=\"section-head__eyebrow\" style=\"color:var(--navy-deep);opacity:0.7;\">Status: FOC27 &ndash; Date TBD</span>\n        <h2 style=\"color:var(--navy-deep);\">Want to know when FOC27 lands?</h2>\n        <p style=\"max-width:60ch;\">Dates aren't set yet &ndash; but when they are, this is the fastest way to hear about it first.</p>\n        <div style=\"display:flex;gap:16px;flex-wrap:wrap;margin-top:20px;\">\n          <a class=\"btn btn--outline-navy\" href=\"{MAILME_URL}\">Join the FOC27 List</a>\n          <a class=\"btn btn--outline-navy\" href=\"https://www.instagram.com/flyover_con/\" rel=\"noopener\" target=\"_blank\">Follow on Instagram</a>\n        </div>\n      </div>\n    </div>\n  </div>\n</section>\n\n"
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
{items}      <li><a class="site-nav__cta" href="{MAILME_URL}">Stay In The Loop</a></li>
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
          <a href="{IG}" aria-label="Flyover Con on Instagram" rel="noopener" target="_blank"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg></a>
          <a href="{FB}" aria-label="Flyover Con on Facebook" rel="noopener" target="_blank"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M22 12a10 10 0 1 0-11.5 9.87v-6.98H7.9V12h2.6V9.8c0-2.57 1.53-4 3.87-4 1.12 0 2.3.2 2.3.2v2.5h-1.3c-1.28 0-1.68.8-1.68 1.62V12h2.86l-.46 2.89h-2.4v6.98A10 10 0 0 0 22 12z"></path></svg></a>
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


def speaker_mini(year):
    pool = [s for s in SPEAKERS if year in s["years"]]
    cards = []
    for s in pool:
        if s["photo"]:
            p = s["photo"]
            alt = re.sub(r"&amp;", "and", s["name"])
            avatar = (f'<img class="mini-speaker__photo" src="assets/img/speakers/{p}.jpg" '
                      f'srcset="assets/img/speakers/{p}.jpg 1x, assets/img/speakers/{p}@2x.jpg 2x" '
                      f'alt="{alt}" width="120" height="120" loading="lazy" decoding="async">')
        else:
            avatar = f'<div class="mini-speaker__badge">{s["badge"]}</div>'
        # Strip company from role for display (keep it concise under the photo)
        role_parts = s["role"].split(" &middot; ")
        company = role_parts[-1] if role_parts else s["role"]
        cards.append(
            f'<div class="mini-speaker">'
            f'{avatar}'
            f'<p class="mini-speaker__name">{s["name"]}</p>'
            f'<p class="mini-speaker__role">{company}</p>'
            f'</div>'
        )
    return '<div class="mini-speaker-grid">' + "".join(cards) + '</div>'

def speaker_grid(year=None):
    pool = [s for s in SPEAKERS if year is None or year in s["years"]]
    out = ['<div class="speaker-grid">']
    for s in pool:
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
    body = page["main"].replace("__SPEAKERS_2026__", speaker_mini(year="2026"))
    body = body.replace("__SPEAKERS_2024__", speaker_mini(year="2024"))
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

Flyover Con is a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility. A modest registration fee keeps it accessible while sponsors cover the rest. No vendor booths, no sales pitches &ndash; real shop-floor learning from people who run print and embroidery shops every day.

Most recent event: FOC26, April 17-18, 2026, in Polk City, Iowa. 16 sessions across two days, 19 speakers, hosted on the P&M Apparel shop floor.

FOC27 is confirmed. Dates, schedule, speakers, and sponsors are not yet announced as of {UPDATED_HUMAN}.

- About: {BASE}/about.html
- Schedule (FOC27, TBD): {BASE}/schedule.html
- Years Past (full schedule archive): {BASE}/years-past.html
- Speakers (FOC27, TBD): {BASE}/speakers.html
- Location: {BASE}/location.html
- Contact: {EMAIL}
- Presented by: P&M Apparel &ndash; {PARENT_URL}
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
