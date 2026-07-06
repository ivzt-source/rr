# Business Ideas — App Build Inventory

> **Goal:** Go through the business ideas and identify which ones are *an app
> that needs to be built* (targeting a build with **Fable 5**).
>
> **Scope note:** This inventory currently covers the four ideas being taken
> forward as named in-session on 2026-07-06. The **full master list lives in a
> separate directory/repo** (not `rr`, and not on this machine's filesystem —
> both scanned). It also includes a recent SaaS-idea research pass (sources:
> koenwr's channel/office + other business podcasts, YouTube channels, and social
> profiles). Once that directory is added to the session I'll scan it and slot
> every idea into the table below.

## Legend

- 🟢 **Build** — a standalone app that should be built.
- 🟡 **Clarify** — an app, but the scope/product needs one decision before build.
- ⚪ **Not an app** — a feature, component, or non-app idea (don't scaffold as its own app).

---

## Apps to build

| # | Idea | Verdict | What it most likely is | Build-ready? |
|---|------|---------|------------------------|--------------|
| 1 | **Real Estate Photos app** | 🟢 Build | App for property listing photos — capture/upload, AI enhancement, and delivery to agents. | Yes |
| 2 | **Blossy** (flowers) | 🟢 Build | Local florist ↔ recipient preference-matching app. Recipients save flower preferences; the florist looks them up so a gift buyer gets flowers the recipient will actually love. | Yes — scope defined |
| 3 | **Be Paid** | 🟢 Build | A get-paid / invoicing + payment-collection app (send a request, client pays). | Needs a one-line scope (see below) |
| 4 | **Round Up** (for charity) | 🟢 Build | Rounds up everyday purchases to the nearest dollar and donates the spare change to a chosen charity. | Needs a transaction data source (or manual/demo mode for v1) |

**Dropped:** ~~Website Builder – Login~~ — not an idea Tzvi wants to build. Removed
from the list per 2026-07-06.

---

## Per-idea detail

### Be Paid — 🟢 Build
- **Type:** App (standalone).
- **Assumed product:** A lightweight tool to request and collect payment — create
  a payment request/invoice, send a link, get paid, track status.
- **Open question:** Is this **invoicing-first** (send an invoice, reconcile) or
  **payment-link-first** (tap → pay, minimal invoicing)? One answer sets the MVP.
- **Fable 5 MVP:** Create request → shareable pay link → status (paid/unpaid) →
  simple list of requests.

### Real Estate Photos app — 🟢 Build
- **Type:** App (standalone). Clearest "build this" of the set.
- **Assumed product:** Agents/photographers capture or upload listing photos;
  app enhances (lighting/sky/declutter) and packages them for the listing.
- **Fable 5 MVP:** Upload photos → auto-enhance → gallery per property → download/share set.
- **Note:** No blocking decision — good candidate to start first.

### Blossy (flowers) — 🟢 Build
- **Type:** App (standalone, two-sided: recipients + florists).
- **Product (defined):** A **local florist ↔ recipient preference-matching** app.
  Recipients (the people who *receive* flowers) save their flower preferences to a
  "Blossy profile." A gift buyer (e.g. a husband) walks into a local florist; the
  florist looks up the recipient's profile by **phone number and/or home address
  (for delivery)** and assembles flowers the recipient will actually love.
- **Core problem it solves:** *"Which flowers should I buy?"* — the recipient has
  effectively pre-answered by saving their preferences, so the buyer doesn't guess
  and the florist doesn't have to interrogate a clueless gift buyer.
- **Why it works:** It's **local**. Recipients are already known to neighbourhood
  florists (they often shop there themselves), so lookup-by-phone/address is
  natural and trust already exists.
- **Two sides to build:**
  - **Recipient app** — create profile, set preferences (flower types, colours,
    scents, allergies/dislikes, arrangement style), control lookup by phone/address.
  - **Florist tool** — search a recipient by phone number or delivery address,
    view their preference profile, build the order to match.
- **Fable 5 MVP:** Recipient onboards → saves preferences → gets a lookup key
  (phone/address). Florist enters that key → sees the preference profile.
- **Key design questions (not blocking a v1):**
  - **Privacy/consent** — profiles are looked up by phone/address, so a recipient
    must opt in and control who can see what (surprise-gift vs. privacy tension).
  - **Recipient acquisition** — the network only works once enough local recipients
    have profiles; florists likely drive signups ("save your Blossy so you always
    get flowers you love").

### Round Up (for charity) — 🟢 Build
- **Type:** App (standalone), fintech/giving.
- **Product:** Rounds each everyday purchase up to the nearest dollar and donates
  the spare change to a charity the user picks (e.g. $4.30 spend → $0.70 donated).
- **Core dependency:** to round up *real* spend you need access to transactions —
  open-banking / card-linked data (Basiq or Plaid in AU, or a card partner). That's
  the one thing that makes this heavier than the others.
- **Fable 5 MVP (demo-friendly, no bank integration):** user picks a charity →
  logs/imports purchases (manual or mock feed) → app rounds each to the nearest
  dollar → running "spare change" total → simulated donation + receipt/history.
- **Open questions (not blocking a demo):**
  - **Money movement** — who holds and disburses the funds (a charity partner, a
    payments provider)? Real donations need a compliant path.
  - **Single charity vs. choice** — one cause, or a directory the user selects from?

---

## Recommended build order for tomorrow (Fable 5)

1. **Real Estate Photos app** — no open decisions, start here.
2. **Blossy** — scope is now defined (recipient profile + florist lookup); ready to build.
3. **Be Paid** — start once invoicing-vs-payment-link is chosen (30-second call).
4. **Round Up** — buildable as a demo tomorrow; a *real* version waits on a
   transaction data source + a compliant way to move the donations.

_(Website Builder – Login was dropped — not a build Tzvi wants.)_

**Provenance note:** **Be Paid** came out of an earlier Reddit-data mining pass
(codename **"Bereshit"**). That same run surfaced other candidate ideas — those
belong in the "Backlog / To classify" section once the research output is pulled
into the session.

## Backlog / To classify

_None yet beyond the four above. Paste any other ideas here (or point me at the
list) and I'll classify each as 🟢 Build / 🟡 Clarify / ⚪ Not an app._
