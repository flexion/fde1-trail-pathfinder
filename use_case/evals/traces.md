# AI-1 traces

50 runs of `suggest_competencies` (`suggest.py`), one per input in `trace_inputs.jsonl`. Read each and write one sentence per failure in `failures.md`.

## t-ai1-01 (golden)

**Backgrounds:** corps  
**Text:** Two seasons on a conservation corps crew. Mostly brushing and lopping, dug a lot of water bars and grade dips, some bench cut on new trail. Took the chainsaw class but only bucked a few logs.

**Output** (model, 12.2s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — You wrote "Mostly brushing and lopping"
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "Mostly brushing and lopping"
- likely · Entry · Water Management/Drainage Features (Trail Construction) — You wrote "dug a lot of water bars and grade dips"
- likely · Entry · Drainage Features/Water Management (Trail Maintenance) — You wrote "dug a lot of water bars and grade dips"
- check · Entry · Hand-Built Trail Construction (Trail Construction) — You wrote "some bench cut on new trail"
- check · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — You wrote "only bucked a few logs"
- check · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — You wrote "only bucked a few logs"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Safety/Site Management (Trail Maintenance) — Common for people with conservation corps experience
- possible · Entry · Trail Sustainability Principles (Trail Construction) — Common for people with conservation corps experience

---

## t-ai1-02 (golden)

**Backgrounds:** military  
**Text:** (none)

**Output** (rules, 0.0s):

- likely · Entry · Jobsite Safety (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Management (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Training (Crew Management) — Common for people with military service experience
- check · Entry · Communications (Program Administration) — Common for people with military service experience

---

## t-ai1-03 (golden)

**Backgrounds:** forestry  
**Text:** Four seasons on a hotshot crew. Certified sawyer, ran saw on fuels reduction and hazard trees. Squad boss the last season, ran the morning briefing.

**Output** (model, 4.4s):

- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — You wrote "Certified sawyer, ran saw on fuels reduction and hazard trees."
- likely · Entry · Crew Management (Crew Management) — You wrote "Squad boss the last season, ran the morning briefing."
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-ai1-04 (golden)

**Backgrounds:** landscape  
**Text:** Eight years in landscaping and grounds. Built dry-stack stone walls and flagstone steps, ran a mini-ex and skid steer, put in French drains.

**Output** (model, 4.1s):

- likely · Entry · Retaining Walls (Trail Construction) — You wrote "Built dry-stack stone walls"
- likely · Entry · Mechanized Trail Construction (Trail Construction) — You wrote "ran a mini-ex and skid steer"
- likely · Entry · Water Management/Drainage Features (Trail Construction) — You wrote "put in French drains"
- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience

---

## t-ai1-05 (golden)

**Backgrounds:** volunteer  
**Text:** Nine seasons building trail, the last four as crew lead for a six-person crew. Expert at dry-stone retaining walls and rock steps. I train the new hires on tool safety every spring.

**Output** (model, 6.5s):

- likely · Entry · Hand-Built Trail Construction (Trail Construction) — You wrote "Nine seasons building trail"
- likely · Entry · Crew Management (Crew Management) — You wrote "the last four as crew lead for a six-person crew"
- likely · Entry · Retaining Walls (Trail Construction) — You wrote "Expert at dry-stone retaining walls"
- likely · Entry · Crew Training (Crew Management) — You wrote "I train the new hires on tool safety every spring"
- likely · Entry · Jobsite Safety (Crew Management) — You wrote "tool safety"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-ai1-06 (golden)

**Backgrounds:** -  
**Text:** I worked on trails.

**Output** (model, 2.2s): declined. Not enough to go on: no task, tool or feature is named. Ask for what the work involved.


---

## t-ai1-07 (golden)

**Backgrounds:** -  
**Text:** Five years as a barista, then two years as an assistant manager at a retail store.

**Output** (model, 3.2s): declined. Nothing here maps to a trail competency. Pick a background or describe any outdoor, construction or crew work.


---

## t-ai1-08 (golden)

**Backgrounds:** volunteer, landscape  
**Text:** I helped plant trees and bushes and mowed lawns. Through scouts I helped maintain about three miles of trail.

**Output** (model, 3.5s):

- check · Entry · Maintenance Specifications (Trail Maintenance) — You wrote "Through scouts I helped maintain about three miles of trail."
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience

---

## t-ai1-09 (golden)

**Backgrounds:** landscape, construction  
**Text:** (none)

**Output** (rules, 0.0s):

- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience

---

## t-ai1-11 (golden)

**Backgrounds:** corps  
**Text:** Two seasons on a conservation corps crew. Mostly brushing and lopping, dug a lot of water bars and grade dips, some bench cut on new trail. Took the chainsaw class but only bucked a few logs.

**Output** (model, 6.6s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — You wrote "Mostly brushing and lopping"
- likely · Entry · Water Management/Drainage Features (Trail Construction) — You wrote "dug a lot of water bars and grade dips"
- check · Entry · Hand-Built Trail Construction (Trail Construction) — You wrote "some bench cut on new trail"
- check · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — You wrote "only bucked a few logs"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Safety/Site Management (Trail Maintenance) — Common for people with conservation corps experience
- possible · Entry · Trail Sustainability Principles (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with conservation corps experience

---

## t-ai1-12 (golden)

**Backgrounds:** none  
**Text:** Five years in landscaping. I built dry-stack stone walls on my own, laid flagstone paths, and ran a mini excavator to dig drainage trenches.

**Output** (model, 5.7s):

- likely · Entry · Retaining Walls (Trail Construction) — You wrote "I built dry-stack stone walls on my own"
- likely · Entry · Tread Hardening and Surfacing (Trail Construction) — You wrote "laid flagstone paths"
- likely · Entry · Water Management/Drainage Features (Trail Construction) — You wrote "ran a mini excavator to dig drainage trenches"

---

## t-ai1-13 (golden)

**Backgrounds:** -  
**Text:** For three years I coordinated volunteers for our local trail club. I ran the work-day sign-ups, wrote the monthly newsletter, and helped write a state grant for new trail signs. On work days I showed new volunteers how to clear drains and brush the trail.

**Output** (model, 5.3s):

- likely · Entry · Crew Management (Crew Management) — You wrote "I coordinated volunteers for our local trail club."
- check · Entry · Funding/Grants (Program Administration) — You wrote "helped write a state grant for new trail signs"
- likely · Entry · Education and Public Outreach (Program Administration) — You wrote "I showed new volunteers how to clear drains and brush the trail."

---

## t-ai1-14 (golden)

**Backgrounds:** volunteer  
**Text:** Weekend volunteer with a trail club for six years. We built a puncheon bridge across a wet meadow, rebuilt washed-out tread with hand tools, and I cleared blowdowns with a crosscut saw.

**Output** (model, 3.1s):

- likely · Entry · Water Crossing Structures (Trail Construction) — You wrote "We built a puncheon bridge across a wet meadow"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — You wrote "rebuilt washed-out tread with hand tools"
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — You wrote "I cleared blowdowns with a crosscut saw"
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-01 (generated)

**Backgrounds:** corps  
**Text:** I did one season with a conservation corps clearing brush, digging drainage, and fixing muddy spots on trails. Got pretty good with hand tools and hauling stuff all day.

**Output** (model, 6.8s):

- likely · Entry · Corridor Clearing/Site Preparation (Trail Construction) — You wrote "clearing brush"
- likely · Entry · Drainage Features/Water Management (Trail Maintenance) — You wrote "digging drainage"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — You wrote "fixing muddy spots on trails"
- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — You wrote "clearing brush"
- likely · Entry · Safety/Site Management (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Hand-Built Trail Construction (Trail Construction) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Trail Sustainability Principles (Trail Construction) — Common for people with conservation corps experience

---

## t-gen-02 (generated)

**Backgrounds:** corps, forestry  
**Text:** Spent two seasons doing trail work and invasive plant removal. We planted trees, used a brush cutter, and helped with some small bridge repairs. I learned a lot but was still pretty new at the start.

**Output** (model, 7.7s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "used a brush cutter"
- check · Entry · Water Crossing Structures (Trail Construction) — You wrote "helped with some small bridge repairs"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Safety/Site Management (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Hand-Built Trail Construction (Trail Construction) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Trail Sustainability Principles (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-gen-03 (generated)

**Backgrounds:** corps, construction  
**Text:** I worked one season building rock steps, moving gravel, and putting in culverts. I had done some home construction before, so the tools and measuring part wasnt totally new to me.

**Output** (model, 7.7s):

- likely · Entry · Hand-Built Trail Construction (Trail Construction) — You wrote "building rock steps"
- likely · Entry · Tread Hardening and Surfacing (Trail Construction) — You wrote "building rock steps, moving gravel"
- likely · Entry · Water Management/Drainage Features (Trail Construction) — You wrote "putting in culverts"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Safety/Site Management (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Trail Sustainability Principles (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with conservation corps experience
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience

---

## t-gen-04 (generated)

**Backgrounds:** corps, military  
**Text:** Did a season on a corps crew after getting out of the military. Mostly clearing storm damage, carrying logs, and working long days outside. I liked the team part of it.

**Output** (model, 6.4s):

- likely · Entry · Corridor Clearing/Site Preparation (Trail Construction) — You wrote "Mostly clearing storm damage, carrying logs"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Safety/Site Management (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Hand-Built Trail Construction (Trail Construction) — Common for people with conservation corps experience
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Trail Sustainability Principles (Trail Construction) — Common for people with conservation corps experience
- possible · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with conservation corps experience
- likely · Entry · Jobsite Safety (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Management (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Training (Crew Management) — Common for people with military service experience
- check · Entry · Communications (Program Administration) — Common for people with military service experience

---

## t-gen-05 (generated)

**Backgrounds:** none  
**Text:** I spent one summer on a trail crew. We cut back overgrown plants, painted signs, and picked up trash. I didnt know much going in but got the hang of it.

**Output** (model, 6.6s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "We cut back overgrown plants"

---

## t-gen-06 (generated)

**Backgrounds:** landscape, volunteer  
**Text:** I helped with trail projects for two seasons and also volunteered on weekend park work days. Did planting, weeding, and some basic trail repairs. Not an expert, but I show up and work hard.

**Output** (model, 5.6s):

- check · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — You wrote "some basic trail repairs"
- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-07 (generated)

**Backgrounds:** forestry  
**Text:** I worked on a hotshot crew for 3 seasons. Did fireline, burnout, saw work, and long hikes with a heavy pack.

**Output** (model, 7.4s):

- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — You wrote "saw work"
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — You wrote "saw work"
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-gen-08 (generated)

**Backgrounds:** forestry, volunteer  
**Text:** Ran an engine on wildfires and did structure protection, hose lays, and mop up. Also helped with prescribed burns in the off season.

**Output** (rules, 3.2s):

- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-09 (generated)

**Backgrounds:** forestry, construction  
**Text:** I was a sawyer on trail and fuels projects, mostly clearing down trees and brushing in rough country. Pretty comfortable with chainsaws and hard work.

**Output** (model, 3.1s):

- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — You wrote "I was a sawyer on trail and fuels projects, mostly clearing down trees"
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — You wrote "brushing in rough country"
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience

---

## t-gen-10 (generated)

**Backgrounds:** forestry  
**Text:** Did timber cruising for a couple summers, measuring trees and marking units. Wasnt fancy work but I learned the woods and got good at working on my own.

**Output** (rules, 3.3s):

- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-gen-11 (generated)

**Backgrounds:** landscape  
**Text:** I’ve done lawn care and landscaping for about 4 years. Lots of planting, trimming, hauling mulch, and using small equipment.

**Output** (model, 5.0s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — You wrote "Lots of planting, trimming, hauling mulch, and using small equipment."
- likely · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — You wrote "using small equipment"
- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience

---

## t-gen-12 (generated)

**Backgrounds:** landscape  
**Text:** Worked with a nursery crew loading trees, watering, and keeping plants organized. I’m used to being outside all day and doing the hard lifting.

**Output** (rules, 4.2s):

- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience

---

## t-gen-13 (generated)

**Backgrounds:** construction  
**Text:** I helped on a few patio and retaining wall jobs, mixing materials and moving rock. Never worked on trails before but I learn fast.

**Output** (model, 2.7s):

- check · Entry · Retaining Walls (Trail Construction) — You wrote "I helped on a few patio and retaining wall jobs, mixing materials and moving rock."
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience

---

## t-gen-14 (generated)

**Backgrounds:** volunteer  
**Text:** Did volunteer cleanups at a local park and some brush clearing with my neighbor. Not a ton of experience but I dont mind dirty work.

**Output** (model, 2.2s):

- check · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — You wrote "Did volunteer cleanups at a local park and some brush clearing with my neighbor."
- check · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "some brush clearing with my neighbor"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-15 (generated)

**Backgrounds:** military  
**Text:** I spent 8 years in the Army doing field work, vehicle maintenance, and leading small teams. Used to long days outside and figuring things out with limited tools.

**Output** (rules, 6.9s):

- likely · Entry · Jobsite Safety (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Management (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Training (Crew Management) — Common for people with military service experience
- check · Entry · Communications (Program Administration) — Common for people with military service experience

---

## t-gen-16 (generated)

**Backgrounds:** military, construction  
**Text:** Worked as a combat engineer building roads, clearing sites, and running equipment. Not much trail work yet but I’m comfortable with hard physical work and safety procedures.

**Output** (model, 5.2s):

- likely · Entry · Mechanized Trail Construction (Trail Construction) — You wrote "running equipment"
- likely · Entry · Corridor Clearing/Site Preparation (Trail Construction) — You wrote "clearing sites"
- likely · Entry · Safety/Site Management (Trail Construction) — You wrote "safety procedures"
- likely · Entry · Jobsite Safety (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Management (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Training (Crew Management) — Common for people with military service experience
- check · Entry · Communications (Program Administration) — Common for people with military service experience
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience

---

## t-gen-17 (generated)

**Backgrounds:** military, volunteer  
**Text:** I led crews on different projects and handled planning, training, and daily task assignments. Also did some volunteer cleanup work at local parks, nothing fancy.

**Output** (model, 6.9s):

- likely · Entry · Crew Management (Crew Management) — You wrote "I led crews on different projects and handled planning, training, and daily task assignments."
- likely · Entry · Crew Training (Crew Management) — You wrote "handled planning, training, and daily task assignments"
- likely · Entry · Jobsite Safety (Crew Management) — Common for people with military service experience
- check · Entry · Communications (Program Administration) — Common for people with military service experience
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-18 (generated)

**Backgrounds:** volunteer  
**Text:** Helped with a local trail cleanup a few times, mostly picking up trash and moving small branches. It was good work outside.

**Output** (model, 4.0s):

- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — You wrote "mostly picking up trash and moving small branches"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-19 (generated)

**Backgrounds:** volunteer, construction  
**Text:** I spent two weekends with the trail club clearing brush and fixing a couple muddy spots. Used hand tools and worked with a small crew.

**Output** (model, 3.9s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "clearing brush"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — You wrote "fixing a couple muddy spots. Used hand tools"
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience

---

## t-gen-20 (generated)

**Backgrounds:** landscape  
**Text:** Did some seasonal landscaping work, including spreading mulch, trimming plants, and hauling materials. A little hard on the back but I liked being outdoors.

**Output** (model, 5.8s):

- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Construction) — You wrote "trimming plants"
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "trimming plants"
- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience

---

## t-gen-21 (generated)

**Backgrounds:** volunteer, forestry  
**Text:** I volunteered on trail days for about a year. Cleared fallen trees, dug drainage ditches, and helped build steps. Not an expert but I learned as I went.

**Output** (model, 4.5s):

- likely · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — You wrote "Cleared fallen trees"
- likely · Entry · Drainage Features/Water Management (Trail Maintenance) — You wrote "dug drainage ditches"
- check · Entry · Hand-Built Trail Construction (Trail Construction) — You wrote "helped build steps"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-gen-22 (generated)

**Backgrounds:** construction  
**Text:** I did framing and trim work on houses for about 5 years. Also built decks and fixed whatever needed fixing.

**Output** (rules, 5.5s):

- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience

---

## t-gen-23 (generated)

**Backgrounds:** construction  
**Text:** Ran skid steer and mini excavator on site prep and utility jobs. Did some grading, trenching, and loading trucks.

**Output** (model, 5.3s):

- likely · Entry · Mechanized Trail Construction (Trail Construction) — You wrote "Ran skid steer and mini excavator on site prep and utility jobs."
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience

---

## t-gen-24 (generated)

**Backgrounds:** construction, volunteer  
**Text:** Ive done general labor on road crews, moving materials, cleanup, and flagging. Helped a volunteer group clear brush and fallen trees too.

**Output** (model, 6.5s):

- check · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "Helped a volunteer group clear brush and fallen trees too."
- likely · Entry · Corridor Clearing: Material and Debris Management (Trail Maintenance) — You wrote "moving materials, cleanup"
- check · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — You wrote "Helped a volunteer group clear brush and fallen trees too."
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-25 (generated)

**Backgrounds:** forestry  
**Text:** I worked for the parks department doing basic map updates, site checks, and helping with permits. Mostly office work but I got out in the field some too.

**Output** (model, 6.8s):

- likely · Entry · Trail Plan Development (Project Planning and Design) — You wrote "basic map updates"
- likely · Entry · Inspections/Monitoring (Program Administration) — You wrote "site checks"
- likely · Entry · Compliance and Permitting (Project Planning and Design) — You wrote "helping with permits"
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-gen-26 (generated)

**Backgrounds:** volunteer  
**Text:** I helped a nonprofit write grants and organize volunteer days. I kept track of sign-ups, sent emails, and made sure people had what they needed. never had a formal trail job.

**Output** (model, 5.5s):

- check · Entry · Funding/Grants (Program Administration) — You wrote "helped a nonprofit write grants"
- likely · Entry · Communications (Program Administration) — You wrote "sent emails"
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-27 (generated)

**Backgrounds:** none  
**Text:** I did planning work with GIS and reviewed permits for small projects. I’m comfortable learning new systems and talking with the public, but I havent done much hands-on construction.

**Output** (model, 4.1s):

- likely · Entry · Trail Plan Development (Project Planning and Design) — You wrote "I did planning work with GIS"
- likely · Entry · Compliance and Permitting (Project Planning and Design) — You wrote "reviewed permits for small projects"
- likely · Entry · Communications (Program Administration) — You wrote "talking with the public"

---

## t-gen-28 (generated)

**Backgrounds:** landscape  
**Text:** I’ve mostly done outdoor work and didn’t mind being out in bad weather. It was pretty physical and I liked staying busy.

**Output** (rules, 1.9s):

- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience

---

## t-gen-29 (generated)

**Backgrounds:** volunteer  
**Text:** I helped out with some community projects for a while. Just showed up, worked hard, and did whatever needed doing.

**Output** (rules, 1.8s):

- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-30 (generated)

**Backgrounds:** none  
**Text:** I’ve had a few different jobs, mostly hands-on stuff. Nothing fancy, but I’m used to long days and working with other people.

**Output** (model, 2.0s): declined. Nothing here maps to a trail competency. Pick a background or describe any outdoor, construction or crew work.


---

## t-gen-31 (generated)

**Backgrounds:** none  
**Text:** I worked retail for about three years. I helped customers, stocked shelves, and opened and closed the store. I’m used to being on my feet and getting stuff done even when it’s busy.

**Output** (model, 3.8s): declined. Nothing here maps to a trail competency. Pick a background or describe any outdoor, construction or crew work.


---

## t-gen-32 (generated)

**Backgrounds:** volunteer  
**Text:** I’ve mostly worked in restaurants, taking orders and helping prep food. I also volunteer at a community garden sometimes, so I don’t mind physical work or getting dirty.

**Output** (rules, 2.8s):

- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-33 (generated)

**Backgrounds:** construction, volunteer  
**Text:** I’ve done a bit of everything over the years, building trails, clearing brush, fixing things and helping crews get jobs done. I’m good with tools and can figure stuff out as I go.

**Output** (model, 4.6s):

- likely · Entry · Hand-Built Trail Construction (Trail Construction) — You wrote "building trails"
- likely · Entry · Corridor Clearing: Pruning/ Side-Cutting/ Brushing (Trail Maintenance) — You wrote "clearing brush"
- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience
- likely · Entry · Tread Maintenance - Hand tools (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Corridor Clearing/Site Preparation (Trail Maintenance) — Common for people with trail volunteering experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with trail volunteering experience
- check · Entry · Drainage Features/Water Management (Trail Maintenance) — Common for people with trail volunteering experience

---

## t-gen-34 (generated)

**Backgrounds:** landscape  
**Text:** Worked on trails and outdoor projects for a long time. I’ve done crew work, repairs, cleanup, and some landscaping, pretty comfortable with most jobs.

**Output** (model, 8.8s):

- check · Entry · Corridor Clearing/Site Preparation (Trail Construction) — You wrote "I’ve done crew work, repairs, cleanup, and some landscaping"
- possible · Entry · Tread Hardening and Surfacing (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with landscaping or grounds experience
- possible · Entry · Tread Maintenance - Mechanized Equipment (Trail Maintenance) — Common for people with landscaping or grounds experience
- check · Entry · Water Management/Drainage Features (Trail Construction) — Common for people with landscaping or grounds experience

---

## t-gen-35 (generated)

**Backgrounds:** military  
**Text:** (none)

**Output** (rules, 0.0s):

- likely · Entry · Jobsite Safety (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Management (Crew Management) — Common for people with military service experience
- possible · Entry · Crew Training (Crew Management) — Common for people with military service experience
- check · Entry · Communications (Program Administration) — Common for people with military service experience

---

## t-gen-36 (generated)

**Backgrounds:** construction, forestry  
**Text:** (none)

**Output** (rules, 0.0s):

- possible · Entry · Water Crossing Structures (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Retaining Walls (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Mechanized Trail Construction (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Construction Specifications (Trail Construction) — Common for people with construction trades experience
- possible · Entry · Jobsite Safety (Crew Management) — Common for people with construction trades experience
- likely · Entry · Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut (Trail Maintenance) — Common for people with forestry or wildland fire experience
- likely · Entry · Corridor Clearing: Felling/tree removal; Chainsaw/ Crosscut (Trail Construction) — Common for people with forestry or wildland fire experience
- possible · Entry · Safety/Site Management (Trail Maintenance) — Common for people with forestry or wildland fire experience
- possible · Entry · Corridor Clearing: Material and Debris Management (Trail Construction) — Common for people with forestry or wildland fire experience

---

## t-gen-37 (generated)

**Backgrounds:** none  
**Text:** (none)

**Output** (rules, 0.0s): declined. Nothing here maps to a trail competency. Pick a background or describe any outdoor, construction or crew work.


---
