#!/usr/bin/env python3
"""
Seed 10-Student Authentic Cognitive Development Cohort for Dara's Coffee Cart (4Ps).

Features:
- Prunes noisy synthetic test sessions (probe_student_*, test_student_*, etc.) from BUS C150.
- Seeds exactly 10 distinct, named students working on Dara's Coffee Cart.
- Each student encounters one or more of the 4 Neo4j misconception traps on
  "The Marketing Mix and the 4Ps of Marketing" (concept 4375e29e-c040-5ff0-bef2-8780e3c95d2e).
- Probes are structured pedagogically:
    Level 1: Orienting Inquiry (Observe key case context)
    Level 2: Critical Challenge (Examine trade-offs & binding constraints)
    Level 3: Strategic Framework (Ground decisions in core marketing principles)
- Replaces conversational noise with high-signal cognitive milestones:
    Framing -> Conceptual Friction -> Deliberation & Struggle -> Cognitive Pivot (with before/after diff)
    -> Evidence Grounding -> Strategic Synthesis -> Completed Draft.
- Sets all 10 students to status = 'completed' (none in 'submitted' state).
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from fiosra.mvp.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

COURSE_ID = "8a9fefac-e5b9-49dd-935c-88cfd1929e26"

STUDENTS = [
    {
        "student_id": "julian_hayes",
        "name": "Julian Hayes",
        "trap_name": "The Library Footfall Trap (Raw Footfall Fallacy)",
        "inquiry_level": 2,
        "probe_focus": "Competitor proximity & walk-time friction",
        "probe_text": "If a student is already standing on the library steps, only 4 minutes from the campus café, what advantage is Dara delivering outside in the cold to justify buying there instead? And at €0.70 margin, how many cups must she sell daily just to cover the €45 licence?",
        "struggle_text": "I didn't account for dwell time versus footfall. 1,200 people walking past the library steps doesn't mean they will stop in the cold when a warm café with seating is 4 minutes away. At €1.50, my margin is only €0.70 (€1.50 - €0.80 cost), meaning Dara needs 65 cups a day just to pay fixed rent.",
        "premise_text": "Dara should park at the library steps because 1,200 people pass there every day. She should charge €1.50 to undercut the campus café and drive maximum sales volume.",
        "pivot_before": "Dara should park at the library steps because 1,200 people pass there every day. She should charge €1.50 to undercut the campus café.",
        "pivot_after": "Dara must abandon her initial intuition to position the coffee cart on the central library steps and instead relocate permanently to the Science concourse. While raw pedestrian footfall at the library appears enticing at 1,200 individuals per hour, raw volume is not equivalent to converted purchasing demand. At the library steps, students are situated a mere four-minute walk from the established campus café, which offers indoor heating, extensive comfortable seating, and protection from cold Irish rain. Operating outdoors directly adjacent to a superior indoor facility forces Dara into destructive price discounting. Conversely, the Science concourse—despite registering lower footfall of 700 students—is separated from the campus café by an 11-minute cross-campus walk (a 22-minute round trip). By positioning at the Science building, Dara eliminates transit friction for laboratory students and creates a defensible geographic convenience moat.",
        "pivot_insight": "Shifted from raw footfall volume to walk-time buffer as the true strategic moat and pricing driver.",
        "evidence_text": "Empirical survey metrics from the case dossier provide rigorous quantitative validation for this strategic shift. Crucially, 62% of surveyed students report that they purchase coffee between classes solely if the retail location is substantially closer than the central café. Science students moving between tight 50-minute laboratory blocks simply cannot spare 22 minutes to fetch coffee; Dara becomes their only viable supplier. Furthermore, the survey identifies that 41% of campus consumers actively demand plant-based oat milk and are prepared to pay an extra premium. Cost accounting reveals an ingredient floor of €0.80 per cup (beans, milk, biodegradable cup, lid). By establishing a retail price of €2.80, Dara secures a €2.00 unit contribution margin (71% gross margin). Incorporating the €0.40 oat milk add-on yields a €2.40 margin. Selling 65 cups daily across morning break surges generates €130 in daily gross profit, amortizing the €45 weekly municipal licence fee (€9 daily allocation) in less than two trading hours.",
        "synthesis_text": "The four Ps must operate as a unified, systematically interlocking mechanism rather than four fragmented choices. Product: Dara must bypass complex food prep to offer streamlined, pre-batched dark roast drip coffee, express espresso, and rapid oat milk dispensers, maintaining an uncompromising sub-40-second transaction cycle. Price: Set retail price at €2.80, comfortably underneath the campus café's €3.20 price ceiling while fully capturing convenience rent. Place: Secure an authorized trading stance at the covered Science concourse breezeway, capturing heavy pedestrian flow between biology and chemistry lecture theatres. Promotion: Rather than spending on broad social media ads, Dara should utilize hyper-local physical marketing—installing bold A3 timetable boards outside laboratory exit doors and distributing punch-cards ('Buy 5 Mornings, Get Friday Free') to establish habitual morning purchase rituals.",
        "word_count": 413,
    },
    {
        "student_id": "elena_rostova",
        "name": "Elena Rostova",
        "trap_name": "The Menu Bloat Trap (Destroying Service Speed)",
        "inquiry_level": 2,
        "probe_focus": "Queue throughput & service speed",
        "probe_text": "The survey notes 62% of students buy coffee between classes. If Dara begins toasting paninis and blending smoothies on a single cart with one pair of hands, what happens to queue length and transaction speed during a 10-minute break rush? In OpenStax §9.1, what is the core product being sold?",
        "struggle_text": "Food preparation takes 3-4 minutes per customer. During a brief 10-minute lecture changeover, Dara could only serve 3 people! In OpenStax §9.1, the core benefit for a student rushing between buildings is saved time. Preparing hot food actually attacks and destroys the core product rather than enhancing it.",
        "premise_text": "Dara should offer hot panini melts, toasted bagels, blended fruit smoothies, and artisan pastries alongside coffee to maximize average basket size and reach €8 per transaction.",
        "pivot_before": "Dara should offer hot panini melts, toasted bagels, blended smoothies, and pastries to increase ticket size to €6-€8 per order.",
        "pivot_after": "Dara must rigorously eliminate all hot food preparation, toasted paninis, bagels, and blended fruit smoothies from her cart's offerings. Drawing upon core versus augmented product theory (OpenStax §9.1), the fundamental product Dara sells to campus commuters is not gourmet dining or culinary variety, but saved transit time during frantic class changeovers. Preparing toasted paninis and blended drinks requires two to three minutes per patron. Operating as a solo entrepreneur on a compact mobile cart with a single pair of hands, preparing hot food immediately produces catastrophic queuing bottlenecks. Impatient students standing in an immobile queue will abandon their place for fear of missing lectures. Introducing food complexity actively attacks and destroys the primary customer benefit: rapid caffeine delivery without academic tardiness. Streamlining the product line protects the cart's fundamental competitive advantage and preserves the operational integrity of the entire business model.",
        "pivot_insight": "Recognized that transaction speed during peak changeover windows is the actual product, not menu variety.",
        "evidence_text": "Grounded case data confirms that 62% of student coffee consumption occurs strictly within compressed 10-minute intervals between consecutive university lectures. If food preparation stretches service time to three minutes per patron, Dara can process a maximum of three customers during a 10-minute break, capping gross revenue at €18 to €24. In radical contrast, configuring the cart around pre-brewed thermal carafes and tap-dispensed nitro cold brew reduces transaction duration to 40 seconds per person. This ergonomic velocity enables Dara to serve 15 to 18 customers during each 10-minute inter-class window. Selling 60 cups across four daily changeover periods at €2.60 per cup (€0.80 ingredient baseline) yields €1.80 contribution margin per cup and €108 in daily gross margin. This performance easily absorbs the €45 weekly licence fee (€9 per day) while eliminating raw food inventory spoilage and equipment maintenance overhead. Operational velocity is the true engine of profitability.",
        "synthesis_text": "Every dimension of the marketing mix must systematically reinforce operational throughput and counter velocity. Product: Curate a focused, high-speed beverage menu centered on rich batch filter coffee, double espresso, cold brew, and pre-wrapped local flapjacks that require zero counter preparation. Price: Establish an all-inclusive €2.60 pricing standard optimized for rapid contactless card tap-and-go transactions, avoiding delays associated with cash handling. Place: Position the cart at the high-density North Lecture Hall crossroads where thousands of students transit between back-to-back 50-minute lectures. Promotion: Prominently mount an overhead high-contrast chalkboard sign announcing 'Fresh Hot Coffee in Under 40 Seconds - Guaranteed No Class Delays', explicitly communicating time savings as the cart's core value proposition to hurried passersby. Together, these elements deliver unmatched convenience.",
        "word_count": 407,
    },
    {
        "student_id": "marcus_chen",
        "name": "Marcus Chen",
        "trap_name": "Superficial Arithmetic (Break-Even without Strategic Inference)",
        "inquiry_level": 3,
        "probe_focus": "Peak-window throughput vs fixed licence",
        "probe_text": "Across 9,000 campus students, selling 23 cups a week covers the €45 licence. If financial survival is readily achieved on paper, what is the real operational constraint on Dara's revenue? Connect break-even to peak inter-class windows.",
        "struggle_text": "A standard break-even calculation assumes customers arrive smoothly throughout an 8-hour day. But campus demand arrives in four intense 15-minute bursts. If Dara prices at €1.20 (€0.40 margin), serving 80 peak cups yields only €32 daily profit, which fails to pay for her time. Break-even math without queue modeling is misleading.",
        "premise_text": "The €45 weekly licence requires selling 112.5 cups at €1.20 to break even (€0.40 margin). Across 9,000 students, selling 23 cups a day is trivial, so Dara's financial model is guaranteed secure.",
        "pivot_before": "Selling 23 cups a day at €1.20 covers the €45 weekly licence. Therefore the cart is financially secure with minimal volume.",
        "pivot_after": "Dara's commercial strategy must abandon simplistic, static break-even calculations in favor of capacity-constrained queuing economics. Calculating that selling 23 cups per week covers the €45 municipal licence fee naively assumes that student footfall is distributed evenly across an eight-hour operating schedule. In reality, university demand functions in four intense, 15-minute inter-class transition bursts, providing approximately 60 minutes of aggregate peak sales opportunity per day. Positioning the cart as a low-price discount vendor at €1.20 yields a fragile €0.40 unit margin that cannot generate an acceptable operator return, regardless of headline campus enrollment of 9,000 students. Dara must optimize margin velocity per minute of peak operational capacity rather than chasing ungrounded volume illusions. Survival depends on capturing maximum economic value during brief surges, requiring a rigorous alignment between service speed, pricing strategy, and physical counter throughput.",
        "pivot_insight": "Replaced decorative break-even calculation with throughput-constrained capacity economics.",
        "evidence_text": "Financial and survey evidence within the case dossier confirms this operational reality. Dara faces an €0.80 variable ingredient floor per cup (fresh beans, milk, cup, lid). Selling at €1.20 produces €0.40 gross margin; serving 80 peak patrons generates a negligible €32 in daily gross profit, failing to cover basic labor costs. Conversely, pricing strategically at €2.70 generates €1.90 gross profit per transaction. Maintaining a disciplined 45-second service rhythm allows Dara to serve 20 students per 15-minute passing window, achieving 80 completed transactions across four daily peaks. This delivers €216 in daily revenue, €64 in variable costs, and €143 net daily operating income after allocating the €9 daily licence share. Monetizing the 41% student demand for plant-based oat milk at +€0.40 adds an extra €13.12 pure margin daily, creating an economically resilient enterprise capable of sustaining the owner-operator throughout the semester.",
        "synthesis_text": "The 4Ps align to maximize net contribution margin per second of peak operational availability. Product: Standardized twin thermal airpot filter brews and automated double espresso pulls engineered for zero preparation latency. Price: Value-calibrated €2.70 base with an optional €0.40 oat milk customization, positioned safely below the €3.20 campus café while guaranteeing healthy unit returns. Place: Station the cart at the Engineering Concourse breezeway, where dense changeover footfall gathers without causing indoor corridor congestion. Promotion: Distribute lecture-synchronized loyalty punch cards ('Buy 5 Mornings, Get Friday Free') during opening-week module orientations to lock in weekly repeat purchase habits and smooth out demand across morning sessions. Every variable reinforces financial sustainability and queue velocity, ensuring robust economic returns and operational resilience.",
        "word_count": 393,
    },
    {
        "student_id": "priya_patel",
        "name": "Priya Patel",
        "trap_name": "The Disjointed Mix Fallacy (4P Silo Trap)",
        "inquiry_level": 1,
        "probe_focus": "4Ps system interdependence",
        "probe_text": "Reflect on OpenStax §1.2: How does a decision about where to park immediately constrains what your price and preparation speed can be? Trace how these decisions depend on one another rather than four isolated answers.",
        "struggle_text": "My first draft treated the 4Ps as four unconnected answers on an exam: artisan pour-overs, €4.20 price, library steps, and TikTok reels. But high-end pour-overs take 5 minutes to brew, contradicting the rush at the library, and €4.20 exceeds the café ceiling. Every decision constrains the other three.",
        "premise_text": "Product: Single-origin Ethiopian pour-over. Price: €4.20. Place: Library steps. Promotion: Viral TikTok video campaigns.",
        "pivot_before": "Product: Single-origin pour-overs (€4.20). Place: Library steps. Promotion: TikTok video campaigns.",
        "pivot_after": "Dara's marketing mix must function as a cohesive, systematically integrated mechanism rather than four isolated checklist decisions (OpenStax §1.2). Proposing single-origin artisan pour-overs priced at €4.20 on the library steps supported by viral social media campaigns fails because the individual decisions actively contradict one another. Manual pour-overs take four to five minutes to brew, completely destroying transaction throughput during morning commuter rushes. Simultaneously, charging €4.20 exceeds the campus café's €3.20 price benchmark on their immediate doorstep, driving price-sensitive students inside. Dara's core positioning must center on dependable commuter transit velocity, where every element of the marketing mix reinforces and enables the others. Location choices immediately dictate preparation speeds, which in turn dictate price thresholds and promotional channels. A successful strategy requires holistic harmony across all four Ps, ensuring that each decision magnifies the effectiveness of the total commercial offering.",
        "pivot_insight": "Transformed four disconnected checklist answers into a mutually reinforcing marketing mix.",
        "evidence_text": "Rigorous analysis of the case survey reveals that 62% of campus coffee consumers purchase strictly between classes, prioritizing physical proximity and speed over gourmet brand prestige. Positioning the cart at the West Quad commuter bus terminal establishes an immediate seven-minute walking advantage over the central university building. At a retail price of €2.60 set against the €0.80 cost of goods floor, Dara secures an attractive €1.80 unit contribution margin (69% gross margin). Capturing just 50 morning bus arrivals covers the €45 weekly municipal licence in less than two trading days, while catering to the 41% student demand for oat milk (+€0.40) lifts average unit margin to €1.96. The economic numbers demonstrate that speed and proximity drive sustainable profitability far more effectively than isolated luxury pricing, establishing a sound financial foundation for daily operations and guaranteeing healthy margins.",
        "synthesis_text": "Systemic interdependence binds the four Ps into a synchronized operational machine: Place (West bus terminal loop) dictates customer mindset (schedule-pressured morning arrivals sprint-walking toward lecture halls); which strictly dictates Product (instant thermal batch filter coffee and pre-poured cold brews designed for immediate handover); which dictates Price (€2.60 round contactless pricing eliminating till friction); which dictates Promotion (high-contrast directional ground stencils and transit shelter posters directing disembarking bus passengers straight to Dara's service counter). Each variable supports transit speed, eliminating operational contradictions and creating an unbroken circuit of customer value that competitors cannot readily match. Cohesion creates defensibility and locks in predictable customer habits every morning of the week, generating consistent revenue throughout the semester.",
        "word_count": 390,
    },
    {
        "student_id": "david_kim",
        "name": "David Kim",
        "trap_name": "The Library Footfall Trap (Raw Footfall Fallacy)",
        "inquiry_level": 2,
        "probe_focus": "Footfall conversion vs competitive insulation",
        "probe_text": "Look closely at the library steps in the case data. What competitor is 4 minutes away, and if Dara undercuts with a €1.40 price, what does that force her daily volume to be in order to survive?",
        "struggle_text": "Discounting to €1.40 leaves only €0.60 margin. To make even €60 a day, Dara would have to serve 100 people outside in the freezing weather right next to a warm café. Moving to an underserved academic quad allows higher pricing and requires half the transactions.",
        "premise_text": "Dara should park on the central library plaza and charge €1.40. With 1,200 people passing, price discounting will steal customers from the campus café.",
        "pivot_before": "Dara should park on the central library plaza and charge €1.40. Price discounting will steal customers from the café.",
        "pivot_after": "Dara should decisively reject aggressive price-cutting on the central library steps in favor of captive spatial insulation in the Engineering and Technology Quad. Attempting to undercut the established campus café by discounting coffee to €1.40 leaves a meager €0.60 margin above the €0.80 ingredient baseline. To earn even a modest €60 daily return, Dara would need to serve 100 outdoor patrons directly adjacent to a heated indoor competitor with plush seating and Wi-Fi. Moving to the Engineering Quad provides an isolated territory where 650 students face a 12-minute walk to any hot beverage outlet, allowing Dara to price for convenience rather than engaging in a ruinous price war with an established rival. Geographic insulation transforms an otherwise weak outdoor stance into a protected local micro-monopoly, providing reliable pricing power and consistent customer demand throughout the week.",
        "pivot_insight": "Swapped high-traffic price war for captive-quad convenience pricing.",
        "evidence_text": "At a convenience price of €2.75, Dara earns €1.95 in gross margin per cup over her €0.80 ingredient baseline. Serving just 45 engineering students daily generates €87.75 in daily gross margin, easily surpassing the weekly €45 licence fee in under three days of trading. Conversely, at the discounted €1.40 price, achieving that same margin would require 146 transactions—an impossible volume for a solo cart operator during restricted changeover breaks. Furthermore, incorporating quick-brew loose leaf black and green teas directly captures the 28% non-coffee demographic identified in the campus survey at a €0.35 unit cost and €2.20 retail price (€1.85 margin). Capturing both tea and coffee drinkers diversifies revenue while keeping preparation entirely frictionless and swift, maximizing daily transaction yield across both groups and boosting overall cart profitability significantly.",
        "synthesis_text": "The 4Ps coordinate around spatial convenience and targeted student demographics. Product: Fresh hot batch brew, espresso, and high-margin specialty teas catering to diverse student tastes without slowing queue lines. Price: €2.75 for coffee and €2.20 for tea, offering excellent perceived value compared to the €3.20 café while preserving strong gross margins. Place: Engineering Quad courtyard, directly serving 650 STEM students during laboratory intervals who cannot make the 24-minute round trip across campus. Promotion: Sponsor weekly engineering student society project showcases and offer group discounts on pre-filled insulated travel carafes for late-night lab teams, cementing strong departmental loyalty and steady weekday demand. This integrated mix ensures high volume, healthy margins, and sustainable operations that thrive independent of central campus competition and deliver robust commercial returns every single day.",
        "word_count": 391,
    },
    {
        "student_id": "maya_lin",
        "name": "Maya Lin",
        "trap_name": "The Menu Bloat Trap (Destroying Service Speed)",
        "inquiry_level": 1,
        "probe_focus": "Core customer value vs equipment complexity",
        "probe_text": "Section 9.1 separates the core benefit from augmented items. If the core benefit is saved time during class breaks, how does adding blenders and toasters damage the cart's competitive advantage?",
        "struggle_text": "I thought offering sandwiches and smoothies would make Dara more competitive. But blenders require heavy power, cleaning cycles, and 3-minute prep times. Students who only have 10 minutes between lectures will walk away if the queue moves slowly.",
        "premise_text": "Dara should equip the cart with a dual panini grill and commercial blender to offer grilled wraps and berry smoothies.",
        "pivot_before": "Dara should equip the cart with a panini grill and blender to offer grilled wraps and smoothies.",
        "pivot_after": "Dara must firmly resist expanding her cart menu with commercial blenders, panini grills, and hot food items. According to product hierarchy theory (OpenStax §9.1), customer value is anchored in the core benefit: rapid cognitive alertness delivered between scheduled university lectures. Incorporating blended smoothies and toasted wraps introduces severe electrical demands, hygiene maintenance cycles, and extended three-minute preparation times. On an outdoor cart during a chilly 10-minute lecture recess, long queues destroy customer confidence. Hurried students walking past an immobile queue will continue walking to avoid being late. Streamlining the product line to rapid-pour beverages preserves Dara's core competitive advantage of speed, protecting the operational simplicity required for a single operator to succeed without compromising service quality or alienating time-pressed patrons. Speed is the essence of campus retail, and operational focus is the key to maintaining student trust during critical peak transition windows.",
        "pivot_insight": "Eliminated prep friction to defend the core product value proposition: instantaneous service.",
        "evidence_text": "The case survey reveals that 62% of respondents purchase coffee strictly during class intervals when speed is their paramount decision factor. Utilizing dual high-capacity thermal carafes and pre-batched nitro cold brew taps reduces service time to just 30 seconds per customer. This velocity allows Dara to serve 20 students during every 10-minute break. At an average retail price of €2.80 against an €0.80 unit cost, Dara nets €2.00 per cup. Achieving 70 transactions daily across morning and afternoon lecture intervals yields €140 in daily gross profit, absorbing the €45 weekly licence fee (€9 per day) in less than an hour of peak trade while incurring zero food spoilage. Fast turnover eliminates perishable inventory waste completely, preserves cash flow, and ensures high product consistency throughout every single shift. Serving speed directly translates into commercial profitability.",
        "synthesis_text": "An integrated velocity-first marketing mix: Product: Premium dark roast batch brew, nitrogen-tapped cold brew, and pre-wrapped artisanal flapjacks that require zero prep time or counter clutter. Price: Clean €2.80 standard price point with contactless tap payment, eliminating coin transactions and till delays. Place: Central Sciences concourse connecting major lecture halls, capturing students during scheduled five-minute lecture changeovers. Promotion: Distribute branded reusable travel tumblers with a €0.20 refill discount to encourage customer retention and generate visible peer word-of-mouth endorsement across science lecture halls, turning regular commuters into vocal brand advocates. Every element aligns to deliver instantaneous, dependable caffeine service while maintaining high unit margins, protecting the cart from operational bottlenecks and creating an extraordinary customer experience.",
        "word_count": 391,
    },
    {
        "student_id": "liam_oconnor",
        "name": "Liam O'Connor",
        "trap_name": "The Library Footfall Trap (Raw Footfall Fallacy)",
        "inquiry_level": 3,
        "probe_focus": "Defensibility against indoor café in winter",
        "probe_text": "Compare alternatives: at the Library, the campus café is 4 minutes away; at the Arts Annex, it is 10 minutes away. In bad weather or winter months, which location is defensible?",
        "struggle_text": "When it rains or gets cold, nobody will queue outside at the library steps when the heated café is 200 meters away. At the Arts Annex, walking to the café takes 20 minutes round trip, so an outdoor cart with an awning is far more defensible.",
        "premise_text": "Park on the library steps to catch students going into the library, charging €1.75.",
        "pivot_before": "Park on the library steps to catch students going into the library, charging €1.75.",
        "pivot_after": "Dara should position her cart under the sheltered colonnade of the Arts Annex rather than the exposed library steps. Distribution strategy must account for physical environment factors and weather seasonality. During rainy autumn and freezing winter terms, an outdoor cart on the library steps loses almost all footfall to the heated campus café situated just 200 meters away. At the Arts Annex, however, walking to the central café requires a 20-minute round trip through open, unsheltered campus grounds. Stationing the cart under the Arts arcade provides essential weather protection while establishing a localized monopoly for 800 arts and humanities students who need quick service without braving the elements. Environmental defensibility protects sales continuity during winter, insulating Dara from adverse seasonal fluctuations and guaranteeing steady revenue year-round. Sheltered location transforms weather from a threat into a powerful protective barrier, lasting competitive advantage, protect market share, and shield the business from revenue volatility.",
        "pivot_insight": "Factored weather and physical environmental friction into distribution defensibility.",
        "evidence_text": "Because a 20-minute round trip walk exceeds the standard 15-minute inter-class passing window, students at the Arts Annex cannot patronize the central café without risking lecture tardiness. Pricing coffee at €2.65 against an €0.80 ingredient baseline delivers a healthy €1.85 unit contribution margin. Serving 50 captive students daily yields €92.50 in daily gross margin (€462.50 per five-day week), easily amortizing the €45 weekly municipal permit in half a single day. Furthermore, catering to the 28% of students who prefer hot tea with premium specialty blends generates €1.80 margin per cup at negligible preparation cost. Dara provides high satisfaction while securing dependable, weather-resilient profit margins throughout the entire academic year, proving that spatial and climate barriers create lasting competitive advantage and shield the business from revenue volatility.",
        "synthesis_text": "A weather-defensible, coordinated marketing strategy: Product: Steaming batch brew coffee, spicy chai, and loose teas formulated for brisk weather and rapid dispensation. Price: €2.65 for coffee and €2.20 for tea, delivering superior perceived value compared to the café while protecting healthy unit margins. Place: Covered walkway of the Arts Annex, shielded from rain and wind gusts. Promotion: Post graphic timetable announcements on arts departmental digital noticeboards and collaborate with the student drama society for opening-night intermission coffee service, anchoring the cart within student cultural life and building authentic community roots that survive competitive pressures. This creates a deeply loyal, year-round patron base and shields the venture from macro volatility, ensuring durable daily trading success across all seasons and weather conditions.",
        "word_count": 397,
    },
    {
        "student_id": "sofia_rodriguez",
        "name": "Sofia Rodriguez",
        "trap_name": "Superficial Arithmetic (Break-Even without Strategic Inference)",
        "inquiry_level": 2,
        "probe_focus": "Inter-class rush queuing model",
        "probe_text": "If Dara charges €1.50, she needs 65 transactions a day to cover costs and make a modest wage. In a single cart operation with peak 10-minute rushes, is 65 transactions feasible if preparation takes 2 minutes?",
        "struggle_text": "At 2 minutes per cup, Dara can only serve 5 people per 10-minute break. Across 4 breaks, that is only 20 cups! At €1.50, she would lose money every week. The preparation time must be cut to 40 seconds, and the price must rise to €2.70.",
        "premise_text": "Charge €1.50 to guarantee high customer volume and easily cover the €45 licence fee.",
        "pivot_before": "Charge €1.50 to guarantee high volume and easily cover the €45 licence fee.",
        "pivot_after": "Dara must discard static break-even assumptions and structure her business model around the mathematical constraints of inter-class queuing. A low-price strategy of €1.50 yields an inadequate €0.70 contribution margin above the €0.80 cost floor, requiring 65 daily transactions to achieve financial sustainability. However, if individual beverage preparation takes two minutes, a single-operator cart can serve only five customers during a 10-minute class break. Across four daily breaks, maximum achievable volume is only 20 cups, resulting in severe daily financial losses. Dara must re-engineer her workflow for 40-second transaction velocity and adopt premium convenience pricing to achieve solvency and commercial viability. Operational speed is the primary prerequisite for business survival, without which no volume strategy can succeed in a transit-oriented university setting. Speed and margin must be designed concurrently from day one to guarantee that peak surges convert into viable financial surpluses.",
        "pivot_insight": "Linked transaction time directly to mathematical solvency and capacity ceiling.",
        "evidence_text": "Optimizing cart ergonomics and utilizing commercial thermal brewers reduces transaction time to 40 seconds, expanding capacity to 15 transactions per 10-minute break window. Across five daily lecture intervals, Dara can achieve 75 transactions. Pricing at €2.75 against the €0.80 ingredient baseline generates €1.95 unit margin, yielding €146.25 daily gross profit (€731.25 weekly). This comfortably absorbs the €45 weekly licence fee (€9 per day) and leaves €137.25 daily net operating income to reward Dara's labor. In addition, capturing the 41% student demand for oat milk (+€0.40 surcharge) contributes an extra €12.30 in pure margin daily, proving that service speed directly dictates profitability and long-term viability. Financial success stems from rapid execution rather than discounted pricing, turning operational excellence into sustainable economic returns and solid business value that easily withstands unexpected cost shocks and seasonal attendance shifts.",
        "synthesis_text": "An operationally grounded marketing mix: Product: Pre-brewed dark roast filter coffee, automated espresso pulls, and oat milk options designed for rapid pouring and instant service. Price: €2.75 flat contactless price point engineered for rapid tap-to-pay throughput, entirely eliminating change handling. Place: Humanities and Social Sciences concourse crossroads, capturing massive pedestrian waves between lecture halls. Promotion: Distribute a digital WhatsApp community loyalty pass offering every seventh cup free, driving predictable repeat patronage across the semester while keeping promotional spend at zero. Every operational touchpoint minimizes friction and maximizes transaction throughput, guaranteeing consistent commercial returns and durable competitive advantage that keeps queues moving smoothly and ensures student satisfaction across every break period throughout the entire academic term.",
        "word_count": 391,
    },
    {
        "student_id": "aisha_almansoor",
        "name": "Aisha Al-Mansoor",
        "trap_name": "The Disjointed Mix Fallacy (4P Silo Trap)",
        "inquiry_level": 2,
        "probe_focus": "Promotion aligned with physical Place constraints",
        "probe_text": "A single coffee cart can only be in one physical spot at a time. If you run general campus-wide digital promotions, what happens when students on the other side of campus cannot reach you in time?",
        "struggle_text": "Promoting on Instagram to all 9,000 students is wasteful because only students within a 3-minute walking radius can physically buy between classes. Promotion must be strictly localized to the buildings surrounding the cart.",
        "premise_text": "Use campus social media ads and sponsored student union Instagram posts to drive campus-wide awareness.",
        "pivot_before": "Use campus social media ads and sponsored student union Instagram posts to drive campus-wide awareness.",
        "pivot_after": "Dara must realign her promotional strategy with the physical distribution realities of a single stationary cart. Allocating time and financial capital to campus-wide Instagram advertising or student union sponsorships is economically wasteful. A mobile cart stationed at a specific campus location cannot serve students situated across an expansive 9,000-student university campus during brief 10-minute class transitions. Promotional efforts must be strictly confined to the immediate two-minute pedestrian walking radius surrounding the cart, targeting students who have the physical capability to complete a transaction between lectures without incurring schedule delays. Promoting outside this physical catchment creates awareness that cannot convert into realized sales, wasting scarce marketing resources on unreachable audiences. Promotional discipline must mirror physical distribution limits, creating a hyper-targeted outreach model that converts foot traffic into paying patrons with maximum efficiency and minimum overhead, ensuring that marketing spend directly drives immediate volume.",
        "pivot_insight": "Aligned promotional spend and channel with hyper-local physical distribution constraints.",
        "evidence_text": "Case brief survey findings confirm that 62% of campus coffee purchasing decisions are dictated by immediate proximity during class changeovers. Stationing the cart at the Science concourse exposes Dara to 700 passing students per day. Setting retail price at €2.80 against an €0.80 cost floor provides €2.00 contribution margin per cup. Converting just 8% of this localized corridor traffic (56 customers per day) generates €112 in daily gross profit, fully amortizing the €45 weekly licence fee in less than two trading days. Expensive broad digital campaigns are unnecessary when localized footfall conversion yields complete financial viability. Hyper-local conversion provides all the customer volume needed to maximize profitability without extraneous promotional expenses, ensuring extraordinary return on investment and disciplined capital allocation that allows the venture to thrive on modest capital while protecting operating cash.",
        "synthesis_text": "Physical Place directly dictates Promotional architecture: Place (Science concourse) restricts Promotion to zero-cost chalk sidewalk wayfinding and physical timetable posters positioned at science lecture hall exits; which dictates Product (rapid batch drip coffee and oat milk options ensuring 35-second service); which dictates Price (€2.80 premium convenience pricing reflecting isolation from the central café). Every component of the mix reinforces the local walking shed, creating a tight geographic circuit that maximizes local conversion without spending a single euro on wasteful campus-wide advertising. This discipline guarantees exceptional marketing efficiency, high margins, and sustainable long-term campus operations that outcompete distant, generic campus catering alternatives while building strong neighborhood loyalty and dependable, highly lucrative daily student purchasing routines.",
        "word_count": 389,
    },
    {
        "student_id": "lucas_bennett",
        "name": "Lucas Bennett",
        "trap_name": "The Library Footfall Trap (Raw Footfall Fallacy)",
        "inquiry_level": 1,
        "probe_focus": "Transit footfall vs dwell-time conversion",
        "probe_text": "Section 17.2 treats a location's value as its traffic set against the ease of the nearest alternative. Does high footfall on the library steps convert into sales if students are in rapid transit to catch buses or rush into quiet zones?",
        "struggle_text": "Footfall does not equal demand. Students at the library steps are either heading into quiet study where coffee is restricted, or sprinting to the bus. Moving to the Medical building patio captures students who have a mandatory 15-minute wait between lab rotations.",
        "premise_text": "Park on library steps because 1,200 people pass by every hour.",
        "pivot_before": "Park on library steps because 1,200 people pass by every hour.",
        "pivot_after": "Dara must distinguish between raw transit pedestrian traffic and qualified, dwell-time purchasing intent (OpenStax §17.2). The 1,200 students passing the library steps each hour are predominantly commuters rushing to catch municipal buses or students entering library study halls where beverage consumption is strictly prohibited. Relocating to the Medical Sciences courtyard taps a cohort of 600 healthcare students who experience mandatory 15-minute dwell intervals between clinical laboratory rotations. Because the central campus café is a 14-minute walk away (a 28-minute round trip), these students represent a captive audience with high intent to purchase and sufficient time to enjoy their beverage. Quality dwell time converts far better than rushed footfall, providing an ideal customer base for an outdoor cart that commands strong loyalty and delivers consistent, high-volume transactions throughout the academic year. Captive dwell time turns pedestrian traffic into loyal, daily patrons.",
        "pivot_insight": "Distinguished between transit traffic and dwell-time purchasing intent.",
        "evidence_text": "Because clinical students cannot complete a 28-minute round-trip to the campus café during their 15-minute recess, Dara enjoys total geographic insulation. At a price of €2.85 against an €0.80 ingredient cost, she earns €2.05 unit contribution margin. Serving 55 medical students daily across morning and afternoon clinical changeovers generates €112.75 in daily gross profit (€563.75 weekly), covering the €45 licence fee in under two days. Catering to the 41% student preference for oat milk (+€0.40) provides €2.45 margin on those orders, maximizing profit from a captive professional student body that values quality, convenience, and reliable service during demanding academic days. The numbers demonstrate an extraordinarily resilient operational model with unmatched customer retention, high average ticket values, and robust daily profitability that shields Dara from broader campus footfall swings and macro seasonality.",
        "synthesis_text": "Strategic coordination of the 4Ps: Product: High-caffeine dark batch brew, chilled cold brew, and herbal teas formulated for medical students under intense study schedules. Price: €2.85 for coffee and €2.30 for tea, anchored comfortably below the café's €3.20 price ceiling while reflecting spatial convenience. Place: Sheltered Medical Sciences courtyard arcade, capturing dwell-time breaks between clinical laboratories. Promotion: Informational notices pinned to medical student common room boards and scheduled announcements during morning clinical orientation meetings, ensuring 100% awareness among the captive medical cohort and driving robust daily sales volume. This targeted alignment delivers consistent commercial success, enduring competitive strength, and high daily customer satisfaction across every academic department in the medical wing, creating a dependable and thriving campus coffee enterprise.",
        "word_count": 390,
    },
]


async def seed_clean_cohort():
    async with AsyncSessionLocal() as session:
        logger.info("🔍 Locating Dara's Coffee Cart assignment in BUS C150...")
        result = await session.execute(
            text("""
                SELECT a.assignment_id, a.title, m.course_id
                FROM assignments a
                JOIN modules m ON a.module_id = m.module_id
                WHERE (a.title ILIKE '%coffee%' OR a.title ILIKE '%dara%')
                  AND m.course_id = :course_id
                ORDER BY a.created_at DESC
                LIMIT 1;
            """),
            {"course_id": COURSE_ID}
        )
        row = result.mappings().first()
        if not row:
            raise RuntimeError(f"Dara's Coffee Cart assignment not found in course {COURSE_ID}")

        assignment_id = str(row["assignment_id"])
        assignment_title = row["title"]
        logger.info(f"✅ Found assignment: '{assignment_title}' ({assignment_id})")

        # 1. Clean up noisy test/mock sessions for this course
        logger.info("🧹 Pruning noisy test/mock sessions from course...")
        sess_rows = await session.execute(
            text("""
                SELECT s.session_id, s.student_id 
                FROM student_sessions s
                JOIN assignments a ON s.assignment_id = a.assignment_id
                JOIN modules m ON a.module_id = m.module_id
                WHERE m.course_id = :course_id;
            """),
            {"course_id": COURSE_ID}
        )
        all_course_sessions = sess_rows.mappings().all()
        clean_student_ids = {s["student_id"] for s in STUDENTS}

        stale_session_ids = [
            str(r["session_id"])
            for r in all_course_sessions
            if r["student_id"] not in clean_student_ids
        ]

        if stale_session_ids:
            logger.info(f"   Deleting {len(stale_session_ids)} stale/mock sessions and events...")
            for i in range(0, len(stale_session_ids), 50):
                chunk = stale_session_ids[i:i+50]
                formatted_sids = ", ".join(f"'{sid}'" for sid in chunk)
                await session.execute(
                    text(f"DELETE FROM session_events WHERE session_id IN ({formatted_sids});")
                )
                await session.execute(
                    text(f"DELETE FROM student_sessions WHERE session_id IN ({formatted_sids});")
                )
            await session.commit()
            logger.info("   ✅ Stale test records pruned.")

        # 2. Seed each of the 10 students
        now = datetime.now(timezone.utc)
        for idx, stu in enumerate(STUDENTS):
            student_id = stu["student_id"]
            logger.info(f"🌱 Seeding student [{idx+1}/10]: {stu['name']} ({student_id})...")

            existing = await session.execute(
                text("SELECT session_id FROM student_sessions WHERE student_id = :sid AND assignment_id = :aid;"),
                {"sid": student_id, "aid": assignment_id}
            )
            ex_row = existing.mappings().first()

            if ex_row:
                session_id = str(ex_row["session_id"])
                await session.execute(
                    text("DELETE FROM session_events WHERE session_id = :sid;"),
                    {"sid": session_id}
                )
            else:
                session_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO student_sessions (
                            session_id, student_id, assignment_id, current_question_id, status,
                            started_at, last_activity_at, completed_at
                        ) VALUES (
                            CAST(:session_id AS UUID), :student_id, CAST(:assignment_id AS UUID), :question_id, 'completed',
                            NOW() - INTERVAL '45 minutes', NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '5 minutes'
                        );
                    """),
                    {"session_id": session_id, "student_id": student_id, "assignment_id": assignment_id, "question_id": str(assignment_id)}
                )

            # Ensure status is 'completed' and question_id is assignment_id
            await session.execute(
                text("""
                    UPDATE student_sessions 
                    SET status = 'completed', 
                        current_question_id = :question_id,
                        completed_at = NOW() - INTERVAL '5 minutes',
                        last_activity_at = NOW() - INTERVAL '5 minutes'
                    WHERE session_id = CAST(:session_id AS UUID);
                """),
                {"session_id": session_id, "question_id": str(assignment_id)}
            )

            # Build chronological events (T-45 min to T-5 min)
            base_t = now - timedelta(minutes=45) + timedelta(minutes=idx * 2)

            events = [
                # 1. Assignment Opened
                (base_t, "assignment_opened", {
                    "title": "Dara's Coffee Cart: A First Encounter with the 4Ps",
                    "module": "Module 1: Foundations of Marketing Strategy",
                }),
                # 2. Case Exhibit Read
                (base_t + timedelta(seconds=20), "source_exhibit_read", {
                    "title": "Dara's Coffee Cart: Case Dossier & Survey",
                    "citation": "Campus Operational Brief (2026)",
                }),
                # 3. Textbook Chapter Opened
                (base_t + timedelta(seconds=55), "source_document_opened", {
                    "title": "OpenStax Principles of Marketing §1.2 The Marketing Mix",
                    "section": "§1.2",
                }),
                # 4. Initial Premise Saved (with flawed intuition)
                (base_t + timedelta(seconds=140), "canvas_section_saved", {
                    "section_id": "positioning",
                    "revision": 1,
                    "plaintext": stu["premise_text"],
                }),
                # 5. Misconception Flagged (Neo4j Trap Triggered)
                (base_t + timedelta(seconds=220), "misconception_flagged", {
                    "kc_id": "4375e29e-c040-5ff0-bef2-8780e3c95d2e",
                    "concept": "The Marketing Mix and the 4Ps of Marketing",
                    "trap_name": stu["trap_name"],
                    "inquiry_level": stu["inquiry_level"],
                }),
                # 6. Socratic Marginalia Probe Delivered
                (base_t + timedelta(seconds=250), "socratic_probe_offered", {
                    "focus_type": stu["probe_focus"],
                    "question": stu["probe_text"],
                    "inquiry_level": stu["inquiry_level"],
                    "probe_label": f"Socratic Inquiry: {stu['probe_focus']}",
                    "eyebrow": "ORIENTING INQUIRY" if stu["inquiry_level"] == 1 else ("CRITICAL CHALLENGE" if stu["inquiry_level"] == 2 else "STRATEGIC FRAMEWORK"),
                }),
                # 7. Student Reflection & Struggle
                (base_t + timedelta(seconds=350), "socratic_probe_response_submitted", {
                    "response_text": stu["struggle_text"],
                }),
                # 8. Cognitive Pivot (Revised Canvas with before/after diff & insight)
                (base_t + timedelta(seconds=460), "canvas_section_saved", {
                    "section_id": "positioning",
                    "revision": 2,
                    "milestone": "pivot",
                    "icon": "🔄",
                    "label": f"Reframed strategy: {stu['pivot_insight']}",
                    "insight": stu["pivot_insight"],
                    "plaintext": stu["pivot_after"],
                    "diff": {
                        "before": stu["pivot_before"],
                        "after": stu["pivot_after"],
                    },
                }),
                # 9. Evidence Grounding (Survey data, cost floor, margins)
                (base_t + timedelta(seconds=580), "canvas_section_saved", {
                    "section_id": "evidence_grounding",
                    "revision": 3,
                    "milestone": "evidence",
                    "icon": "📊",
                    "label": "Grounded model in case brief survey & cost floors",
                    "plaintext": stu["evidence_text"],
                }),
                # 10. Strategic Synthesis (All 4Ps interlocked)
                (base_t + timedelta(seconds=710), "canvas_section_saved", {
                    "section_id": "strategic_synthesis",
                    "revision": 4,
                    "milestone": "synthesis",
                    "icon": "🧩",
                    "label": "Unified Product, Price, Place, and Promotion into one cohesive mix",
                    "plaintext": stu["synthesis_text"],
                }),
                # 11. Final Reasoning Draft Completed
                (base_t + timedelta(seconds=820), "session_completed", {
                    "document_revision": 4,
                    "word_count": stu["word_count"],
                    "sections_completed": ["positioning", "evidence_grounding", "strategic_synthesis"],
                    "summary": f"Completed 4Ps strategic reasoning draft ({stu['word_count']} words) addressing all case criteria.",
                }),
            ]

            for ev_time, ev_type, payload in events:
                await session.execute(
                    text("""
                        INSERT INTO session_events (
                            session_id, student_id, assignment_id, question_id, event_type, created_at, payload
                        ) VALUES (
                            CAST(:session_id AS UUID), :student_id, CAST(:assignment_id AS UUID), :question_id, :event_type, :created_at, CAST(:payload AS JSONB)
                        );
                    """),
                    {
                        "session_id": session_id,
                        "student_id": student_id,
                        "assignment_id": assignment_id,
                        "question_id": str(assignment_id),
                        "event_type": ev_type,
                        "created_at": ev_time,
                        "payload": json.dumps(payload),
                    }
                )

            # 12. Seed Learning Document & Blocks (so Canvas is fully populated)
            await session.execute(
                text("DELETE FROM learning_document_blocks WHERE document_id IN (SELECT document_id FROM learning_documents WHERE session_id = :sid);"),
                {"sid": session_id}
            )
            await session.execute(
                text("DELETE FROM learning_documents WHERE session_id = :sid;"),
                {"sid": session_id}
            )
            await session.execute(
                text("DELETE FROM canvas_section_drafts WHERE session_id = :sid;"),
                {"sid": session_id}
            )

            doc_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO learning_documents (
                        document_id, session_id, assignment_id, title, schema_version, document_revision, created_at, updated_at
                    ) VALUES (
                        CAST(:doc_id AS UUID), CAST(:session_id AS UUID), CAST(:assignment_id AS UUID),
                        :title, 1, 4, NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '5 minutes'
                    );
                """),
                {
                    "doc_id": doc_id,
                    "session_id": session_id,
                    "assignment_id": assignment_id,
                    "title": f"Strategic Marketing Plan: Dara's Coffee Cart - {stu['name']}",
                }
            )

            # Insert structured blocks (Headings + Paragraphs)
            doc_blocks = [
                ("heading", "page_1", 1, "Strategic Marketing Plan: Dara's Coffee Cart"),
                ("paragraph", "page_1", None, f"Executive Analysis & Strategy Draft prepared by {stu['name']} for BUS C150: Principles of Marketing."),
                ("heading", "page_1", 2, "1. Strategic Positioning & Customer Value Proposition"),
                ("paragraph", "page_1", None, stu["pivot_after"]),
                ("heading", "page_1", 2, "2. Unit Economics & Grounded Evidence"),
                ("paragraph", "page_1", None, stu["evidence_text"]),
                ("heading", "page_1", 2, "3. Cohesive 4Ps Marketing Mix"),
                ("paragraph", "page_1", None, stu["synthesis_text"]),
            ]

            for pos, (b_type, sec_id, level, text_val) in enumerate(doc_blocks, start=1):
                b_id = str(uuid.uuid4())
                if b_type == "heading":
                    node_content = {
                        "type": "heading",
                        "attrs": {"level": level, "blockId": b_id, "sectionId": sec_id},
                        "content": [{"type": "text", "text": text_val}],
                    }
                else:
                    node_content = {
                        "type": "paragraph",
                        "attrs": {"blockId": b_id, "sectionId": sec_id},
                        "content": [{"type": "text", "text": text_val}],
                    }

                await session.execute(
                    text("""
                        INSERT INTO learning_document_blocks (
                            block_id, document_id, section_id, position, block_type, content, plaintext, author_type, revision, created_at, updated_at
                        ) VALUES (
                            CAST(:block_id AS UUID), CAST(:document_id AS UUID), :section_id, :position,
                            :block_type, CAST(:content AS JSONB), :plaintext, 'student', 1, NOW() - INTERVAL '20 minutes', NOW() - INTERVAL '5 minutes'
                        );
                    """),
                    {
                        "block_id": b_id,
                        "document_id": doc_id,
                        "section_id": sec_id,
                        "position": pos,
                        "block_type": b_type,
                        "content": json.dumps(node_content),
                        "plaintext": text_val,
                    }
                )

            # Insert legacy canvas section drafts
            for sec_id, text_val in [
                ("positioning", stu["pivot_after"]),
                ("evidence_grounding", stu["evidence_text"]),
                ("strategic_synthesis", stu["synthesis_text"]),
            ]:
                await session.execute(
                    text("""
                        INSERT INTO canvas_section_drafts (
                            session_id, section_id, text, author_type, revision, updated_at
                        ) VALUES (
                            CAST(:session_id AS UUID), :section_id, :text, 'student', 4, NOW() - INTERVAL '5 minutes'
                        );
                    """),
                    {"session_id": session_id, "section_id": sec_id, "text": text_val}
                )

        await session.commit()
        logger.info(f"\n🎉 Successfully seeded all 10 students into Dara's Coffee Cart ({assignment_id})!")
        logger.info("   All 10 students marked status = 'completed'.")
        logger.info("   All stale mock sessions pruned.")


if __name__ == "__main__":
    asyncio.run(seed_clean_cohort())
