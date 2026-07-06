# Business Ideas — App Build Inventory

> **Goal:** Go through the business ideas and identify which ones are *an app
> that needs to be built* (targeting a build with **Fable 5**).
>
> **Scope note:** This inventory is built from the four ideas named directly in
> the session on 2026-07-06. A stored master list could not be located in the
> connected accounts (Slack + Gmail searched — no ideas list found; not in the
> `rr` repo either). Add any further ideas to the "Backlog / To classify"
> section and they'll get slotted in.

## Legend

- 🟢 **Build** — a standalone app that should be built.
- 🟡 **Clarify** — an app, but the scope/product needs one decision before build.
- ⚪ **Not an app** — a feature, component, or non-app idea (don't scaffold as its own app).

---

## Apps to build

| # | Idea | Verdict | What it most likely is | Build-ready? |
|---|------|---------|------------------------|--------------|
| 1 | **Be Paid** | 🟢 Build | A get-paid / invoicing + payment-collection app (send a request, client pays). | Needs a one-line scope (see below) |
| 2 | **Real Estate Photos app** | 🟢 Build | App for property listing photos — capture/upload, AI enhancement, and delivery to agents. | Yes |
| 3 | **Website Builder – Login** | 🟡 Clarify | Either a full website-builder product, or just the auth/login module of one. | Decide: whole product vs. login module |
| 4 | **Blossy** (flowers) | 🟢 Build | A flowers app — likely florist ordering/delivery or a flower/plant-care companion. | Needs a one-line scope (see below) |

---

## Per-idea detail

### 1. Be Paid — 🟢 Build
- **Type:** App (standalone).
- **Assumed product:** A lightweight tool to request and collect payment — create
  a payment request/invoice, send a link, get paid, track status.
- **Open question:** Is this **invoicing-first** (send an invoice, reconcile) or
  **payment-link-first** (tap → pay, minimal invoicing)? One answer sets the MVP.
- **Fable 5 MVP:** Create request → shareable pay link → status (paid/unpaid) →
  simple list of requests.

### 2. Real Estate Photos app — 🟢 Build
- **Type:** App (standalone). Clearest "build this" of the set.
- **Assumed product:** Agents/photographers capture or upload listing photos;
  app enhances (lighting/sky/declutter) and packages them for the listing.
- **Fable 5 MVP:** Upload photos → auto-enhance → gallery per property → download/share set.
- **Note:** No blocking decision — good candidate to start first.

### 3. Website Builder – Login — 🟡 Clarify (likely a component, not a whole app)
- **Type:** Ambiguous. As written, "Website builder **login**" reads like the
  **auth screen of a website-builder product**, not a standalone business.
- **Two readings:**
  - **(a)** You want the whole **website builder** product → big build, its own app.
  - **(b)** You just need the **login/auth module** → a component inside another app,
    not a business idea on its own.
- **Recommendation:** Treat as ⚪ "not its own app" unless you confirm you mean (a).

### 4. Blossy (flowers) — 🟢 Build
- **Type:** App (standalone).
- **Assumed product:** A flowers app. Most likely **florist ordering + delivery**
  (browse → order → deliver), possibly a **flower/plant-care** companion instead.
- **Open question:** Commerce (sell/deliver flowers) or care/utility (identify,
  water reminders, arrangement guides)?
- **Fable 5 MVP (commerce reading):** Browse bouquets → order → delivery details → confirmation.

---

## Recommended build order for tomorrow (Fable 5)

1. **Real Estate Photos app** — no open decisions, start here.
2. **Be Paid** — start once invoicing-vs-payment-link is chosen (30-second call).
3. **Blossy** — start once commerce-vs-care is chosen.
4. **Website Builder – Login** — only if you confirm you want the *full builder*;
   otherwise it's a login module folded into whichever app needs auth.

## Backlog / To classify

_None yet beyond the four above. Paste any other ideas here (or point me at the
list) and I'll classify each as 🟢 Build / 🟡 Clarify / ⚪ Not an app._
