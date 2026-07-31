# Waypoint — travel-triggered relationship radar

**Status:** design proposal, not yet built
**Author:** drafted for Jonas Menesklou (AskUI)
**Date:** 2026-07-31

---

## 1. The problem, stated precisely

Three different failures are hiding in one complaint:

| # | Failure | Example | Why existing tools miss it |
|---|---------|---------|----------------------------|
| 1 | **Dropped promises** | "Let me know when you're in South Bay to catch up." Read, meant it, forgot it. | The commitment lives inside a message thread. No system ever turned it into an object with a trigger. |
| 2 | **Invisible proximity** | You're in SF for three days. 180 of your 4,000 LinkedIn connections are there; 9 of them are ICP, investor, or partner shaped. You never find out. | Your network has no geography attached to it. LinkedIn does not tell you "who of mine is here". |
| 3 | **Relationship decay** | You met someone great 14 months ago, had two good calls, then nothing. | Nothing measures staleness against relationship value, and nothing knows when re-contacting is cheap (same city) vs. expensive. |

All three become tractable the moment you join **two datasets that are never joined today**:

```
(your calendar / trips / current location)  ⋈  (your relationship graph + its message history)
```

Waypoint is the join, plus a ranking on top of it, plus a nudge at the moment the join produces something actionable.

**One-line pitch:** *Your network, sorted by where you'll be standing next Tuesday.*

---

## 2. What the product actually is

Not a CRM. Not an outreach tool. It is a **briefing surface** with three views:

### 2.1 Radar (now)
You're in a place right now. "You are in Munich until Friday. Three people are worth 30 minutes each. One of them invited you 8 months ago."

### 2.2 Trip Brief (the core object)
A trip = a place + a date range. The brief is a **ranked list of plays** for that trip, each one a card:

- who, where, how far from your anchor hotel/office
- **why now** — one sentence, the whole reason the card exists
- **evidence** — the actual quote from the thread that justifies it, with date
- **the draft** — a two-line message you can send or edit, in your voice
- a slot suggestion against your real calendar gaps

Cards are grouped by play type: `Promises` · `Pipeline` · `Capital` · `Partners` · `Catch-ups`.

### 2.3 Sweep (always running)
Independent of travel: a background pass over new messages that files anything that looks like a future commitment, so nothing new is ever lost. This is what makes the product work in month 6, not just at import time.

**The wow moment for the demo** is not the map. It is the first import: *"We found 23 open invitations in your LinkedIn history. 11 are still warm."* That output alone justifies the product before a single trip is planned.

---

## 3. Ranking: how a card earns its place

Every candidate person/trip pair gets scored. Keep it explainable — the user must be able to see why a card ranked where it did, otherwise trust dies on the first bad suggestion.

```
score = value × timeliness × feasibility
```

**value** — the highest-scoring role match, not a sum:
- `promise` — an explicit, unreturned invitation exists → strongest signal in the system
- `icp` — company + title match the ICP definition (for AskUI: automotive / aviation / defense / medtech / industrial, QA / test / validation / HIL / E2E ownership, OEM or Tier-1)
- `investor` — stage, thesis, and check size match the current or next raise
- `partner` — systems integrators, test-bench vendors, tooling ecosystems
- `relationship` — high historical warmth, no current commercial angle (these still matter; rank them lower but never zero)

**timeliness** — decay and freshness:
- promise age (an invite from 3 weeks ago beats one from 3 years ago, but old ones don't hit zero — surface them as "long overdue")
- staleness vs. cadence: someone you used to talk to monthly and haven't in a year scores higher than someone you never had cadence with
- live triggers: they changed jobs, their company raised, they posted about a relevant problem, the fund announced a new vehicle

**feasibility** — the thing that makes it a *travel* app:
- travel time from your anchor location that day (not straight-line distance — a Peninsula meeting from SoMa is a 50-minute commitment each way and the app should say so)
- do you actually have a gap in the calendar
- do they look reachable (recent activity, response history)

Show the score as a bar with a hover breakdown. Never show a naked number.

**Feedback loop:** every dismiss is training data. "Not relevant" vs. "not now" vs. "wrong person" are three different buttons and three different weight updates.

---

## 4. Promise extraction

The hardest and most valuable piece. Input: a message thread. Output: zero or more structured commitments.

```json
{
  "person_id": "li:aleksandra-…",
  "type": "open_invitation",
  "direction": "inbound",
  "place": { "raw": "south bay", "resolved": "South Bay, CA, US", "confidence": 0.86 },
  "quote": "let me know when you're in the south bay and we'll grab coffee",
  "said_at": "2025-11-14",
  "expires": null,
  "fulfilled": false,
  "evidence_message_id": "…"
}
```

Design notes that matter more than the prompt:

- **Recall over precision at extraction, precision at surfacing.** Extract generously, then let a second pass and the user's confirmations filter. A missed promise is invisible; a false one costs one click.
- **Detect fulfillment, not just creation.** If a later message in the thread says "great seeing you in Palo Alto", the promise is closed. Without this the app nags about things you already did — the fastest way to get uninstalled.
- **Direction matters.** *They* invited *you* (act on it) is different from *you* promised *them* (you owe them — rank higher, it's a debt).
- **Vague places are normal.** "the Bay", "next time you're stateside", "when you're at CES" — resolve to a geo shape or an *event*, and keep the confidence. Event-anchored promises ("find me at CES") are their own trigger type keyed to a conference date, not a city.
- **Run extraction over a whole thread, not message-by-message.** Context decides whether "let's catch up" is a real invite or a sign-off pleasantry.

---

## 5. Data plumbing — and the honest constraint

**LinkedIn is the whole product and LinkedIn does not want to give you this data.** Any design that hand-waves here is a design that doesn't ship. Options, ranked by how much you'd regret them:

| Source | Gets you | Reality |
|---|---|---|
| **LinkedIn data export** (Settings → Get a copy of your data) | `Connections.csv` (name, company, position, connect date) + **full `messages.csv` archive** | Official, ToS-clean, complete history. Manual, ~24h to generate, refresh monthly. **No location field on connections** and no profile URLs for everyone. Start here. |
| **LinkedIn Marketing/Partner APIs** | Effectively nothing relevant | No connection list, no messaging read. Not a path. |
| **Hosted unofficial API** (Unipile, and similar) | Live connections + messaging + send | Real companies build on it. It's account-automation against ToS; restriction risk is on your account. Viable if you accept that. |
| **Your own computer-use agent** (AskUI) | Whatever a logged-in human can see, driven locally in your own browser | Dogfood angle: AskUI is literally a UI automation agent. Same ToS exposure as above, but the data never leaves your machine. Good demo story, real risk. |
| **Gojberry** (already connected) | LinkedIn unibox threads + `send_unibox_linkedin_message` | You already own a LinkedIn messaging surface. For threads that flow through it, this is a live read/write channel with no new integration risk. |

**Recommendation:** build v1 on the **export**, because it is the only path that gives you the full historical message archive — which is exactly where the forgotten promises are. Layer the live channel (Gojberry, then optionally a hosted API) on top for ongoing capture, and treat re-export as a monthly ritual until a live read path proves itself.

### The location problem

Connections.csv has no location. Location is the field the entire product pivots on. Fix it in three tiers:

1. **Enrichment** — Lusha is already connected; Clay/Apollo/Proxycurl are alternatives. Enrich only the top N by score, not all 4,000 — cost control matters and most connections will never rank.
2. **Inference** — company HQ + office locations, historical meeting locations from Granola, timezone from message timestamps.
3. **User correction** — one tap on a card fixes it forever. Treat corrections as gold; they're cheap and permanent.

Every location carries a confidence, and a low-confidence location shows as "likely in SF" rather than a false certainty.

### Other sources worth wiring

| Source | Why |
|---|---|
| **Calendar** | Trip detection (events with a location, out-of-office), and free-slot suggestion. The feasibility term needs it. |
| **Gmail** (connected) | Flight and hotel confirmations → trips detected before you plan them. Also a second promise-extraction corpus — plenty of "swing by when you're here" lives in email. |
| **Granola** (connected) | Meeting transcripts: who you actually met, what you actually promised out loud. Best single source for "you said you'd introduce them to X". |
| **Attio** (connected) | Existing company/deal context so ICP scoring reflects real pipeline stage, and so a Waypoint meeting writes back as an interaction. |
| **Phone location** | Only for "I'm here now" nudges. Optional, off by default, coarse geofence at metro level — never a live trail. |

---

## 6. Data model

```
Person        id, names, linkedin_urn, emails, current_title, current_company_id,
              location{place_id, confidence, source}, tags[], warmth, last_touch_at,
              cadence_days, do_not_nudge

Company       id, name, domain, industry, size, hq_place_id, attio_id, icp_score

Place         id, name, kind(metro|neighborhood|venue|region), geo, parent_id
              — "South Bay" and "SF Bay Area" must both be first-class and nested

Thread        id, channel(linkedin|email|whatsapp|meeting), person_ids[], last_message_at
Message       id, thread_id, direction, sent_at, body, source_ref

Promise       id, person_id, thread_id, type, direction, place_id, event_id,
              quote, said_at, expires_at, state(open|scheduled|fulfilled|dropped),
              confidence

Trip          id, place_id, starts_on, ends_on, anchor_place_id, purpose, source(manual|calendar|email)
Slot          id, trip_id, starts_at, ends_at, state(free|held|booked)

FitProfile    id, kind(icp|investor|partner), rules/description  — editable in plain language
Nudge         id, trip_id?, person_id, play_type, score, score_breakdown,
              why_now, evidence_promise_id?, draft_body, state, feedback
Interaction   id, person_id, kind, happened_at, source  — writes back to Attio
```

Two modelling decisions worth defending:

- **Promise is a first-class table, not a tag on a message.** It has a lifecycle, it can be fulfilled, and it is the highest-value object in the system. Burying it in message metadata makes it unqueryable.
- **Place is a hierarchy.** "South Bay" ⊂ "SF Bay Area" ⊃ "San Francisco". A trip to SF must match a South Bay promise with a *proximity* flag ("45 min from your hotel"), not an exact-string miss. This one decision is the difference between the app working and the app being useless for the exact example that prompted it.

---

## 7. Architecture

Small on purpose. This is a single-user tool before it is a product.

```
  sources                ingestion              store              surfaces
┌──────────────┐      ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│ LinkedIn     │─────▶│ importers    │────▶│            │────▶│ Web app      │
│  export      │      │ (idempotent) │     │ Postgres   │     │ (PWA, mobile │
│ Gmail        │─────▶│              │     │ + pgvector │     │  first)      │
│ Granola      │─────▶│ extraction   │     │            │     ├──────────────┤
│ Calendar     │─────▶│ (Claude)     │     │ object     │     │ Trip brief   │
│ Attio        │◀────▶│              │     │ store for  │     │ Radar        │
│ Lusha        │◀─────│ enrichment   │     │ raw dumps  │     │ Sweep inbox  │
│ Gojberry     │◀────▶│ scoring      │     │            │     ├──────────────┤
└──────────────┘      └──────────────┘     └────────────┘     │ Push / daily │
                             ▲                                 │ digest       │
                             └──── nightly + on-trip-change ───└──────────────┘
```

- **Store:** Postgres + pgvector. SQLite is enough for a single user, but the semantic search over message history wants pgvector and the multi-user path wants Postgres anyway.
- **Extraction:** Claude for promise extraction, why-now generation, and drafting. Batch the historical import, stream the ongoing sweep.
- **Scoring:** plain code, not a model. It must be explainable and tunable by hand.
- **Frontend:** mobile-first PWA. The moment of use is standing in a hotel lobby with 40 free minutes, not sitting at a desk.
- **Jobs:** nightly re-score; re-score immediately when a trip is created or its dates change.

### Privacy

This system holds your complete private message history with thousands of people, including their words, which they did not consent to hand to a vendor.

- Self-hosted or single-tenant. No shared multi-tenant store for message bodies.
- Send the minimum to the model: the relevant thread window, not the archive.
- Message bodies encrypted at rest; only derived objects (promises, scores) in the hot path.
- Hard delete of a person removes their messages, not just their row.
- Never auto-send. Drafts are drafts. The user presses send, every time.

---

## 8. Build plan

**Phase 1 — "the forgotten invitations" (≈2 weeks).** The whole point is to prove value before building any travel machinery.
- Import LinkedIn export: connections + full message archive
- Promise extraction over the entire history
- One screen: every open promise, ranked by warmth × age, each with its quote and a draft reply
- Confirm / dismiss / mark-done, and the feedback captured

*Ships as a useful product on its own.* If this screen isn't compelling, stop.

**Phase 2 — trips.** Manual trip creation. Place hierarchy + proximity matching. Enrich locations for the top few hundred contacts. Trip Brief with ranked cards, grouped by play type, with drafts. Calendar read for free slots.

**Phase 3 — ambient.** Calendar and flight-email trip detection. Ongoing sweep of new messages. Daily digest and pre-trip push ("You land in SF Tuesday — here are your five"). Granola and Attio wired in; interactions written back.

**Phase 4 — sharpen.** Investor and partner fit profiles as editable plain-language rules. Live signals (job changes, funding, posts). Feedback-tuned weights. Optional live LinkedIn read.

---

## 9. Open decisions

1. **Live LinkedIn read** — accept the ToS/account risk for freshness, or stay on monthly exports? Affects Phase 4 and nothing before it.
2. **Single-user tool or product?** The design above is single-user. Making it a product mostly changes privacy architecture and the LinkedIn access story, both of which get harder, not easier.
3. **Enrichment budget** — location enrichment on 4,000 contacts is real money. Proposal: enrich top 300 by score, plus anyone with an open promise, plus on-demand.
4. **How aggressive should nudges be?** Recommendation: one pre-trip brief, one daily digest while travelling, nothing else. An app that pings you about people is an app you mute.
5. **Whose voice do drafts use?** Needs a style sample from your real sent messages, or every draft reads like a sales sequence and you'll rewrite all of them.
