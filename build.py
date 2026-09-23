#!/usr/bin/env python3
"""
Flyover Con static site generator for flyovercon.ink
Run:  python3 build.py      →  regenerates the entire ./site/ directory
Never edit ./site/ by hand; it is wiped and rebuilt on every run.
"""
import json, os, re, shutil, sys

# ---------------------------------------------------------------- constants
BASE            = "https://www.flyovercon.ink"
SITE_NAME       = "Flyover Con"
TAGLINE         = "The Midwest's conference for screen printers and decorators."
EMAIL           = "ryan@flyovercon.ink"
TODAY           = "2026-09-23"
UPDATED_HUMAN   = "September 2026"

# FOC27, public dates. The Thursday April 15 dinner is invite only and must not
# appear on any public page.
FOC27_START     = "2027-04-16"
FOC27_END       = "2027-04-17"
FOC27_HUMAN     = "April 16&ndash;17, 2027"
FOC27_LONG      = "Friday April 16 and Saturday April 17, 2027"
PARENT_NAME     = "P&amp;M Apparel"
PARENT_URL      = "https://www.pmapparel.com"
PARENT_ADDR     = "1100 S 5th St, Polk City, IA 50226"
IG              = "https://www.instagram.com/flyover_con/"
FB              = "https://www.facebook.com/profile.php?id=61556233233152"
OUT             = "site"

# FOC27 is presented by SanMar. The presenting sponsor lockups carry the
# sponsor credit wherever there is room to read it (home hero, footer). The nav
# is too small for "presented by" to be legible, so it gets the 2027 badge
# alone. The Organization schema keeps logo-512.png: that is Flyover Con the
# organization, not this year's event, and should not carry a sponsor.
PRESENTING_SPONSOR = "SanMar"
LOGO_BADGE      = "/assets/img/foc27-badge.svg"                 # 388.5 x 359.38
LOGO_STACKED    = "/assets/img/foc27-presented-stacked.svg"     # 381.55 x 431.21
LOGO_HORIZONTAL = "/assets/img/foc27-presented-horizontal.svg"  # 590.98 x 359.38
SPONSOR_WORDMARK = "/assets/img/sanmar-white.svg"               # 764.59 x 154.35

# The FOC27 notify list lives on our own domain now. The old Alliteration
# MailMe page is retired: it sent the highest intent click on the site off to a
# URL that read like a test deployment, and every share credited Vercel.
NOTIFY_URL      = "/notify"

# FOC27 planning survey POST target. This is our own serverless function at
# src/api/survey.js, same origin, so there is no CORS story to manage.
SURVEY_ENDPOINT = "/api/survey"

# Sponsor inquiry and speaker proposal POST targets. Same pattern as the
# survey: our own serverless functions, same origin, no CORS story.
SPONSOR_ENDPOINT = "/api/sponsor"
SPEAK_ENDPOINT   = "/api/speak"

SPONSOR_URL     = "/sponsor"
SPEAK_URL       = "/speak"

# Sponsor commitment deadline, from the FOC27 sponsor packet.
SPONSOR_DEADLINE = "January 15, 2027"

# Call for speakers milestones. Change these three lines and both the /speak
# dates list and the page copy follow. Keep them in chronological order.
PROPOSALS_CLOSE   = "November 13, 2026"
SPEAKERS_NOTIFIED = "December 11, 2026"
MATERIALS_DUE     = "February 12, 2027"

# Sponsor levels. Price is the string as it renders, availability is the small
# mono label beside the name. Order runs low to high on purpose so the
# "everything in the prior level" lines read in sequence.
SPONSOR_TIERS = [
    ("silver", "Silver", "Unlimited", "$1,000", [
        "Logo on event signage, website and digital agenda",
        "Mention during opening and closing remarks",
        "Materials included in attendee swag bags",
        "Group social media recognition and inclusion in event recaps",
    ]),
    ("gold", "Gold", "3 available", "$2,500", [
        "Everything in Silver, plus:",
        "Time to introduce yourself and your company to the full room on day one",
        "Recognition during major sessions and at lunch",
        "Dedicated social media features before and during the event",
        "Opt in attendee contact list following the event",
    ]),
    ("presenting", "Presenting", "Claimed", "$7,000", [
        "Everything in Gold, plus:",
        "Event branded as &ldquo;Flyover Con presented by [Sponsor]&rdquo; across all materials",
        "Stage recognition at opening and closing sessions, option to give the welcome address",
        "Logo on attendee swag bags and event apparel",
        "Featured in all pre event and post event social media",
        "First right of refusal on the 2028 presenting slot",
    ]),
]

# Standalone pages copied verbatim from ./src into ./site. They keep their own
# self-contained markup and CSS, stay out of NAV, and stay out of sitemap.xml.
# Each one is noindex on purpose.
RAW_PAGES = {
    "survey": {
        "src": "src/survey.html",
        "subs": {'var ENDPOINT = "";': f'var ENDPOINT = "{SURVEY_ENDPOINT}";'},
    },
}

# Files copied byte for byte from ./src into ./site, keeping their path.
# Vercel serves site/ as the deployment root, so site/api/*.js become functions.
COPY_FILES = ["api/survey.js", "api/notify.js", "api/sponsor.js", "api/speak.js"]

NAV = [("/","Home"),("/about","About"),("/speak","Call for Speakers"),
       ("/sponsor","Sponsor"),("/location","Location"),("/years-past","Years Past")]

# Schedule and Speakers are out of NAV until the FOC27 program is announced;
# until then they are placeholder pages. They stay live, in the footer, and in
# the sitemap. When speakers are confirmed: swap ("/speak","Call for Speakers")
# back out for ("/schedule","Schedule"),("/speakers","Speakers"). Don't show
# "Speak" and "Speakers" side by side; it reads as a typo.

# /notify stays out of NAV on purpose. It already has the nav CTA button plus
# both homepage buttons pointing at it; a seventh nav item would be noise.

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
    "bio": "Randy presented on custom headwear: sourcing, decoration options, and building headwear programs that work for decorators and their clients.",
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
    "bio": "Adrienne covered the state of direct-to-film printing: equipment, production workflow, and where DTF fits in a full-service decorator's mix.",
    "years": [
      "2024"
    ],
    "photo": None
  },
  {
    "badge": "SF",
    "name": "Steve Forbes",
    "role": "Iowa State University CIRAS",
    "bio": "Steve brought lean manufacturing principles to the print shop floor: eliminating waste, improving throughput, and building scalable systems.",
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
    "bio": "Jacob covered trends in wholesale blanks: what's moving, what customers are asking for, and how decorators should be thinking about their blank selections.",
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
    "desc": "FOC27 is April 16 and 17, 2027. A hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working shop floor in Polk City, Iowa. Capped at 75.",
    "canon": "https://www.flyovercon.ink/",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Event\", \"name\": \"Flyover Con 2027\", \"image\": [\"https://www.flyovercon.ink/assets/img/event/foc26-hero-16x9.jpg\", \"https://www.flyovercon.ink/assets/img/event/foc26-hero-4x3.jpg\", \"https://www.flyovercon.ink/assets/img/event/foc26-hero-1x1.jpg\"], \"url\": \"https://www.flyovercon.ink/\", \"startDate\": \"2027-04-16\", \"endDate\": \"2027-04-17\", \"eventAttendanceMode\": \"https://schema.org/OfflineEventAttendanceMode\", \"eventStatus\": \"https://schema.org/EventScheduled\", \"location\": {\"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}}, \"description\": \"The third Flyover Con, a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility in Polk City, Iowa. Attendance is capped at 75.\", \"organizer\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}, \"maximumAttendeeCapacity\": 75}]"
    ],
    "main": f"\n\n<section class=\"hero\">\n  <div class=\"container hero__inner\">\n    <img class=\"hero__logo\" src=\"{LOGO_STACKED}\" alt=\"Flyover Con 2027, presented by {PRESENTING_SPONSOR}\" width=\"260\" height=\"294\">\n    <div class=\"hero__eyebrow\">Status Board: Polk&nbsp;City,&nbsp;Iowa</div>\n    <div class=\"plaque\" style=\"margin:0 auto 22px;\"><p class=\"plaque__text\">FOC27: April 16&ndash;17, 2027</p></div>\n    <h1>The Midwest's conference<br>for people who <span class=\"accent\">make things.</span></h1>\n    <p class=\"hero__lead\">The Midwest's conference for screen printers and decorators. Hosted inside a working screen print and embroidery shop by P&M Apparel. No vendor booths, no sales pitches, just the shop floor and the people running it.</p>\n    <div class=\"hero__actions\">\n      <a class=\"btn btn--gold\" href=\"{NOTIFY_URL}\">Get Notified for FOC27</a>\n      <a class=\"btn btn--outline\" href=\"https://www.youtube.com/watch?v=q7Qx18jLp_o\" rel=\"noopener\" target=\"_blank\">See the FOC26 Recap</a>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">What It Is</span>\n      <h2>Not a trade show. A working shop floor.</h2>\n      <p>Flyover Con is a hands-on conference for screen printers, embroiderers, and decorators who want practical learning, real conversations, and a stronger sense of community, built and hosted by P&amp;M Apparel, right inside their own working screen print and embroidery facility.</p>\n    </div>\n    <div class=\"stat-strip\">\n      <div class=\"stat\"><span class=\"stat__num\">2</span><span class=\"stat__label\">Conferences So Far</span></div>\n<div class=\"stat\"><span class=\"stat__num\">16</span><span class=\"stat__label\">Sessions at FOC26</span></div>\n<div class=\"stat\"><span class=\"stat__num\">19</span><span class=\"stat__label\">Speakers &amp; Panelists</span></div>\n<div class=\"stat\"><span class=\"stat__num\">2</span><span class=\"stat__label\">Days on the Shop Floor</span></div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">From The Floor</span>\n      <h2>What people actually said.</h2>\n    </div>\n    <div class=\"testimonial-strip\">\n      <div class=\"testimonial\">\n        <p class=\"testimonial__quote\">This was the first time we&rsquo;ve left a show and didn&rsquo;t say &ldquo;I wish they would&rsquo;ve talked about this or that.&rdquo;</p>\n        <div class=\"testimonial__source\">\n          <p class=\"testimonial__name\">Darci</p>\n          <p class=\"testimonial__shop\">Spot On Printing</p>\n        </div>\n      </div>\n      <div class=\"testimonial\">\n        <p class=\"testimonial__quote\">The friendly faces and no-gatekeeping mentality. It was so refreshing.</p>\n        <div class=\"testimonial__source\">\n          <p class=\"testimonial__name\">Emily</p>\n          <p class=\"testimonial__shop\">Sparkling Image</p>\n        </div>\n      </div>\n      <div class=\"testimonial\">\n        <p class=\"testimonial__quote\">Try to keep me away. I dare you.</p>\n        <div class=\"testimonial__source\">\n          <p class=\"testimonial__name\">Peter</p>\n          <p class=\"testimonial__shop\">A&amp;P Graphics</p>\n        </div>\n      </div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">From FOC26</span>\n      <h2>Scenes from the shop floor.</h2>\n    </div>\n    <div class=\"photo-strip\">\n      <img src=\"/assets/img/event/foc26-007.jpg\" alt=\"Flyover Con VIP Lounge refreshment station\" loading=\"lazy\" width=\"400\" height=\"220\">\n      <img src=\"/assets/img/event/foc26-006.jpg\" alt=\"Attendees talking between sessions at Flyover Con\" loading=\"lazy\" width=\"400\" height=\"220\">\n      <img src=\"/assets/img/event/foc26-002.jpg\" alt=\"A speaker presenting to the room at Flyover Con\" loading=\"lazy\" width=\"400\" height=\"220\">\n      <img src=\"/assets/img/event/foc26-009.jpg\" alt=\"A speaker presenting near the Gate B sign at Flyover Con\" loading=\"lazy\" width=\"400\" height=\"220\">\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">FOC27</span>\n      <h2>Sponsorship is open.</h2>\n      <p>FOC26 was made possible by SanMar, Limitless Transfers, PrintGrip, Chipply, S&amp;S Activewear, SPSI, Embellishr, and Atonal Headwear. FOC27 is presented by {PRESENTING_SPONSOR}. Silver and Gold are open now, and commitments are due {SPONSOR_DEADLINE}.</p>\n    </div>\n    <div class=\"hero__actions\" style=\"justify-content:flex-start;\">\n      <a class=\"btn btn--gold\" href=\"{SPONSOR_URL}\">See Sponsor Levels</a>\n      <a class=\"btn btn--outline\" href=\"{SPEAK_URL}\">Submit a Session</a>\n    </div>\n  </div>\n</section>\n\n"
  },
  "about": {
    "title": "About Flyover Con | Hands-On Decorator Conference",
    "desc": "Flyover Con is a hands-on conference for screen printers and decorators hosted inside a working Iowa print and embroidery shop. No booths, no pitches.",
    "canon": "https://www.flyovercon.ink/about",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"About\", \"item\": \"https://www.flyovercon.ink/about\"}]}]"
    ],
    "main": "\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">About</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">What is Flyover Con?</h1>\n  </div>\n</section>\n\n<section>\n  <div class=\"container two-col\">\n    <div class=\"prose\">\n      <p>Flyover Con is a hands-on conference built for screen printers, embroiderers, and decorators who want practical learning, real conversations, and a stronger sense of community.</p>\n      <p>Hosted inside a working print and embroidery shop in Polk City, Iowa, Flyover Con brings together shop owners, managers, and decorators to learn from people who are actively doing the work every day. Sessions focus on real-world challenges and solutions: what actually works on the shop floor and in the office.</p>\n      <p>Flyover Con is intentionally different from traditional industry events. There are no vendor booths and no sales-driven presentations. Instead, the event is built around education, transparency, and connection. Attendees are encouraged to ask questions, walk the production floor, and engage directly with speakers and fellow decorators.</p>\n      <p>The name reflects a belief that great work is happening everywhere, not just in major markets. The Midwest is full of skilled, hardworking shops doing innovative things, and Flyover Con exists to highlight that work while welcoming decorators from across the country.</p>\n    </div>\n    <div class=\"plaque\" style=\"width:100%;\">\n      <p class=\"plaque__text\" style=\"font-size:0.95rem;line-height:1.6;\">\"The term &lsquo;flyover&rsquo; often describes the Midwest as something to be passed over. For us, it represents the opposite.\"</p>\n    </div>\n  </div>\n</section>\n\n<section class=\"section--navy\">\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">Why Attend</span>\n      <h2>Why decorators keep coming back.</h2>\n    </div>\n    <div class=\"card-grid\">\n      <div class=\"reason-card\">\n        <h3>You leave with something real.</h3>\n        <p>Every session is built around practical, shop-floor challenges: pricing, webstores, workflows, hiring, data. Not theory. Things you can act on Monday morning.</p>\n        <blockquote class=\"reason-card__quote\">\n          The hands-on learning and transparency of the entire P&amp;M Apparel team.\n          <span class=\"reason-card__attr\">Lynn, House of Brands</span>\n        </blockquote>\n      </div>\n      <div class=\"reason-card\">\n        <h3>No gatekeeping. No sales pitch.</h3>\n        <p>Speakers share what actually works, including what didn&rsquo;t. There are no vendor booths, no sponsored talking points, and no one holding back the good stuff.</p>\n        <blockquote class=\"reason-card__quote\">\n          Don&rsquo;t change the vibe. Not feeling like I was being sold to was a big deal to me.\n          <span class=\"reason-card__attr\">Karen, Get GAPD</span>\n        </blockquote>\n      </div>\n      <div class=\"reason-card\">\n        <h3>It happens on a real shop floor.</h3>\n        <p>Not a convention center. Not a hotel ballroom. The presses run during sessions. You can walk the floor, ask the crew anything, and see a working shop in motion.</p>\n      </div>\n      <div class=\"reason-card\">\n        <h3>The connections are the point.</h3>\n        <p>Small enough that you actually talk to people. Speakers stick around for coffee, lunch, and happy hour. Most attendees leave with contacts they&rsquo;ll actually use.</p>\n        <blockquote class=\"reason-card__quote\">\n          You made each and every one of us feel like family.\n          <span class=\"reason-card__attr\">Angela, America&rsquo;s Best Apparel</span>\n        </blockquote>\n      </div>\n      <div class=\"reason-card\">\n        <h3>It&rsquo;s built for shops like yours.</h3>\n        <p>Small shop, large shop, one-person operation. It doesn&rsquo;t matter. Nobody here is too big to share or too small to belong. The Midwest has always worked that way.</p>\n      </div>\n    </div>\n    <div class=\"photo-pair\">\n      <img src=\"/assets/img/event/foc26-001.jpg\" alt=\"Attendees examining production work on the Flyover Con shop floor\" loading=\"lazy\">\n      <img src=\"/assets/img/event/foc26-008.jpg\" alt=\"An attendee taking notes during a Flyover Con session\" loading=\"lazy\">\n    </div>\n  </div>\n</section>\n\n"
  },
  "notify": {
    "title": "Get Notified for FOC27 | Flyover Con",
    "desc": "FOC26 sold out at 75. Join the Flyover Con list to hear when FOC27 registration opens, April 16 and 17, 2027 in Polk City, Iowa.",
    "canon": "https://www.flyovercon.ink/notify",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Get Notified for FOC27\", \"item\": \"https://www.flyovercon.ink/notify\"}]}]"
    ],
    "main": "\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">FOC27: April 16&ndash;17, 2027</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Get the registration link first.</h1>\n    <p class=\"hero__lead\">FOC26 sold out at 75 people. FOC27 caps at the same number. This list hears when registration opens, before it goes anywhere else.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"signup\" id=\"signup\">\n      <div class=\"signup__field\">\n        <label for=\"n-name\">Your name</label>\n        <input type=\"text\" id=\"n-name\" name=\"name\" autocomplete=\"name\" required>\n      </div>\n      <div class=\"signup__field\">\n        <label for=\"n-email\">Email</label>\n        <input type=\"email\" id=\"n-email\" name=\"email\" autocomplete=\"email\" required>\n      </div>\n      <div class=\"signup__field\">\n        <label for=\"n-city\">City and state</label>\n        <input type=\"text\" id=\"n-city\" name=\"city_state\" autocomplete=\"address-level2\">\n      </div>\n      <div class=\"signup__hp\" aria-hidden=\"true\">\n        <label for=\"n-gotcha\">Leave this empty</label>\n        <input type=\"text\" id=\"n-gotcha\" name=\"_gotcha\" tabindex=\"-1\" autocomplete=\"off\">\n      </div>\n      <button class=\"btn btn--gold\" type=\"button\" id=\"n-submit\">Join the FOC27 List</button>\n      <p class=\"signup__msg\" id=\"n-msg\" role=\"status\" aria-live=\"polite\"></p>\n      <p class=\"signup__note\">This is not a reserved seat. Registration has not opened and nothing is being held. We use your email for Flyover Con updates only, and we do not sell it.</p>\n    </div>\n\n    <div class=\"signup__done\" id=\"signup-done\" hidden>\n      <h2>You are on the list.</h2>\n      <p>We will email you when FOC27 registration opens. In the meantime, <a href=\"/survey\" style=\"color:var(--navy);font-weight:600;\">tell us what to teach</a>. It takes about five minutes and it shapes the schedule.</p>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"section-head\">\n      <span class=\"section-head__eyebrow\">What You Are Signing Up For</span>\n      <h2>Not many emails.</h2>\n      <p>Registration opening, the schedule going live, and the speaker lineup. That is it. Flyover Con runs on no vendor booths and no sales pitches, and the list works the same way. Anything else, reach out at <a href=\"mailto:ryan@flyovercon.ink\" style=\"color:var(--navy);font-weight:600;\">ryan@flyovercon.ink</a>.</p>\n    </div>\n  </div>\n</section>\n\n<script>\n(function(){\n  var btn  = document.getElementById('n-submit');\n  var msg  = document.getElementById('n-msg');\n  var box  = document.getElementById('signup');\n  var done = document.getElementById('signup-done');\n  var EMAIL = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/;\n\n  function val(id){ return document.getElementById(id).value.trim(); }\n  function err(text, focusId){\n    msg.className = 'signup__msg signup__msg--err';\n    msg.textContent = text;\n    if(focusId) document.getElementById(focusId).focus();\n  }\n\n  btn.addEventListener('click', function(){\n    var name = val('n-name'), email = val('n-email');\n    msg.className = 'signup__msg';\n\n    if(!name){ err('Please add your name.', 'n-name'); return; }\n    if(!EMAIL.test(email)){ err('That email address does not look right.', 'n-email'); return; }\n\n    btn.disabled = true;\n    msg.textContent = 'Adding you to the list.';\n\n    fetch('/api/notify', {\n      method: 'POST',\n      headers: {'Content-Type':'application/json'},\n      body: JSON.stringify({\n        name: name,\n        email: email,\n        city_state: val('n-city'),\n        _gotcha: val('n-gotcha')\n      })\n    }).then(function(r){ return r.json(); }).then(function(d){\n      if(!d || d.ok !== true) throw new Error('failed');\n      box.hidden = true;\n      done.hidden = false;\n      done.scrollIntoView({block:'center'});\n    }).catch(function(){\n      btn.disabled = false;\n      err('That did not send. Email ryan@flyovercon.ink and we will add you by hand.');\n    });\n  });\n})();\n</script>\n\n"
  },
  "schedule": {
    "title": "Schedule | Flyover Con FOC27",
    "desc": "FOC27 runs April 16 and 17, 2027. Flyover Con is the Midwest's hands-on conference for screen printers and decorators, hosted inside P&M Apparel's working shop floor in Polk City, Iowa.",
    "canon": "https://www.flyovercon.ink/schedule",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Schedule\", \"item\": \"https://www.flyovercon.ink/schedule\"}]}]"
    ],
    "main": f"\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">FOC27</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Schedule</h1>\n    <p class=\"hero__lead\">FOC27 is April 16 and 17, 2027. The session schedule is not built yet. Want to see how past years ran? Check the Years Past archive.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"plaque\" style=\"margin-bottom:24px;\">\n      <p class=\"plaque__text\">Next Departure: FOC27, April 16&ndash;17, 2027</p>\n    </div>\n    <p style=\"max-width:60ch;color:var(--grey);\">Sessions and tracks for FOC27 will land here once they're locked. It runs at P&amp;M Apparel in Polk City, Iowa, and the room caps at 75. <a href=\"{NOTIFY_URL}\" style=\"color:var(--navy);font-weight:600;\">Join the FOC27 list</a> to hear the moment it's posted.</p>\n    <p style=\"margin-top:24px;\"><a class=\"btn btn--outline\" href=\"/years-past\">See Past Schedules</a></p>\n  </div>\n</section>\n"
  },
  "years-past": {
    "title": "Years Past | Flyover Con Schedule Archive",
    "desc": "Full session schedules from every Flyover Con. FOC26: 16 sessions, 19 speakers, two days on the P&M Apparel shop floor in Polk City, Iowa.",
    "canon": "https://www.flyovercon.ink/years-past",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Years Past\", \"item\": \"https://www.flyovercon.ink/years-past\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Event\", \"name\": \"Flyover Con 2026\", \"image\": [\"https://www.flyovercon.ink/assets/img/event/foc26-hero-16x9.jpg\", \"https://www.flyovercon.ink/assets/img/event/foc26-hero-4x3.jpg\", \"https://www.flyovercon.ink/assets/img/event/foc26-hero-1x1.jpg\"], \"url\": \"https://www.flyovercon.ink/years-past\", \"startDate\": \"2026-04-17\", \"endDate\": \"2026-04-18\", \"eventAttendanceMode\": \"https://schema.org/OfflineEventAttendanceMode\", \"eventStatus\": \"https://schema.org/EventScheduled\", \"location\": {\"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}}, \"description\": \"The second year of Flyover Con, a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility in Polk City, Iowa.\", \"organizer\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}, \"performer\": [{\"@type\": \"Person\", \"name\": \"Ryan Toney\"}, {\"@type\": \"Person\", \"name\": \"Megan Griffith\"}, {\"@type\": \"Person\", \"name\": \"Amanda Clark\"}, {\"@type\": \"Person\", \"name\": \"Alexis Davis\"}, {\"@type\": \"Person\", \"name\": \"Christy Shellenberger\"}, {\"@type\": \"Person\", \"name\": \"Anna Wardenburg\"}, {\"@type\": \"Person\", \"name\": \"Ali Hansen\"}, {\"@type\": \"Person\", \"name\": \"Amy Benton\"}, {\"@type\": \"Person\", \"name\": \"Meghan Brazzelle\"}, {\"@type\": \"Person\", \"name\": \"Paul A. Gormley\"}, {\"@type\": \"Person\", \"name\": \"Justin Sebren\"}, {\"@type\": \"Person\", \"name\": \"Mark Bailey\"}, {\"@type\": \"Person\", \"name\": \"Ryan Snaadt\"}, {\"@type\": \"Person\", \"name\": \"Chris Clark\"}, {\"@type\": \"Person\", \"name\": \"Matt Richardson\"}, {\"@type\": \"Person\", \"name\": \"Nathan Richardson\"}, {\"@type\": \"Person\", \"name\": \"Spencer Chernoff\"}, {\"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\"}, {\"@type\": \"Person\", \"name\": \"Russ Corey\"}]}]"
    ],
    "main": "\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">Archive</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Years Past</h1>\n    <p class=\"hero__lead\">Every Flyover Con schedule, one flight at a time. For most time blocks, two sessions run at once (one in Gate A, one in Gate B), so you could always build a day that fit what you wanted to learn.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <h2 style=\"font-size:1.15rem;margin-bottom:20px;color:var(--ink);\">Session Schedules</h2>\n    <div class=\"year-tabs\" role=\"tablist\" aria-label=\"Flyover Con years\">\n      <button class=\"year-tab\" data-year=\"2026\" aria-selected=\"true\">FOC26</button>\n      <button class=\"year-tab\" data-year=\"2024\">FOC24</button>\n    </div>\n    <div class=\"year-panel is-active\" data-year=\"2026\">\n      <div class=\"plaque\" style=\"margin-bottom:32px;\">\n        <p class=\"plaque__text\">FOC26: April 17\u201318, 2026</p>\n      </div>\n      <p class=\"prose\" style=\"color:var(--grey);max-width:65ch;margin-bottom:40px;\">Flyover Con's second year, and the first with a full two-track schedule.</p>\n      <div class=\"photo-single\" style=\"margin-bottom:40px;\">\n        <img src=\"/assets/img/event/foc26-004.jpg\" alt=\"A speaker presenting a session at Flyover Con 2026\" loading=\"lazy\">\n      </div>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 1: April 17, 2026</h3>\n      <div class=\"slot\">\n        <span class=\"slot__time\">8:00 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4>\n          <p class=\"session__desc\">Doors open. Grab coffee, get checked in, and watch the shop come alive before the first session.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">9:00 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Finding Your Profit Centers</h4>\n        <p class=\"session__speaker\">Christy Shellenberger, Rock Hill Screen Printing</p>\n        <p class=\"session__desc\">Revenue is fun. Profit is what keeps the lights on. A real shop case study breaking down where the money is actually made, where it's lost, and the decisions that move the needle: pricing, products, labor, and the difference between being busy and being profitable.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">From the Other Side of the Order</h4>\n        <p class=\"session__speaker\">Megan Griffith (Moderator), P&amp;M Apparel, with Anna Wardenburg, Ali Hansen, Amy Benton</p>\n        <p class=\"session__desc\">Real customers on what makes them choose a shop, what keeps them coming back, and what creates frustration along the way. A moderated conversation on serving, communicating with, and retaining clients.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">10:30 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Building Webstores That Sell</h4>\n        <p class=\"session__speaker\">Meghan Brazzelle, Chipply</p>\n        <p class=\"session__desc\">How successful shops use webstores to simplify ordering and unlock scalable sales serving teams, schools, and organizations more efficiently.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">AI for Streamlining Business</h4>\n        <p class=\"session__speaker\">Paul Gormley, CIRAS</p>\n        <p class=\"session__desc\">AI is more than a design tool. How decorators can use it to streamline everyday operations: marketing, analytics, communication, and decision-making.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">11:45 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Lunch // Provided by PrintGrip</h4>\n          <p class=\"session__desc\">A break to eat, regroup, and keep the shop-floor conversations going.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">1:00 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Making Better Decisions With Data</h4>\n        <p class=\"session__speaker\">Amanda Clark, P&amp;M Apparel</p>\n        <p class=\"session__desc\">Your business generates more data than you think. How to turn everyday information into actionable insights that improve operations, guide strategy, and drive results.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Serving Your Community</h4>\n        <p class=\"session__speaker\">Justin Sebren, Lucid Ink</p>\n        <p class=\"session__desc\">Strong community relationships can be one of a shop's greatest advantages. Building local trust, supporting organizations, and turning involvement into lasting growth.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">2:15 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Resources for Decorators</h4>\n        <p class=\"session__speaker\">Mark Bailey, SanMar</p>\n        <p class=\"session__desc\">Tools, organizations, and industry resources decorators can lean on to improve operations, stay informed, and keep learning.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Relentless Determination</h4>\n        <p class=\"session__speaker\">Matt and Nate Richardson, Relentless Merchandise</p>\n        <p class=\"session__desc\">The real story behind Relentless Merch's growth: the obstacles, the mistakes, the risk, and what it actually takes to build something and keep pushing when things get hard.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">3:45 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Why Customers Choose You (And Not the Cheaper Guy)</h4>\n        <p class=\"session__speaker\">Ryan Toney (Moderator), P&amp;M Apparel, with Christy Shellenberger, Justin Sebren, Chris Clark</p>\n        <p class=\"session__desc\">A panel on customer experience, professionalism, communication, and the real reasons customers choose one shop over another.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Not All Work Is Good Work (When to Say No)</h4>\n        <p class=\"session__speaker\">Megan Griffith (Moderator), P&amp;M Apparel, with Matt and Nate Richardson, Spencer Chernoff</p>\n        <p class=\"session__desc\">Not every order, customer, or opportunity is worth taking. Learning when to say no is often where profitability actually comes from.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">5:00 PM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Happy Hour // Presented by SanMar</h4>\n          <p class=\"session__desc\">Drinks, snacks, and a live band to close out day one.</p>\n        </div></div>\n      </div>\n    </div>\n<div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 2: April 18, 2026</h3>\n      <div class=\"slot\">\n        <span class=\"slot__time\">8:00 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4>\n          <p class=\"session__desc\">Doors open for day two, same as day one: coffee, check-in, and the shop already running.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">9:00 AM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Mastering DTF: From First Print to Profitable Growth</h4>\n        <p class=\"session__speaker\">Spencer Chernoff, Limitless Transfers</p>\n        <p class=\"session__desc\">The full DTF journey, from understanding the technology to running it as a profitable part of the business, with practical tips on artwork, quality control, and avoiding common pitfalls.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">MultiMedia Design and Implementation</h4>\n        <p class=\"session__speaker\">Megan Griffith, P&amp;M Apparel</p>\n        <p class=\"session__desc\">Combining multiple decoration methods (screen print, embroidery, transfers, specialty finishes) to elevate both design and perceived value.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">10:30 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Live Decorating (Shop Wide)</h4>\n          <p class=\"session__desc\">The whole shop floor live and running: every station, every method, all at once.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">11:45 AM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Lunch // Provided by SanMar</h4>\n          <p class=\"session__desc\">A break to eat, regroup, and keep the shop-floor conversations going.</p>\n        </div></div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">1:00 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Live Activations</h4>\n        <p class=\"session__speaker\">Ashleigh &amp; Elena Leon, The Side Garage</p>\n        <p class=\"session__desc\">How shops can execute successful live printing activations that engage audiences, create memorable experiences, and build stronger brand connections.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Selling with Empathy</h4>\n        <p class=\"session__speaker\">Alexis Davis, P&amp;M Apparel</p>\n        <p class=\"session__desc\">Strong sales start with understanding the customer: how empathy, clear communication, and thoughtful guidance build trust and long-term relationships.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">2:15 PM</span>\n        <div class=\"slot__sessions\">\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate A</span>\n        <h4 class=\"session__title\">Be Bold. Be Odd. Marketing That Actually Works</h4>\n        <p class=\"session__speaker\">Ryan Snaadt, Snaadt Media Group</p>\n        <p class=\"session__desc\">Most marketing gets ignored. How to use video, content, and storytelling to get attention, build trust, and create marketing people actually pay attention to.</p>\n      </div>\n        <div class=\"session\">\n        <span class=\"session__gate\">Gate B</span>\n        <h4 class=\"session__title\">Selling More Than A Shirt</h4>\n        <p class=\"session__speaker\">Ryan Toney, P&amp;M Apparel</p>\n        <p class=\"session__desc\">Decorators often have a captive audience. How shops can expand beyond apparel with promotional products that increase order value and strengthen client relationships.</p>\n      </div>\n        </div>\n      </div><div class=\"slot\">\n        <span class=\"slot__time\">3:45 PM</span>\n        <div class=\"slot__sessions\"><div class=\"session session--solo\">\n          <h4 class=\"session__title\">Decorator Round Table</h4>\n          <p class=\"session__desc\">An open forum for fellow decorators on the realities of running a shop. Bring your questions, share your experiences, learn from the room.</p>\n        </div></div>\n      </div>\n    </div>\n    \n      <div style=\"margin-top:48px;padding-top:32px;border-top:2px solid var(--grey-light);\">\n        <h3 style=\"font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin-bottom:20px;\">Speakers</h3>\n        __SPEAKERS_2026__\n      </div>\n    </div>\n    <div class=\"year-panel\" data-year=\"2024\">\n      <div class=\"plaque\" style=\"margin-bottom:32px;\">\n        <p class=\"plaque__text\">FOC24: April 19&ndash;20, 2024</p>\n      </div>\n      <p class=\"prose\" style=\"color:var(--grey);max-width:65ch;margin-bottom:40px;\">The first Flyover Con: an open house on the P&amp;M Apparel shop floor. One track, two days, peer-to-peer learning inside a working print shop.</p>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 1: Friday, April 19, 2024</h3>\n      <div class=\"slot\"><span class=\"slot__time\">9:00 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Breakfast // Registration // Live Decorating</h4><p class=\"session__desc\">Doors open. Get checked in on the shop floor while the presses run.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">9:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Welcome // P&amp;M Apparel // The Goal of Flyover Con</h4><p class=\"session__speaker\">Jeremy Ray, Rock Hill Screen Printing &middot; Christy Shellenberger, Rock Hill Screen Printing</p><p class=\"session__desc\">Why Flyover Con exists, what makes it different, and what to expect.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">10:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Custom Headwear &amp; Cap America</h4><p class=\"session__speaker\">Randy Argotsinger, Cap America</p><p class=\"session__desc\">What decorators should know about custom headwear sourcing, decoration, and program design.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">11:45 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Women in Screen Printing</h4><p class=\"session__speaker\">Megan Griffith, P&amp;M Apparel &middot; Christy Shellenberger, Rock Hill Screen Printing &middot; Kay Ferin</p><p class=\"session__desc\">A panel conversation on navigating the print industry as women.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">12:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lunch</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">1:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">DTF Printing</h4><p class=\"session__speaker\">Adrienne Palmer, DTFPrinting.com</p><p class=\"session__desc\">The state of direct-to-film: production, equipment, and where the technology fits in a decorator&rsquo;s service mix.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">2:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Hiring &amp; Retention</h4><p class=\"session__speaker\">Megan Griffith, P&amp;M Apparel</p><p class=\"session__desc\">Finding good people and keeping them.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">3:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lean Manufacturing</h4><p class=\"session__speaker\">Steve Forbes, Iowa State University CIRAS</p><p class=\"session__desc\">How lean principles apply to a print shop floor: eliminating waste, improving throughput, building systems that scale.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">5:00 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Happy Hour // Live Print // Last Call Live Podcast</h4><p class=\"session__desc\">End of day on the shop floor. Presses running, drinks poured, podcast recording live.</p></div></div></div>\n      </div>\n      <div class=\"day-block\">\n      <h3 class=\"day-block__title\">Day 2: Saturday, April 20, 2024</h3>\n      <div class=\"slot\"><span class=\"slot__time\">9:00 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Breakfast // Welcome // Registration // Live Decorating</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">10:30 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Gildan Board of Decorators // Sustainability</h4><p class=\"session__speaker\">Ryan Toney &middot; Christy Shellenberger, Rock Hill Screen Printing</p><p class=\"session__desc\">Inside the Gildan Board of Decorators program and a conversation about sustainability in decorated apparel.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">11:45 AM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Trends in Blanks</h4><p class=\"session__speaker\">Jacob Whitman, P&amp;M Apparel &middot; Taylor Larson, Authentic Brands</p><p class=\"session__desc\">What&rsquo;s moving in wholesale blanks: styles, fabrics, and what your customers are actually asking for.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">12:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Lunch</h4></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">1:30 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Printavo</h4><p class=\"session__desc\">Shop management software: how to run a tighter operation from quote to ship.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">3:45 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Chipply</h4><p class=\"session__speaker\">Grace Schettler, Chipply</p><p class=\"session__desc\">Online team stores and how to build a webstore program that works for your shop and your clients.</p></div></div></div>\n      <div class=\"slot\"><span class=\"slot__time\">5:00 PM</span><div class=\"slot__sessions\"><div class=\"session session--solo\"><h4 class=\"session__title\">Live Decorating</h4><p class=\"session__desc\">Final session closes on the shop floor.</p></div></div></div>\n      </div>\n      <div style=\"margin-top:48px;padding-top:32px;border-top:2px solid var(--grey-light);\">\n        <h3 style=\"font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin-bottom:20px;\">Speakers</h3>\n        __SPEAKERS_2024__\n      </div>\n    </div>\n  </div>\n</section>\n\n"
  },
  "speakers": {
    "title": "Speakers | Flyover Con",
    "desc": "Meet the shop owners, operators, and industry partners who speak at Flyover Con, the Midwest's hands-on screen printing and embroidery conference.",
    "canon": "https://www.flyovercon.ink/speakers",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Speakers\", \"item\": \"https://www.flyovercon.ink/speakers\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ryan Toney\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Megan Griffith\", \"jobTitle\": \"Owner & Art Director\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Amanda Clark\", \"jobTitle\": \"Financials Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Alexis Davis\", \"jobTitle\": \"Account Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Christy Shellenberger\", \"jobTitle\": \"Owner & VP of Sales\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Rock Hill Screen Printing\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Anna Wardenburg\", \"jobTitle\": \"Events Specialist\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Iowa Donor Network\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ali Hansen\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Pat Barton Dance Studio\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Amy Benton\", \"jobTitle\": \"Director of Marketing\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"MH Equipment\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Meghan Brazzelle\", \"jobTitle\": \"Senior Manager, Sales & Operations\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Chipply\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Paul A. Gormley\", \"jobTitle\": \"Digital Marketing & Innovation\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"CIRAS\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Justin Sebren\", \"jobTitle\": \"Co-Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Lucid Ink\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Mark Bailey\", \"jobTitle\": \"Sr Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ryan Snaadt\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Snaadt Media Group\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Chris Clark\", \"jobTitle\": \"Territory Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Matt Richardson\", \"jobTitle\": \"Co-Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Atonal Headwear / Relentless Merchandising\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Nathan Richardson\", \"jobTitle\": \"Owner\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Atonal Headwear / Relentless Merchandising\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Spencer Chernoff\", \"jobTitle\": \"Founder & CEO\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"Limitless Transfers\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Ashleigh & Elena Leon\", \"jobTitle\": \"Owners\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"The Side Garage\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"Person\", \"name\": \"Russ Corey\", \"jobTitle\": \"Strategic Account Manager\", \"worksFor\": {\"@type\": \"Organization\", \"name\": \"SanMar\"}}]"
    ],
    "main": f"\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">FOC27</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">Speakers</h1>\n    <p class=\"hero__lead\">FOC27 is April 16 and 17, 2027. The lineup hasn't been announced yet, because the call for speakers is open right now and the program is still being built.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container\">\n    <div class=\"plaque\" style=\"margin-bottom:24px;\">\n      <p class=\"plaque__text\">Call for Speakers: Open</p>\n    </div>\n    <p style=\"max-width:60ch;color:var(--grey);\">Proposals for FOC27 close {PROPOSALS_CLOSE}. We are looking for people who will teach a task rather than pitch a product, and first time speakers are genuinely welcome. Sessions, live demos at the equipment, and panel seats are all open.</p>\n    <p style=\"margin-top:24px;display:flex;gap:16px;flex-wrap:wrap;\"><a class=\"btn btn--gold\" href=\"{SPEAK_URL}\">Submit a Session</a><a class=\"btn btn--outline\" href=\"/years-past\">See Past Speakers</a></p>\n  </div>\n</section>\n"
  },
  "location": {
    "title": "Location | Flyover Con at P&M Apparel, Polk City IA",
    "desc": "Flyover Con is hosted inside P&M Apparel's production facility in Polk City, Iowa, 8,000 sq ft of working screen print and embroidery equipment.",
    "canon": "https://www.flyovercon.ink/location",
    "schema": [
      "[{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", \"name\": \"Flyover Con\", \"url\": \"https://www.flyovercon.ink\", \"logo\": \"https://www.flyovercon.ink/assets/img/logo-512.png\", \"sameAs\": [\"https://www.instagram.com/flyover_con/\", \"https://www.facebook.com/profile.php?id=61556233233152\"], \"parentOrganization\": {\"@type\": \"Organization\", \"name\": \"P&M Apparel\", \"url\": \"https://www.pmapparel.com\"}}, {\"@context\": \"https://schema.org\", \"@type\": \"BreadcrumbList\", \"itemListElement\": [{\"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.flyovercon.ink/\"}, {\"@type\": \"ListItem\", \"position\": 2, \"name\": \"Location\", \"item\": \"https://www.flyovercon.ink/location\"}]}, {\"@context\": \"https://schema.org\", \"@type\": \"Place\", \"name\": \"P&M Apparel\", \"address\": {\"@type\": \"PostalAddress\", \"streetAddress\": \"1100 S 5th St\", \"addressLocality\": \"Polk City\", \"addressRegion\": \"IA\", \"postalCode\": \"50226\", \"addressCountry\": \"US\"}, \"geo\": {\"@type\": \"GeoCoordinates\", \"latitude\": 41.763743, \"longitude\": -93.719835}}]"
    ],
    "main": f"\n\n<section class=\"hero\" style=\"padding:56px 0;\">\n  <div class=\"container hero__inner\">\n    <div class=\"hero__eyebrow\">The Venue</div>\n    <h1 style=\"font-size:clamp(2.2rem,5vw,3.4rem);\">P&amp;M Apparel</h1>\n    <p class=\"hero__lead\">Flyover Con takes place inside P&amp;M Apparel's production facility, built in 2020 and intentionally designed to bring people, process, and production together in one open, transparent space.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"container location-grid\">\n    <div>\n      <div class=\"map-embed\">\n        <iframe src=\"https://maps.google.com/maps?q=1100+S+5th+St,+Polk City,+IA+50226,+USA&z=16&output=embed\" loading=\"lazy\" title=\"Map to P&amp;M Apparel, 1100 S 5th St, Polk City, IA 50226\"></iframe>\n      </div>\n      <div class=\"prose\" style=\"margin-top:28px;\">\n        <p>With more than 8,000 square feet, the shop houses all sales, production, and fulfillment operations under one roof: multiple Anatol automatic presses, an Anatol manual press, a custom-built live screen printing press, an Anatol gas dryer, a Douthitt CTS, a Workhorse LED exposure table, ZSK and Barudan embroidery machines, Stahls Hotronix and MEM heat presses, and in-house digital and prototyping equipment. Every piece is visible, accessible, and actively used during the event.</p>\n        <p>Flyover Con doesn't happen on a stage or inside a conference hall. It's embedded directly into the shop floor. Attendees walk the same paths as the production team, stand next to presses, and watch garments move through the process end to end.</p>\n        <p>Hosting it in our own space is intentional. It reflects a commitment to transparency and a willingness to open the doors fully, even to potential competitors, sharing real systems, real decisions, and real lessons learned.</p>\n        <div class=\"photo-single\">\n          <img src=\"/assets/img/event/foc26-005.jpg\" alt=\"Attendees seated on the Flyover Con shop floor during a session\" loading=\"lazy\">\n        </div>\n      </div>\n    </div>\n    <aside>\n      <div class=\"plaque\" style=\"width:100%;margin-bottom:24px;\">\n        <p class=\"plaque__text\" style=\"font-size:0.95rem;\">1100 S 5th St, Polk City, IA 50226</p>\n      </div>\n      <h3 style=\"font-size:1.1rem;\">Getting Here</h3>\n      <div class=\"getting-here\">\n        <div class=\"getting-here__item\">\n          <div class=\"getting-here__icon\">\u2708</div>\n          <div><strong>By Plane</strong><p style=\"color:var(--grey);margin:2px 0 0;\">Des Moines International Airport (DSM). Nonstop flights from many major U.S. cities, about a 30-minute drive to Polk City.</p></div>\n        </div>\n        <div class=\"getting-here__item\">\n          <div class=\"getting-here__icon\">\u2192</div>\n          <div><strong>By Car</strong><p style=\"color:var(--grey);margin:2px 0 0;\">About 10 miles west of I-35, accessible via Highway 415. An easy drive from Des Moines and the surrounding metro.</p></div>\n        </div>\n      </div>\n      <h3 style=\"font-size:1.1rem;margin-top:32px;\">Need Somewhere to Stay?</h3>\n      <div class=\"hotel\"><h4>Qube Hotel</h4><p>1.3 miles from venue</p><p>300 Boulder Pointe, Polk City, IA 50226</p><p>(515) 984-3092</p></div>\n<div class=\"hotel\"><h4>Tru by Hilton Grimes Des Moines</h4><p>7 miles from venue</p><p>701 NE Gateway Dr, Grimes, IA 50111</p><p>(515) 608-8784</p></div>\n    </aside>\n  </div>\n</section>\n\n<section id=\"updates\" class=\"section--navy\">\n  <div class=\"container\">\n    <div class=\"block-grid\">\n      <div class=\"block block--gold\" style=\"grid-column:1 / -1;text-align:left;\">\n        <span class=\"section-head__eyebrow\" style=\"color:var(--navy-deep);opacity:0.7;\">Status: FOC27, April 16&ndash;17, 2027</span>\n        <h2 style=\"color:var(--navy-deep);\">FOC27 is April 16 and 17, 2027.</h2>\n        <p style=\"max-width:60ch;\">Registration isn't open yet. FOC26 sold out at 75 and FOC27 caps at the same number, so this list is the fastest way to hear when it opens.</p>\n        <div style=\"display:flex;gap:16px;flex-wrap:wrap;margin-top:20px;\">\n          <a class=\"btn btn--outline-navy\" href=\"{NOTIFY_URL}\">Get Notified for FOC27</a>\n          <a class=\"btn btn--outline-navy\" href=\"https://www.instagram.com/flyover_con/\" rel=\"noopener\" target=\"_blank\">Follow on Instagram</a>\n        </div>\n      </div>\n    </div>\n  </div>\n</section>\n\n"
  }
}

# ------------------------------------------------- FOC27 sponsor and speak
# These two pages are built as plain strings with __TOKEN__ placeholders
# rather than escaped f-strings, because both carry inline <script> blocks and
# f-string braces and JavaScript braces do not coexist quietly.

# Where FOC26 attendees came from. Widths are percentages of the Iowa bar.
GEOGRAPHY = [
    ("Iowa",  37, 100, True),
    ("Neb.",   7,  19, False),
    ("Wis.",   7,  19, False),
    ("S.D.",   6,  16, False),
    ("Other", 18,  49, False),
]
GEO_OTHER = "18 across MO, MN, MI, KS, NV, IL, CO, MS, SC, TX, WA, VA, AZ"


def geo_bars(title):
    rows = []
    for label, count, width, dark in GEOGRAPHY:
        fill = "geo__fill geo__fill--dark" if dark else "geo__fill"
        val = GEO_OTHER if label == "Other" else str(count)
        rows.append(
            f'      <div class="geo__row">\n'
            f'        <span class="geo__label">{label}</span>\n'
            f'        <span class="geo__bar"><span class="{fill}" style="width:{width}%;"></span></span>\n'
            f'        <span class="geo__val">{val}</span>\n'
            f'      </div>'
        )
    return ('    <div class="geo">\n'
            f'      <p class="geo__title">{title}</p>\n'
            + "\n".join(rows) + "\n    </div>")


def tier_blocks():
    out = []
    for slug, name, avail, price, lines in SPONSOR_TIERS:
        items = "\n".join(f'          <li>{l}</li>' for l in lines)
        out.append(
            f'      <div class="tier tier--{slug}">\n'
            f'        <div class="tier__head">\n'
            f'          <h3 class="tier__name">{name}<span class="tier__avail">{avail}</span></h3>\n'
            f'          <span class="tier__price">{price}</span>\n'
            f'        </div>\n'
            + (f'        <p class="tier__claimed"><span>FOC27 presented by</span>'
               f'<img src="{SPONSOR_WORDMARK}" alt="{PRESENTING_SPONSOR}" width="150" height="30"></p>\n'
               if slug == "presenting" else "")
            + f'        <ul class="tier__list">\n{items}\n        </ul>\n'
            f'      </div>'
        )
    return '    <div class="tier-stack">\n' + "\n".join(out) + "\n    </div>"


# (time, label, marked) for each day. marked rows render gold.
def sched_mini(day_one, day_two, closer="Doors close, shop goes back to work"):
    def col(day_label, rows, tail=None):
        body = []
        for time, label, mark in rows:
            cls = "sched-mini__row sched-mini__row--mark" if mark else "sched-mini__row"
            body.append(
                f'        <div class="{cls}">\n'
                f'          <span class="sched-mini__time">{time}</span>\n'
                f'          <span class="sched-mini__label">{label}</span>\n'
                f'        </div>'
            )
        if tail:
            body.append(
                '        <div class="sched-mini__row sched-mini__row--end">\n'
                '          <span class="sched-mini__time"></span>\n'
                f'          <span class="sched-mini__label">{tail}</span>\n'
                '        </div>'
            )
        return (f'      <div>\n        <p class="sched-mini__day">{day_label}</p>\n'
                + "\n".join(body) + "\n      </div>")
    return ('    <div class="sched-mini">\n'
            + col("Day One", day_one) + "\n"
            + col("Day Two", day_two, closer) + "\n    </div>")


SPONSOR_DAY_ONE = [
    ("8:00",  "Breakfast, registration, live decorating", False),
    ("9:00",  "Gate A and Gate B sessions", False),
    ("10:30", "Gate A and Gate B sessions", False),
    ("11:45", "Lunch, provided by [your company]", True),
    ("1:00",  "Gate A and Gate B sessions", False),
    ("2:15",  "Gate A and Gate B sessions", False),
    ("3:45",  "Panels, both gates", False),
    ("5:00",  "Happy hour and trivia, presented by [your company]", True),
]
SPONSOR_DAY_TWO = [
    ("8:00",  "Breakfast, registration, live decorating", False),
    ("9:00",  "Gate A and Gate B sessions", False),
    ("10:30", "Live decorating, shop wide", False),
    ("11:45", "Lunch, provided by [your company]", True),
    ("1:00",  "Gate A and Gate B sessions", False),
    ("2:15",  "Gate A and Gate B sessions", False),
    ("3:45",  "Decorator round table, whole room", False),
]
SPEAK_DAY_ONE = [
    ("8:00",  "Breakfast, registration, live decorating", False),
    ("9:00",  "Gate A and Gate B sessions", True),
    ("10:30", "Gate A and Gate B sessions", True),
    ("11:45", "Lunch, sponsor recognition", False),
    ("1:00",  "Gate A and Gate B sessions", True),
    ("2:15",  "Gate A and Gate B sessions", True),
    ("3:45",  "Panels, both gates", True),
    ("5:00",  "Happy hour and trivia", False),
]
SPEAK_DAY_TWO = [
    ("8:00",  "Breakfast, registration, live decorating", False),
    ("9:00",  "Gate A and Gate B sessions", True),
    ("10:30", "Live decorating, shop wide", True),
    ("11:45", "Lunch, sponsor recognition", False),
    ("1:00",  "Gate A and Gate B sessions", True),
    ("2:15",  "Gate A and Gate B sessions", True),
    ("3:45",  "Decorator round table, whole room", False),
]

SPONSOR_MAIN = """

<section class="hero" style="padding:56px 0;">
  <div class="container hero__inner">
    <div class="hero__eyebrow">Partnership Opportunities</div>
    <h1 style="font-size:clamp(2.2rem,5vw,3.4rem);">Sponsor Flyover Con.</h1>
    <p class="hero__lead">FOC27 is April 16 and 17, 2027, on the working floor at P&amp;M Apparel in Polk City, Iowa. Seventy five decorators, hard cap, two days, no exhibit hall to compete with. Nothing is locked in for 2027 yet.</p>
    <div class="hero__actions">
      <a class="btn btn--gold" href="#levels">See the Levels</a>
      <a class="btn btn--outline" href="#inquire">Start a Conversation</a>
    </div>
  </div>
</section>

<section class="section--tight">
  <div class="container">
    <div class="stat-strip">
      <div class="stat"><span class="stat__num">75</span><span class="stat__label">Seats, Hard Cap</span></div>
      <div class="stat"><span class="stat__num">17</span><span class="stat__label">States in 2026</span></div>
      <div class="stat"><span class="stat__num">9.6</span><span class="stat__label">Avg Attendee Rating</span></div>
      <div class="stat"><span class="stat__num">100%</span><span class="stat__label">Made Connections They Plan to Keep</span></div>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">What It Is</span>
      <h2>Not a trade show. A working shop floor.</h2>
      <p>Flyover Con is a hands on conference for screen printers, embroiderers and apparel decorators, held inside a working production facility instead of a convention hall. Everything happens on the floor at P&amp;M Apparel: 8,220 square feet of active screen printing, embroidery, heat transfer, art and fulfillment. Presses run. Machines are open. When a speaker says &ldquo;come over here, I will show you,&rdquo; they can.</p>
    </div>
    <div class="block-grid">
      <div class="block block--navy block--half">
        <h3 style="font-size:1.05rem;">Traditional conference</h3>
        <p>Come hear experts talk about the industry.</p>
      </div>
      <div class="block block--gold block--half">
        <h3 style="font-size:1.05rem;">Flyover Con</h3>
        <p>Come into the shop and see how the industry actually works.</p>
      </div>
    </div>
  </div>
</section>

<section class="section--navy">
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">The Record</span>
      <h2>2026 by the numbers.</h2>
      <p>Year two results, from registration records and post event attendee surveys. 2024 was our inaugural year, with 40 to 50 attendees and a plan to run every other year. 2026 sold out at 75 and the response was strong enough that we changed our minds. Flyover Con is now annual, and 2027 is our third event and our first consecutive year.</p>
    </div>
__GEO_SPONSOR__
    <div class="block-grid" style="margin-top:32px;">
      <div class="block block--gold" style="grid-column:1 / -1;text-align:left;">
        <span class="section-head__eyebrow" style="color:var(--navy-deep);opacity:0.7;">We are capping 2027 at 75 people</span>
        <p style="max-width:70ch;">We could sell more seats. We are not going to. 8,220 square feet only works as a classroom at this size, and our attendees told us plainly not to grow it. That cap is what makes the room valuable: a sponsor is not competing with an exhibit hall for attention, and there is nowhere for an attendee to hide from a good conversation.</p>
      </div>
    </div>
    <p style="max-width:75ch;margin-top:28px;color:var(--white);opacity:0.85;">Flyover Con is anchored in the Des Moines metro and pulls across the upper Midwest, the exact corridor most national trade shows reach last. These are working shop owners and decision makers who do not routinely travel to Long Beach or Atlantic City. For many of them, this was the only industry education they attended all year.</p>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">From The Sponsors</span>
      <h2>What sponsors actually said.</h2>
      <p>Every 2026 sponsor and speaker got the same survey the attendees did. Every responding sponsor and speaker rated the event a ten out of ten, all of them said yes to coming back in 2027, and all of them rated attendee interaction very good.</p>
    </div>
    <div class="testimonial-strip">
      <div class="testimonial">
        <p class="testimonial__quote">I loved how interactive it was. People were engaged and asked questions during the session, chatted after, and even emailed me.</p>
        <div class="testimonial__source">
          <p class="testimonial__name">Meghan Brazzelle</p>
          <p class="testimonial__shop">Chipply</p>
        </div>
      </div>
      <div class="testimonial">
        <p class="testimonial__quote">I&rsquo;m big on education and networking. Proud to be a part of it and will sponsor again in the future if given the opportunity.</p>
        <div class="testimonial__source">
          <p class="testimonial__name">Spencer Chernoff</p>
          <p class="testimonial__shop">Limitless Transfers</p>
        </div>
      </div>
      <div class="testimonial">
        <p class="testimonial__quote">The most valuable part was the interaction with print homies. I liked the location.</p>
        <div class="testimonial__source">
          <p class="testimonial__name">Matt Richardson</p>
          <p class="testimonial__shop">Atonal Headwear</p>
        </div>
      </div>
    </div>
    <div class="block block--sky" style="margin-top:32px;text-align:left;">
      <span class="section-head__eyebrow" style="color:var(--navy-deep);opacity:0.7;">What they asked us to change</span>
      <p style="max-width:70ch;">Two sponsors told us they wanted more visible presence than they got, and both suggested the same fix: let sponsors put something in every attendee&rsquo;s bag instead of building a booth nobody stops at. That is now in every level, starting at Silver.</p>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">The Shape Of A Day</span>
      <h2>Where your name actually shows up.</h2>
      <p>The 2026 schedule, for reference. Two tracks run at once, Gate A and Gate B, so attendees build the day they want. Gold rows are the sponsored moments.</p>
    </div>
__SCHED_SPONSOR__
    <p style="max-width:70ch;margin-top:28px;color:var(--grey);">Sixteen sessions and nineteen speakers ran in 2026. Presenting and Gold sponsors speak inside this grid, not around it. The 2027 schedule is still being built, so if there is a subject your team teaches well, <a href="__SPEAK_URL__" style="color:var(--navy);font-weight:600;">tell us early</a> and we will make room for it.</p>
  </div>
</section>

<section id="levels" class="section--navy">
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">Boarding Groups</span>
      <h2>Sponsor levels.</h2>
    </div>
    <div class="block block--sky" style="text-align:left;margin-bottom:28px;">
      <span class="section-head__eyebrow" style="color:var(--navy-deep);opacity:0.7;">Every sponsor, every level</span>
      <p style="max-width:70ch;">Full access to both days for your team and all meals. Nobody sits behind a table. You are in the room the whole time, and that is the point.</p>
    </div>
__TIERS__
    <div class="block block--navy" style="border:2px solid rgba(255,255,255,0.15);margin-top:24px;text-align:left;">
      <span class="section-head__eyebrow" style="color:var(--gold);">A note on sponsor sessions</span>
      <p style="max-width:70ch;">If your sponsorship includes speaking time, we will ask you to teach a task rather than introduce a product. This room is technical and already uses most of the tools on the market. They want to watch you do the thing and take the steps home. We will help you shape it.</p>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">Also Open</span>
      <h2>Pieces you can put your name on.</h2>
      <p>Beyond the three levels, individual moments and in kind support are available. Ask about any of these and we will tell you what is still unclaimed.</p>
    </div>
    <div class="sponsor-strip">
      <span class="sponsor-chip">In Kind</span>
      <span class="sponsor-chip">Happy Hour</span>
      <span class="sponsor-chip">Day 1 Lunch</span>
      <span class="sponsor-chip">Day 2 Lunch</span>
      <span class="sponsor-chip">Breakfast</span>
      <span class="sponsor-chip">Swag Bags</span>
    </div>
  </div>
</section>

<section id="inquire">
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">Next Step</span>
      <h2>Let&rsquo;s talk.</h2>
      <p>Flyover Con exists because of companies that believe in investing in people, education and the long term strength of the decorated apparel industry. Your support is what keeps registration at a number a two person shop in rural Nebraska can say yes to. It pays for the food, the video, the venue and the hours our team spends off the production floor. And it is what lets us keep saying no to turning this into a sales event.</p>
    </div>

    <div class="plaque" style="margin-bottom:32px;">
      <p class="plaque__text">Commitments requested by __SPONSOR_DEADLINE__</p>
    </div>

    <div class="signup signup--wide" id="sp-form">
      <div class="form-grid">
        <div class="signup__field">
          <label for="sp-company">Company</label>
          <input type="text" id="sp-company" name="company" autocomplete="organization" required>
        </div>
        <div class="signup__field">
          <label for="sp-name">Your name</label>
          <input type="text" id="sp-name" name="name" autocomplete="name" required>
        </div>
        <div class="signup__field">
          <label for="sp-email">Email</label>
          <input type="email" id="sp-email" name="email" autocomplete="email" required>
        </div>
        <div class="signup__field">
          <label for="sp-phone">Phone</label>
          <input type="tel" id="sp-phone" name="phone" autocomplete="tel">
        </div>
        <div class="signup__field signup__field--full">
          <label for="sp-level">Level you are considering</label>
          <select id="sp-level" name="level">
            <option value="">Not sure yet, let&rsquo;s talk</option>
            <option value="Gold">Gold</option>
            <option value="Silver">Silver</option>
            <option value="In kind">In kind</option>
            <option value="A single moment (lunch, happy hour, breakfast)">A single moment (lunch, happy hour, breakfast)</option>
          </select>
        </div>
        <div class="signup__field signup__field--full">
          <label for="sp-notes">Anything else</label>
          <textarea id="sp-notes" name="notes"></textarea>
          <p class="signup__hint">If there is a subject your team teaches well, say so here. Session time is not guaranteed by level, but it helps us build the grid.</p>
        </div>
        <div class="signup__hp" aria-hidden="true">
          <label for="sp-gotcha">Leave this empty</label>
          <input type="text" id="sp-gotcha" name="_gotcha" tabindex="-1" autocomplete="off">
        </div>
      </div>
      <button class="btn btn--gold" type="button" id="sp-submit">Send It Over</button>
      <p class="signup__msg" id="sp-msg" role="status" aria-live="polite"></p>
      <p class="signup__note">This is not a commitment and nothing is invoiced from this form. It starts a conversation with Ryan, usually the same day. Prefer email? <a href="mailto:ryan@flyovercon.ink" style="color:var(--navy);font-weight:600;">ryan@flyovercon.ink</a> or (515) 984-7740.</p>
    </div>

    <div class="signup__done" id="sp-done" hidden>
      <h2>Got it.</h2>
      <p>Ryan will follow up personally, usually within a day. If it is urgent, call (515) 984-7740.</p>
    </div>
  </div>
</section>

<script>
(function(){
  var btn  = document.getElementById('sp-submit');
  var msg  = document.getElementById('sp-msg');
  var box  = document.getElementById('sp-form');
  var done = document.getElementById('sp-done');
  var EMAIL = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/;

  function val(id){ return document.getElementById(id).value.trim(); }
  function err(text, focusId){
    msg.className = 'signup__msg signup__msg--err';
    msg.textContent = text;
    if(focusId) document.getElementById(focusId).focus();
  }

  btn.addEventListener('click', function(){
    var company = val('sp-company'), name = val('sp-name'), email = val('sp-email');
    msg.className = 'signup__msg';

    if(!company){ err('Please add your company name.', 'sp-company'); return; }
    if(!name){ err('Please add your name.', 'sp-name'); return; }
    if(!EMAIL.test(email)){ err('That email address does not look right.', 'sp-email'); return; }

    btn.disabled = true;
    msg.textContent = 'Sending.';

    fetch('__SPONSOR_ENDPOINT__', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        company: company,
        name: name,
        email: email,
        phone: val('sp-phone'),
        level: val('sp-level'),
        notes: val('sp-notes'),
        _gotcha: val('sp-gotcha')
      })
    }).then(function(r){ return r.json(); }).then(function(d){
      if(!d || d.ok !== true) throw new Error('failed');
      box.hidden = true;
      done.hidden = false;
      done.scrollIntoView({block:'center'});
    }).catch(function(){
      btn.disabled = false;
      err('That did not send. Email ryan@flyovercon.ink and we will pick it up from there.');
    });
  });
})();
</script>

"""

SPEAK_MAIN = """

<section class="hero" style="padding:56px 0;">
  <div class="container hero__inner">
    <div class="hero__eyebrow">Teaching Opportunities</div>
    <h1 style="font-size:clamp(2.2rem,5vw,3.4rem);">Call for speakers.</h1>
    <p class="hero__lead">FOC27 is April 16 and 17, 2027, on the working floor at P&amp;M Apparel in Polk City, Iowa. Seventy five decorators, two tracks, no stage and no ballroom. Proposals close __PROPOSALS_CLOSE__.</p>
    <div class="hero__actions">
      <a class="btn btn--gold" href="#propose">Submit a Session</a>
      <a class="btn btn--outline" href="#what-works">What Works Here</a>
    </div>
  </div>
</section>

<section class="section--tight">
  <div class="container">
    <div class="stat-strip">
      <div class="stat"><span class="stat__num">16</span><span class="stat__label">Sessions Across Two Days</span></div>
      <div class="stat"><span class="stat__num">19</span><span class="stat__label">Speakers on the Floor in 2026</span></div>
      <div class="stat"><span class="stat__num">75</span><span class="stat__label">Decorators, at Capacity</span></div>
      <div class="stat"><span class="stat__num">9.6</span><span class="stat__label">Avg Attendee Rating</span></div>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">What You Would Be Speaking At</span>
      <h2>Not a trade show. A working shop floor.</h2>
      <p>Everything happens on the floor at P&amp;M Apparel: 8,220 square feet of active screen printing, embroidery, heat transfer, art and fulfillment. Presses run. Machines are open. There is no stage, no green room and no ballroom. If you say &ldquo;come over here, I will show you,&rdquo; you can walk fifteen feet and show them.</p>
    </div>
    <div class="block-grid">
      <div class="block block--navy block--half">
        <h3 style="font-size:1.05rem;">Traditional conference</h3>
        <p>Stand at the front and present to the industry.</p>
      </div>
      <div class="block block--gold block--half">
        <h3 style="font-size:1.05rem;">Flyover Con</h3>
        <p>Stand at the machine and show people how to do the thing.</p>
      </div>
    </div>
  </div>
</section>

<section class="section--navy">
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">The Room</span>
      <h2>Who you would be teaching.</h2>
      <p>These are working shop owners and operators, mostly small to mid size, who make the buying and process decisions themselves. They do not routinely travel to Long Beach or Atlantic City. For many of them this was the only industry education they attended all year, so they show up ready to use what they hear on Monday.</p>
    </div>
__GEO_SPEAK__
    <p style="max-width:75ch;margin-top:28px;color:var(--white);opacity:0.85;">It is also a technical room that already owns most of the tools on the market. If something you say does not track with how their shop actually runs, they will tell you in the moment, and that conversation is usually the best part of the session.</p>
  </div>
</section>

<section id="what-works">
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">What Works Here</span>
      <h2>Teach a task, not a product.</h2>
      <p>This is the only rule we are strict about. This room is technical and already uses most of the tools on the market. They want to watch you do the thing and take the steps home. If your session has a product in it, that is fine, put it to work in front of them. Just do not spend forty minutes on a capabilities deck.</p>
    </div>
    <div class="card-grid">
      <div class="card">
        <span class="tag">Gate A or Gate B &middot; 60 to 75 min</span>
        <h3 style="margin-top:14px;">Session</h3>
        <p>The core format. Two tracks run at once, so you are teaching roughly half the room and they chose you over the other option.</p>
      </div>
      <div class="card">
        <span class="tag">Shop wide &middot; At the equipment</span>
        <h3 style="margin-top:14px;">Live Demo</h3>
        <p>Run it on our presses, embroidery machines, heat presses or art stations. Best format we have, and the one attendees ask for most.</p>
      </div>
      <div class="card">
        <span class="tag">3:45 &middot; Both gates</span>
        <h3 style="margin-top:14px;">Panel Seat</h3>
        <p>You bring a point of view and take live questions. Good fit if you have the experience but do not want to build a full session.</p>
      </div>
    </div>
    <div class="split" style="margin-top:48px;">
      <div>
        <p class="split__head">What lands</p>
        <ul class="split__list">
          <li>One narrow problem, taken all the way to the end</li>
          <li>Real numbers from your own shop, including the ugly ones</li>
          <li>Walking the room to a machine mid session</li>
          <li>Handouts, checklists or files people leave with</li>
          <li>Saying &ldquo;here is what we got wrong first&rdquo;</li>
        </ul>
      </div>
      <div>
        <p class="split__head">What does not</p>
        <ul class="split__list split__list--muted">
          <li>Company history and capabilities overviews</li>
          <li>Broad trend talks with no steps attached</li>
          <li>Slides read start to finish with questions held to the end</li>
          <li>Anything that assumes a 30 person staff</li>
          <li>Pricing your product from the front of the room</li>
        </ul>
      </div>
    </div>
    <div class="testimonial-strip" style="margin-top:48px;">
      <div class="testimonial">
        <p class="testimonial__quote">Being able to talk to others, walk around the shop and ask questions. Learn from a larger shop as to how they go about their production and work flows.</p>
        <div class="testimonial__source">
          <p class="testimonial__name">Hussain Ali</p>
          <p class="testimonial__shop">Impressive Promotional Products</p>
        </div>
      </div>
      <div class="testimonial">
        <p class="testimonial__quote">I learned valuable resources to utilize that I had not heard of before with credible sources and vendors without feeling too sales-y or pushy.</p>
        <div class="testimonial__source">
          <p class="testimonial__name">Emily Hassing</p>
          <p class="testimonial__shop">Sparkling Image</p>
        </div>
      </div>
      <div class="testimonial">
        <p class="testimonial__quote">I have been to Long Beach and Print Hustlers and I feel almost intimidated with so many people. This was perfect.</p>
        <div class="testimonial__source">
          <p class="testimonial__name">Peter Hoff</p>
          <p class="testimonial__shop">A&amp;P Graphics</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">The Shape Of A Day</span>
      <h2>Where your session fits.</h2>
      <p>The 2026 schedule, for reference. Two tracks run at once, Gate A and Gate B, so attendees build the day they want. Gold rows are the speaking slots.</p>
    </div>
__SCHED_SPEAK__
    <p style="max-width:70ch;margin-top:28px;color:var(--grey);">Sixteen sessions and nineteen speakers ran in 2026. The 2027 grid is still being built and will shift. Day two is being front loaded so it ends earlier for the people driving four hours home, which means the strongest Saturday content moves up, not down.</p>
    <div class="block block--sky" style="margin-top:28px;text-align:left;">
      <span class="section-head__eyebrow" style="color:var(--navy-deep);opacity:0.7;">You are here both days</span>
      <p style="max-width:70ch;">Speakers stay for the whole event, not just their slot. That is the deal and it is the reason the hallway conversations work. You will be asked questions at breakfast, at lunch and next to a press, and those conversations do more for you than the session does.</p>
    </div>
  </div>
</section>

<section id="propose" class="section--navy">
  <div class="container">
    <div class="section-head">
      <span class="section-head__eyebrow">Next Step</span>
      <h2>Tell us what you want to teach.</h2>
      <p>We read everything and we answer everyone by __SPEAKERS_NOTIFIED__. If the idea is close but not there yet, we will tell you what would get it over the line. First time speakers are genuinely welcome.</p>
    </div>
    <ul class="dates" style="max-width:46rem;margin-bottom:40px;color:var(--white);">
      <li><span class="dates__when" style="color:var(--gold);">__PROPOSALS_CLOSE__</span><span class="dates__what" style="color:rgba(255,255,255,0.75);">Proposals close</span></li>
      <li><span class="dates__when" style="color:var(--gold);">__SPEAKERS_NOTIFIED__</span><span class="dates__what" style="color:rgba(255,255,255,0.75);">Speakers notified and the program locks</span></li>
      <li><span class="dates__when" style="color:var(--gold);">__MATERIALS_DUE__</span><span class="dates__what" style="color:rgba(255,255,255,0.75);">Titles, descriptions and bios due for the public agenda</span></li>
      <li><span class="dates__when" style="color:var(--gold);">April 16 and 17, 2027</span><span class="dates__what" style="color:var(--white);">Flyover Con 2027</span></li>
    </ul>
  </div>
</section>

<section>
  <div class="container">
    <div class="signup signup--wide" id="sk-form">
      <div class="form-grid">
        <div class="signup__field">
          <label for="sk-name">Your name</label>
          <input type="text" id="sk-name" name="name" autocomplete="name" required>
        </div>
        <div class="signup__field">
          <label for="sk-shop">Shop or company</label>
          <input type="text" id="sk-shop" name="shop" autocomplete="organization">
        </div>
        <div class="signup__field">
          <label for="sk-role">What you do there</label>
          <input type="text" id="sk-role" name="role" autocomplete="organization-title">
        </div>
        <div class="signup__field">
          <label for="sk-email">Email</label>
          <input type="email" id="sk-email" name="email" autocomplete="email" required>
        </div>
        <div class="signup__field">
          <label for="sk-phone">Phone</label>
          <input type="tel" id="sk-phone" name="phone" autocomplete="tel">
        </div>
        <div class="signup__field">
          <label for="sk-format">Format you want</label>
          <select id="sk-format" name="format">
            <option value="Session">Session, 60 to 75 minutes</option>
            <option value="Live demo">Live demo at the equipment</option>
            <option value="Panel seat">Panel seat</option>
            <option value="Open to any">Open to whatever fits</option>
          </select>
        </div>
        <div class="signup__field signup__field--full">
          <label for="sk-title">Working session title</label>
          <input type="text" id="sk-title" name="session_title" required>
        </div>
        <div class="signup__field signup__field--full">
          <label for="sk-takeaway">What an attendee walks out able to do</label>
          <textarea id="sk-takeaway" name="takeaway" required></textarea>
          <p class="signup__hint">Three or four sentences is plenty. This is the part we actually read first.</p>
        </div>
        <div class="signup__field signup__field--full">
          <label for="sk-equipment">What you need from the floor</label>
          <input type="text" id="sk-equipment" name="equipment">
          <p class="signup__hint">Press, embroidery machine, heat press, art station, none of it.</p>
        </div>
        <div class="signup__field signup__field--full">
          <label for="sk-sample">Where we can see you teach, present or talk shop</label>
          <input type="url" id="sk-sample" name="sample" placeholder="https://">
          <p class="signup__hint">A video, a podcast or a past session is plenty. Not required.</p>
        </div>
        <div class="signup__field signup__field--full">
          <label for="sk-notes">Anything else</label>
          <textarea id="sk-notes" name="notes"></textarea>
        </div>
        <div class="signup__hp" aria-hidden="true">
          <label for="sk-gotcha">Leave this empty</label>
          <input type="text" id="sk-gotcha" name="_gotcha" tabindex="-1" autocomplete="off">
        </div>
      </div>
      <button class="btn btn--gold" type="button" id="sk-submit">Send the Proposal</button>
      <p class="signup__msg" id="sk-msg" role="status" aria-live="polite"></p>
      <p class="signup__note">Speaking at Flyover Con is not a sponsorship and does not require one. If you would rather talk it through first, email <a href="mailto:ryan@flyovercon.ink" style="color:var(--navy);font-weight:600;">ryan@flyovercon.ink</a> or call (515) 984-7740.</p>
    </div>

    <div class="signup__done" id="sk-done" hidden>
      <h2>Proposal received.</h2>
      <p>We read every one. You will hear back by __SPEAKERS_NOTIFIED__ either way, and if the idea needs a tweak we will tell you what would get it over the line.</p>
    </div>
  </div>
</section>

<script>
(function(){
  var btn  = document.getElementById('sk-submit');
  var msg  = document.getElementById('sk-msg');
  var box  = document.getElementById('sk-form');
  var done = document.getElementById('sk-done');
  var EMAIL = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/;

  function val(id){ return document.getElementById(id).value.trim(); }
  function err(text, focusId){
    msg.className = 'signup__msg signup__msg--err';
    msg.textContent = text;
    if(focusId) document.getElementById(focusId).focus();
  }

  btn.addEventListener('click', function(){
    var name = val('sk-name'), email = val('sk-email');
    var title = val('sk-title'), takeaway = val('sk-takeaway');
    msg.className = 'signup__msg';

    if(!name){ err('Please add your name.', 'sk-name'); return; }
    if(!EMAIL.test(email)){ err('That email address does not look right.', 'sk-email'); return; }
    if(!title){ err('Give it a working title. It does not have to be the final one.', 'sk-title'); return; }
    if(!takeaway){ err('Tell us what an attendee walks out able to do.', 'sk-takeaway'); return; }

    btn.disabled = true;
    msg.textContent = 'Sending.';

    fetch('__SPEAK_ENDPOINT__', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        name: name,
        shop: val('sk-shop'),
        role: val('sk-role'),
        email: email,
        phone: val('sk-phone'),
        session_title: title,
        takeaway: takeaway,
        format: val('sk-format'),
        equipment: val('sk-equipment'),
        sample: val('sk-sample'),
        notes: val('sk-notes'),
        _gotcha: val('sk-gotcha')
      })
    }).then(function(r){ return r.json(); }).then(function(d){
      if(!d || d.ok !== true) throw new Error('failed');
      box.hidden = true;
      done.hidden = false;
      done.scrollIntoView({block:'center'});
    }).catch(function(){
      btn.disabled = false;
      err('That did not send. Email ryan@flyovercon.ink and we will pick it up from there.');
    });
  });
})();
</script>

"""


def _fill(body, extra=None):
    swap = {
        "__SPONSOR_DEADLINE__": SPONSOR_DEADLINE,
        "__PROPOSALS_CLOSE__": PROPOSALS_CLOSE,
        "__SPEAKERS_NOTIFIED__": SPEAKERS_NOTIFIED,
        "__MATERIALS_DUE__": MATERIALS_DUE,
        "__SPONSOR_ENDPOINT__": SPONSOR_ENDPOINT,
        "__SPEAK_ENDPOINT__": SPEAK_ENDPOINT,
        "__SPONSOR_URL__": SPONSOR_URL,
        "__SPEAK_URL__": SPEAK_URL,
    }
    swap.update(extra or {})
    for k, v in swap.items():
        body = body.replace(k, v)
    if "__" in re.sub(r"__SPEAKERS_20\d\d__", "", body):
        leftover = re.findall(r"__[A-Z_]+__", body)
        if leftover:
            sys.exit("build: unfilled token(s) %s" % sorted(set(leftover)))
    return body


_ORG_SCHEMA = ('{"@context": "https://schema.org", "@type": "Organization", "name": "Flyover Con", '
               '"url": "https://www.flyovercon.ink", "logo": "https://www.flyovercon.ink/assets/img/logo-512.png", '
               '"sameAs": ["https://www.instagram.com/flyover_con/", '
               '"https://www.facebook.com/profile.php?id=61556233233152"], '
               '"parentOrganization": {"@type": "Organization", "name": "P&M Apparel", '
               '"url": "https://www.pmapparel.com"}}')


def _crumbs(name, path):
    return ('{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": '
            '[{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.flyovercon.ink/"}, '
            '{"@type": "ListItem", "position": 2, "name": "%s", "item": "https://www.flyovercon.ink%s"}]}'
            % (name, path))


_SPONSOR_FAQ = json.dumps({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": "What does it cost to sponsor Flyover Con?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Flyover Con 2027 has three sponsor levels: Silver at $1,000 (unlimited), Gold at $2,500 "
          "(three available) and Presenting at $7,000, which is claimed by " + PRESENTING_SPONSOR + " for 2027. Individual moments such as a "
          "lunch or the happy hour, and in kind support, are also available."}},
        {"@type": "Question", "name": "How many people will see my sponsorship?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Attendance is capped at 75 decorators. Flyover Con 2026 sold out at that number and drew "
          "attendees from 17 states, mostly working shop owners and operators across the upper Midwest."}},
        {"@type": "Question", "name": "Do sponsors get a booth?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "No. There are no vendor booths at Flyover Con. Sponsors attend both days as participants, "
          "eat with attendees and have materials in every attendee swag bag. Gold and Presenting "
          "sponsors also get time in front of the full room."}},
        {"@type": "Question", "name": "Can a sponsor speak at Flyover Con?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Yes, at the Gold and Presenting levels. Sponsor sessions have to teach a task rather than "
          "introduce a product. The room is technical and already uses most of the tools on the market."}},
        {"@type": "Question", "name": "When do sponsorship commitments need to be in?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Commitments are requested by January 15, 2027. Flyover Con 2027 takes place April 16 and 17, "
          "2027 at P&M Apparel in Polk City, Iowa."}},
    ],
})

_SPEAK_FAQ = json.dumps({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": "Who can speak at Flyover Con?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Anyone in decorated apparel with a task they can teach: shop owners, operators, art and "
          "production staff, and industry partners. First time speakers are welcome. Sessions must "
          "teach a task rather than introduce a product."}},
        {"@type": "Question", "name": "What speaking formats are available?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Three: a 60 to 75 minute session in one of the two tracks, a live demo at the equipment on "
          "the shop floor, or a panel seat."}},
        {"@type": "Question", "name": "Do speakers have to sponsor the event?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "No. Speaking at Flyover Con is not a sponsorship and does not require one."}},
        {"@type": "Question", "name": "When do speaker proposals close?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Proposals close %s. Speakers are notified by %s and session titles, descriptions and bios "
          "are due %s. Flyover Con 2027 runs April 16 and 17, 2027 in Polk City, Iowa."
          % (PROPOSALS_CLOSE, SPEAKERS_NOTIFIED, MATERIALS_DUE)}},
        {"@type": "Question", "name": "Do speakers attend the whole event?",
         "acceptedAnswer": {"@type": "Answer", "text":
          "Yes. Speakers stay for both days rather than just their slot, which is what makes the "
          "hallway and shop floor conversations work."}},
    ],
})

PAGES["sponsor"] = {
    "title": "Sponsor Flyover Con 2027 | Levels & Partnership",
    "desc": ("Sponsor FOC27, April 16 and 17, 2027 in Polk City, Iowa. Three levels, 75 capped "
             "attendees from 17 states, no vendor booths. Commitments requested by "
             + SPONSOR_DEADLINE + "."),
    "canon": "https://www.flyovercon.ink/sponsor",
    "schema": ["[" + _ORG_SCHEMA + ", " + _crumbs("Sponsor", "/sponsor") + ", " + _SPONSOR_FAQ + "]"],
    "main": _fill(SPONSOR_MAIN, {
        "__GEO_SPONSOR__": geo_bars("Arrivals &middot; Where 2026 attendees came from"),
        "__SCHED_SPONSOR__": sched_mini(SPONSOR_DAY_ONE, SPONSOR_DAY_TWO),
        "__TIERS__": tier_blocks(),
    }),
}

PAGES["speak"] = {
    "title": "Call for Speakers | Flyover Con 2027",
    "desc": ("Submit a session for FOC27, April 16 and 17, 2027 in Polk City, Iowa. Sessions, live "
             "demos and panel seats on a working shop floor. Proposals close " + PROPOSALS_CLOSE + "."),
    "canon": "https://www.flyovercon.ink/speak",
    "schema": ["[" + _ORG_SCHEMA + ", " + _crumbs("Call for Speakers", "/speak") + ", " + _SPEAK_FAQ + "]"],
    "main": _fill(SPEAK_MAIN, {
        "__GEO_SPEAK__": geo_bars("Arrivals &middot; Where 2026 attendees came from"),
        "__SCHED_SPEAK__": sched_mini(SPEAK_DAY_ONE, SPEAK_DAY_TWO),
    }),
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
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/img/favicon-192.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}/assets/img/event/foc26-hero-16x9.jpg">
<meta property="og:image:width" content="1600">
<meta property="og:image:height" content="900">
<meta name="twitter:image" content="{BASE}/assets/img/event/foc26-hero-16x9.jpg">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css">
{schema}
</head>
<body>
"""

def nav(key):
    items = ""
    for href, label in NAV:
        cur = ' aria-current="page"' if href == ("/" if key == "index" else "/" + key) else ""
        items += f'          <li><a href="{href}"{cur}>{label}</a></li>\n'
    return f"""
<header class="site-nav">
  <div class="site-nav__inner">
    <a class="site-nav__logo" href="/">
      <img src="{LOGO_BADGE}" alt="Flyover Con 2027" width="52" height="48">
      <span>Flyover Con</span>
    </a>
    <button class="site-nav__toggle" aria-expanded="false" aria-label="Toggle navigation menu">Menu</button>
    <ul class="site-nav__links">
{items}      <li><a class="site-nav__cta" href="{NOTIFY_URL}">Get Notified for FOC27</a></li>
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
        <img src="{LOGO_HORIZONTAL}" alt="Flyover Con 2027, presented by {PRESENTING_SPONSOR}" width="197" height="120">
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
            <li><a href="/about">About Flyover Con</a></li>
            <li><a href="/years-past">Years Past</a></li>
            <li><a href="/schedule">Schedule</a></li>
            <li><a href="/speakers">Speakers</a></li>
            <li><a href="/location">Location</a></li>
          </ul>
        </div>
        <div class="site-footer__col">
          <h5>Get Involved</h5>
          <ul>
            <li><a href="{SPONSOR_URL}">Sponsor FOC27</a></li>
            <li><a href="{SPEAK_URL}">Call for Speakers</a></li>
            <li><a href="{NOTIFY_URL}">Get Notified for FOC27</a></li>
          </ul>
        </div>
        <div class="site-footer__col">
          <h5>Hosted By</h5>
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
      <span>&copy; 2026 Flyover Con, hosted by {PARENT_NAME}. Polk City, Iowa.</span>
      <span>Updated {UPDATED_HUMAN}</span>
    </div>
  </div>
</footer>

<script src="/assets/js/main.js"></script>
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
            avatar = (f'<img class="mini-speaker__photo" src="/assets/img/speakers/{p}.jpg" '
                      f'srcset="/assets/img/speakers/{p}.jpg 1x, /assets/img/speakers/{p}@2x.jpg 2x" '
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
            head_img = (f'<img class="speaker__photo" src="/assets/img/speakers/{p}.jpg" '
                        f'srcset="/assets/img/speakers/{p}.jpg 1x, /assets/img/speakers/{p}@2x.jpg 2x" '
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
    body = "\n\n".join(f"User-agent: {a}\nAllow: /\nDisallow: /api/" for a in agents)
    return f"{body}\n\nSitemap: {BASE}/sitemap.xml\n"

def llms():
    return f"""# Flyover Con

> {TAGLINE} Hosted by P&M Apparel, Polk City, Iowa. FOC27 is presented by {PRESENTING_SPONSOR}.

Flyover Con is a hands-on conference for Midwest screen printers and decorators, hosted inside P&M Apparel's working production facility. A modest registration fee keeps it accessible while sponsors cover the rest. No vendor booths, no sales pitches. Real shop-floor learning from people who run print and embroidery shops every day.

Most recent event: FOC26, April 17-18, 2026, in Polk City, Iowa. 16 sessions across two days, 19 speakers, hosted on the P&M Apparel shop floor.

FOC27 is confirmed for April 16 and 17, 2027, at the same location, capped at 75 attendees. FOC27 is presented by {PRESENTING_SPONSOR}. Schedule and speakers are not yet announced as of {UPDATED_HUMAN}. Silver ($1,000) and Gold ($2,500) sponsorships are open; the Presenting level is claimed. Commitments are requested by {SPONSOR_DEADLINE}. The call for speakers is open and proposals close {PROPOSALS_CLOSE}.

- About: {BASE}/about
- Schedule (FOC27, April 16-17 2027, sessions TBD): {BASE}/schedule
- Years Past (full schedule archive): {BASE}/years-past
- Speakers (FOC27, lineup TBD): {BASE}/speakers
- Sponsor (FOC27 levels and inquiry form, commitments requested by {SPONSOR_DEADLINE}): {BASE}/sponsor
- Call for Speakers (FOC27 proposals close {PROPOSALS_CLOSE}): {BASE}/speak
- Location: {BASE}/location
- Contact: {EMAIL}
- Hosted by: P&M Apparel, {PARENT_URL}
- FOC27 presenting sponsor: {PRESENTING_SPONSOR}
"""

VERCEL = json.dumps({
    "cleanUrls": True,
    "trailingSlash": False,
    "redirects": [
        {"source": "/home", "destination": "/", "permanent": True},
        {"source": "/register", "destination": "/", "permanent": True},
        {"source": "/_/:path*", "destination": "/", "permanent": True},
    ],
    "headers": [{"source":"/(.*)","has":[{"type":"host","value":".*\\.vercel\\.app"}],
        "headers":[{"key":"X-Robots-Tag","value":"noindex"}]}],
}, indent=2)

# ---------------------------------------------------------------- main
def main():
    # The root ./assets directory is not committed. On a fresh clone the only
    # copy of the images and CSS is inside site/assets, and the rmtree below
    # would delete it before copytree could read it. Stage it first instead of
    # relying on remembering to do it by hand.
    if not os.path.isdir("assets"):
        staged = os.path.join(OUT, "assets")
        if not os.path.isdir(staged):
            sys.exit("build: no ./assets and no %s to recover it from" % staged)
        shutil.copytree(staged, "assets")
        print("build: staged ./assets from %s" % staged)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree("assets", os.path.join(OUT, "assets"))
    for key in PAGES:
        with open(os.path.join(OUT, key + ".html"), "w", encoding="utf-8") as f:
            f.write(render(key))
    for key, spec in RAW_PAGES.items():
        raw = open(spec["src"], encoding="utf-8").read()
        for find, repl in spec["subs"].items():
            if find not in raw:
                sys.exit(f"build: substitution target missing in {spec['src']}: {find}")
            raw = raw.replace(find, repl)
        with open(os.path.join(OUT, key + ".html"), "w", encoding="utf-8") as f:
            f.write(raw)
    for rel in COPY_FILES:
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join("src", rel), dst)
    for name, content in [("sitemap.xml", sitemap()), ("robots.txt", robots()),
                          ("llms.txt", llms()), ("vercel.json", VERCEL)]:
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
    n_photo = sum(1 for s in SPEAKERS if s["photo"])
    endpoint_state = SURVEY_ENDPOINT or "NO ENDPOINT SET"
    print(f"built {len(PAGES)} pages · {len(RAW_PAGES)} standalone (survey endpoint: {endpoint_state}) · "
          f"{len(COPY_FILES)} function(s) · {len(SPEAKERS)} speakers "
          f"({n_photo} with photos, {len(SPEAKERS)-n_photo} on initials) → {OUT}/")

if __name__ == "__main__":
    main()
