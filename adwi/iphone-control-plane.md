# Adwi iPhone Control Plane — Setup Guide

## Architecture

```
iPhone (Siri Shortcut / Home app) 
   → Home Assistant companion app (:8123)
      → Home Assistant REST → n8n webhook (:5678)
         → Safe Command API (:5055)
            → adwi / bin scripts
```

For remote access (off-network):
```
iPhone → Tailscale mesh VPN → Open WebUI (:3000) or Home Assistant (:8123)
iPhone → Cloudflare Tunnel → n8n webhook (for inbound triggers like Telegram bot)
```

---

## Step 1: Start Home Assistant

```bash
cd ~/SuneelWorkSpace/adwi/infra/docker
docker compose up -d homeassistant
```

Visit: http://localhost:8123

Complete the onboarding wizard. Create an account.
Go to Settings → Devices & Services → Create a Long-Lived Access Token (save it).

Add to config/.env:
```
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=<your_long_lived_token>
```

---

## Step 2: Configure Tailscale (remote access)

Tailscale is already installed. You just need to authenticate:

```bash
sudo tailscale up --accept-routes
```

Then open https://login.tailscale.com in a browser and authenticate.

Once connected, your Mac's Tailscale IP (e.g., 100.x.x.x) gives you:
- Open WebUI at: http://100.x.x.x:3000
- Home Assistant at: http://100.x.x.x:8123
- n8n at: http://100.x.x.x:5678

On your iPhone: install Tailscale from the App Store, sign in with the same account.
You now have end-to-end encrypted access to all services from anywhere.

---

## Step 3: Cloudflare Tunnel (inbound webhooks)

Used strictly for inbound webhook triggers (e.g., Telegram bot → n8n). 
Does NOT expose your IP or router.

1. Go to https://one.dash.cloudflare.com → Tunnels → Create a tunnel
2. Name it "adwi-n8n"
3. Copy the tunnel token
4. Add to config/.env: `CLOUDFLARE_TUNNEL_TOKEN=<token>`
5. In the tunnel dashboard, add a public hostname pointing to `n8n:5678`
6. Start cloudflared: `docker compose up -d cloudflared`

Your n8n will now receive webhooks at: https://adwi-n8n.<your-subdomain>.cfargotunnel.com

---

## Step 4: n8n Webhook Endpoints for iOS Shortcuts

Import these 3 workflows into n8n (http://localhost:5678):

### Workflow 1: Morning Brief on Demand
- Trigger: Webhook POST /webhook/morning-brief
- Action: HTTP Request → http://localhost:5055/daily-ai-status-report
- Response: Return the report text

### Workflow 2: Pending Approvals
- Trigger: Webhook POST /webhook/pending-approvals
- Action: Read File → ~/Desktop/morning_brief.md
- Action: Extract "Pending User Approval" section with text manipulation
- Response: Return extracted text

### Workflow 3: Force Nightly Maintenance
- Trigger: Webhook POST /webhook/run-nightly
- Auth: Header check (set a secret in the header)
- Action: HTTP Request → http://localhost:5055/auto-ai-maintenance
- Response: Return result

---

## Step 5: iOS Siri Shortcuts

### "Run Morning Brief"
1. Open Shortcuts app → New Shortcut
2. Add action: "Get Contents of URL"
   - URL: http://100.x.x.x:5678/webhook/morning-brief (your Tailscale IP)
   - Method: POST
3. Add action: "Show Result"
4. Add Siri phrase: "Run morning brief"

### "What Needs My Approval?"
1. Same pattern → POST to /webhook/pending-approvals
2. Show result in notification

### "Force Nightly Maintenance"
1. POST to /webhook/run-nightly with secret header
2. Show "Maintenance started" notification

### Apple Watch
In Shortcuts app, for each shortcut:
- Enable "Show on Apple Watch" in shortcut settings
- They appear in the Shortcuts complication on Watch

---

## Step 6: Home Assistant Automations

Add to homeassistant-data/configuration.yaml:

```yaml
rest_command:
  adwi_morning_brief:
    url: "http://host.docker.internal:5678/webhook/morning-brief"
    method: POST
  adwi_nightly:
    url: "http://host.docker.internal:5678/webhook/run-nightly"
    method: POST
  adwi_status:
    url: "http://host.docker.internal:5055/status-ai"
    method: GET
```

Then create a dashboard button that calls `rest_command.adwi_morning_brief`.

---

## Port Reference

| Service | Local Port | Via Tailscale | Via Cloudflare |
|---|---|---|---|
| Open WebUI | :3000 | 100.x.x.x:3000 | — |
| n8n | :5678 | 100.x.x.x:5678 | tunnel (webhooks only) |
| Home Assistant | :8123 | 100.x.x.x:8123 | — |
| Safe Command API | :5055 | internal only | — |
| Obsidian Bridge | :5056 | internal only | — |
| Phoenix (traces) | :6006 | 100.x.x.x:6006 | — |

---

## Security Notes

- Tailscale: only devices on your Tailnet can connect — no open ports
- Cloudflare Tunnel: only /webhook routes exposed, n8n validates a secret header
- Home Assistant: protected by HA login, never exposed to public internet
- Safe Command API: only 8 allowlisted commands, no arbitrary shell access
