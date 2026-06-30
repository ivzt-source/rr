# Cold Lead SMS Opener

First text sent to a brand-new lead. The goal of this opener is to open a
conversation **without pressure** — acknowledge that we don't know if now is a
good time to talk, and let the lead choose the channel: a quick call right now,
or keep it to SMS.

## The addition (why this opener changed)

Old openers jumped straight to "can we book a call?" That assumes the lead is
free and ready to talk, which a cold lead usually isn't. The new opener:

1. **Acknowledges the timing** — "not sure if now's a good time."
2. **Offers a live call as an easy option** — "if you're free now, happy to
   jump on a quick call."
3. **Gives a low-friction fallback** — "otherwise, no worries, we can keep it
   to SMS."

This lets the lead self-select into whichever channel feels comfortable, which
keeps cold leads engaged instead of going quiet.

## Primary opener

> Hi [Name], it's [Your Name] from [Company]. Not sure if now's a good time to
> chat — if you're free to jump on a quick call right now, happy to do that.
> Otherwise no worries, we can keep it to SMS. Either works for me 👍

## Shorter variant

> Hi [Name], [Your Name] here from [Company]. Not sure if now suits — happy to
> hop on a quick call now if you're free, or we can just SMS. Whatever's easier
> for you 🙂

## Most casual variant

> Hey [Name], it's [Your Name] from [Company]. Didn't want to assume now's a
> good time — if you're around for a 2-min call I can ring you, otherwise we
> can sort everything over text. Up to you!

## Notes for the workflow

- **Placeholders:** `[Name]`, `[Your Name]`, `[Company]` are merged from the
  lead record before sending.
- **Tone:** friendly and optional — never "book a call" framing. The lead picks
  the channel.
- **Follow-up branches:**
  - If they reply *"call me"* / *"now is fine"* → trigger the call step.
  - If they reply over SMS → continue the SMS qualifying sequence.
  - If no reply → standard cold-lead follow-up cadence.
