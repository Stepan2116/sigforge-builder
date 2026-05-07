# SigForge Frontend

Public showcase dashboard for SigForge strategies.

## Live demo

🌐 **https://sigforge.dev/showcase.html**

Append `?tour=1` to auto-start the 8-step guided tour:
🌐 **https://sigforge.dev/showcase.html?tour=1**

## Architecture

- Single HTML file (`showcase.html`) — vanilla JS, no build step
- Fetches `/api/showcase` every 30 seconds
- Cyberpunk-matrix theme matching SigForge brand
- Tour mode renders 8 step modal overlay with tile spotlight

## API endpoint

```
GET /api/showcase
```

Returns normalized PnL/WR data for all original SigForge strategies. Aggregated from individual strategy state files. Serves only original (non-fork-derived) strategies.

Example response:
```json
{
  "ts": 1777996575392,
  "arb_paper": {
    "balance": 465.21,
    "starting_balance": 500,
    "equity": 505.93,
    "pnl": 5.93,
    "won": 9,
    "lost": 0,
    "open": 3,
    "closed": 9,
    "win_rate": 1
  },
  "cointrick": {...},
  "esports_copy": {...},
  "sport_paper": {...},
  "poly_mm_paper": {...}
}
```

## Customization

To deploy your own clone:
1. Copy `showcase.html` to your nginx public root
2. Implement `/api/showcase` returning the schema above
3. Update tile descriptions in the `STRATS` JS array
4. Update tour content in the `TOUR` JS array
5. Add nginx public location (no auth) for `/showcase.html` and `/api/showcase`
