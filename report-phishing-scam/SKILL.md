---
name: report-phishing-scam
description: Draft abuse reports for a phishing or smishing (scam text/email) message — to the domain's registrar and to the impersonated brand or authority (USPS, FedEx, UPS, DHL, Amazon, Apple, IRS, a bank, etc.). Use when the user shares a screenshot or the text of a suspicious "delivery," "account," "payment," or "refund" message and wants to report it, get it taken down, or "report this phishing text/email," "draft an abuse report," "report this scam domain."
license: MIT
metadata:
  author: Mitchell Lubbers
  tags: phishing, smishing, abuse-report, security, email
---

# Report Phishing / Smishing

Goal: turn one phishing screenshot or text into ready-to-send abuse reports — one to whoever registered the scam domain, one to the real organization being impersonated (or a universal clearinghouse if there isn't a specific one) — with minimal back-and-forth with the user.

This is a reporting/takedown workflow, not a security investigation. Never click the phishing link, never navigate a browser to it, and never tell the user to reply to the message (even "STOP" or "Y") — replying just confirms to the scammer that the number or address is live.

## 1. Gather the evidence

You need:
- The full text of the message (paste, or read it from an uploaded screenshot).
- A screenshot or text detail that shows **who it came from** (sender phone number or email address) **and when** it was received. Many chat-app screenshots crop this out by default — if the first screenshot you're given only shows the message bubble, ask the user for a second screenshot of the conversation header (or just ask them to type out the sender's number/address and the date/time).

Don't block on the second detail forever — if the user only has the message text, proceed with what you have and just skip the fields that need it (see step 5).

## 2. Identify the impersonated brand

Read the message for who it claims to be from (USPS, FedEx, UPS, DHL, Amazon, a bank, the IRS, Apple, etc.).

Check `references/brand_reporting_contacts.md` for a known reporting address for that brand. If the brand isn't listed there:
- WebSearch `"<brand name>" report phishing email official` to find a current address, or
- Fall back to the universal contacts in that same reference file (APWG, FTC, IC3) — don't leave the brand-specific report out entirely just because it's not in the list; a two-minute search usually finds one.

Brand-specific reports matter even when a universal option exists — the real organization's fraud team can flag accounts or transactions tied to the scam in ways a registrar or the FTC can't.

## 3. Extract and normalize the phishing domain

Pull the URL out of the message and reduce it to the root registrable domain — abuse reports go to whoever registered that domain, not the fake subdomain the scammer prepended.

Example: `usps.lvbkg.shop` → registrable domain is `lvbkg.shop`.

## 4. Find the registrar's abuse contact

WebFetch `https://www.whois.com/whois/<root-domain>` with a prompt like "What is the registrar name and abuse contact email listed for this domain?"

- If that comes back empty or shows a security-check/CAPTCHA page instead of data, retry once, then fall back to WebSearch `"<domain>" whois registrar abuse email`.
- If you still can't find one, tell the user you couldn't resolve the registrar automatically and point them to ICANN Lookup (https://lookup.icann.org/en/lookup) to check manually — don't guess at an abuse address.
- Treat `whois.com` as a starting point, not the only option — if it ever stops working, try another public WHOIS lookup site the same way.

## 5. Draft the reports

Draft, don't send. Use whatever email tool is connected (e.g. a Fastmail or Gmail MCP connector) to create **drafts** the user reviews and sends themselves. If no email tool is connected, output both drafts as text/markdown for the user to copy.

**Draft A — to the registrar's abuse address**
Subject: `Phishing domain report — <domain>`
Body should include: the domain and full URL, what brand it's impersonating, the date the message was received, the full message text (or a close paraphrase), and a request to investigate and suspend the domain per the registrar's Acceptable Use Policy.

**Draft B — to the impersonated brand (or universal fallback)**
Follow that specific brand's stated format from the reference file — some want a subject line convention (IRS), some want the message forwarded as an attachment (Amazon, APWG), some want a screenshot with sender number and timestamp (USPS, IRS smishing, DHL). If the brand isn't listed and you didn't find one in step 2, draft to `reportphishing@apwg.org` instead and mention `reportfraud.ftc.gov` as a next step in your reply to the user.

**If it's a text message from a plausible US number**, add one line to your final summary (not a drafted email) reminding the user to forward the original text to **7726** — that's a carrier-level spam report, separate from and in addition to the email reports above, and doesn't require drafting anything.

### Known limitation — don't try to attach the screenshot yourself
Do not attempt to base64-encode the screenshot through Read/Bash and pass it into an email tool's attachment parameter. Even a small PNG blows past what's practical to move through a single tool call and will fail, truncate, or burn an enormous amount of context. Leave attaching the screenshot(s) as a manual step for the user and say so explicitly — e.g. "drag the screenshot in before you hit send."

## 6. Wrap up

Give the user a short summary: the domain and registrar you found, which brand-specific address you used (or the fallback you used instead), and the manual steps still left (attach screenshot(s), forward to 7726 if applicable, review and send). Keep it tight — they don't need a recap of your process, just what's left for them to do.
