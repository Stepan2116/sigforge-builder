# SigForge — GitHub Sponsors Setup

> *Recurring monthly contributions tied to the Stepan2116 GitHub profile.
> Lower per-contribution amount than grant programs, but accumulates and
> creates ongoing engagement.*

---

## What this is

GitHub Sponsors is GitHub's built-in funding program. Users sponsor
specific developers with monthly recurring payments. For SigForge:

- Sponsors fund Stepan Riznyk's developer profile (not the repo directly)
- The sponsorship signal appears on the SigForge repo via a `Sponsor` button
- Stripe handles payment processing
- GitHub takes 0% fees during the first year of an account, ~10% thereafter

**Realistic yield:** $0-$200 per month early on, can grow if community
forms around the repo. Not a primary funding source but creates
continuous engagement and signals project legitimacy.

---

## Setup checklist (Бос does this — ~30 minutes)

### Step 1: Activate GitHub Sponsors

1. Go to https://github.com/sponsors
2. Click "Join the waitlist" or "Get started" if available
3. Verify GitHub account (Stepan2116)
4. Provide tax info — GitHub requires:
   - Country (Ukraine)
   - Tax ID (none required for individuals in many countries)
   - Bank account (for payouts)
   - Identity verification (passport / national ID)

Approval takes 1-2 weeks typically.

### Step 2: Configure sponsor profile

Once approved, customize the sponsor profile page:

**Welcome message:**
```
Building SigForge — an open-source validation framework for prediction-market trading on Polymarket and beyond.

Five weeks of self-funded work has delivered:
- Universal backtester with 23 unit tests + GitHub Actions CI
- Process watchdog for silent-failure detection
- 13 KB methodology document
- 4 strategy specs (BASKET Sharpe 3.10 verified, YIELD-FARM, SPORT-SNIPER, COPY-TRADER)
- Live public showcase with real-time metrics

Your sponsorship funds:
- Continued open-source maintenance
- Multi-platform adapters (Manifold, Kalshi)
- Documentation and onboarding for first community contributors
- AWS infrastructure costs (~$40/month)

Live showcase: http://18.178.69.19/showcase.html?tour=1
Repo: https://github.com/Stepan2116/sigforge-builder
```

**Featured work:**
- `Stepan2116/sigforge-builder` (the repo)

### Step 3: Set tier descriptions

Recommended tiers:

```
🌱 $5/month — Supporter
"Thanks for backing the project. You get early access to monthly status posts and our gratitude. Mostly: this funds AWS costs and keeps the lights on."

🔬 $25/month — Researcher
"Above plus: priority replies on strategy questions, early access to new strategy specs before they hit the public repo, and your name in our annual contributor list."

🛠 $100/month — Builder
"Above plus: monthly Discord/Telegram call discussing new strategy ideas, code review on your own strategy variants if you build them with the framework."

🏛 $500/month — Patron
"Above plus: direct collaboration on a research question or strategy idea you want explored. Pricing reflects the time commitment, not gatekeeping. Mostly we expect zero of these."
```

### Step 4: Add Sponsor button to repo

Edit `.github/FUNDING.yml` (we'll commit this):

```yaml
github: [Stepan2116]
```

This makes a "Sponsor" button appear on the repo page next to "Watch / Star / Fork."

### Step 5: Add sponsorship link to showcase

Update `frontend/showcase.html` footer to include:

```html
<a href="https://github.com/sponsors/Stepan2116" target="_blank">Sponsor on GitHub</a>
```

### Step 6: First public mention

When everything is live:
1. Tweet (or X-thread reply): "GitHub Sponsors live for SigForge — recurring support helps keep the lights on while we ship the open-source release."
2. Add to README under repository badges:
   ```markdown
   [![Sponsor](https://img.shields.io/github/sponsors/Stepan2116?label=Sponsor&logo=github)](https://github.com/sponsors/Stepan2116)
   ```

---

## What gets committed to repo (my part — done в next commit)

I will add:

1. **`.github/FUNDING.yml`** with `github: [Stepan2116]` placeholder.
2. **`README.md`** sponsor badge added near top.
3. **`frontend/showcase.html`** footer gets sponsor link.

These activate automatically once Бос completes the GitHub Sponsors profile
verification (Step 1-3 above).

---

## Realistic expectation

GitHub Sponsors yields are bimodal:
- Early (months 0-3): $0-50/month
- After community forms (months 6-12): $50-300/month if framework gets
  real adoption
- Long-tail (year 1+): can grow to $500+/month if open-source release
  gets meaningful traction

It's recurring revenue that compounds over time. The setup cost (~30 min
of Бос's time + my repo changes) is trivial.

This is **strategy supplement**, not strategy primary. Use it alongside
grant applications, not instead of them.

---

## Anti-pattern

Don't:
- Tweet "please sponsor me" repeatedly. Reads as desperate.
- Set high minimum tiers ($50/month minimum) — kills onboarding.
- Treat sponsors as customers expecting deliverables. Sponsorship is
  voluntary support, not a contract.

Do:
- Mention sponsorship link once in monthly updates, then leave it alone.
- Acknowledge new sponsors in changelog or monthly blog.
- Keep tier descriptions honest about what they actually get.

---

## See also

- Other grant applications: `application/form-fields.md`,
  `application/manifold-application.md`, `application/gitcoin-application.md`,
  `application/octant-application.md`.
- Multi-grant index: `application/other-grants-index.md`.
