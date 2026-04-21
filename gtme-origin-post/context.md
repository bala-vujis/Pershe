# Context: Bala's GTM Engineering Origin Story

Source material for LinkedIn ghostwriting. Every claim in any post must trace back here.

---

## The trigger (June 2025, at Vujis)

- Working as the sole GTM/SDR owner at Vujis.
- Had taken ~150 demo calls.
- Hit a wall: quoted leads needed systematic follow-up. No system existed. Doing it manually was breaking him.
- That bottleneck pushed him into automation.
- **Key point:** he did NOT think he was becoming a GTM Engineer. He thought he was becoming "an optimized SDR." The label came later.

---

## The first real tool: n8n

- Opened n8n with zero coding background.
- Couldn't parse coding jargon. Learning curve was brutal.
- Watched Nick Saraev (~5 hours) and Lead Gen Jay (~7 hours) on YouTube. Roughly 12 hours of focused input.
- First shipped workflow: Apify scrape → personalized LinkedIn messages → sent through PhantomBuster.
- First failure: couldn't scale. Didn't understand the jargon. Didn't know what was breaking when it broke.

---

## The scaling fail

- Built a cold email personalization workflow: Google Sheet → generate personalized cold email → write back to Sheet → feed into ReachInbox (sequencer).
- Built webhooks that routed positive replies from ReachInbox into Close CRM and Aimfox (LinkedIn campaign tool).
- Problem: n8n ran on his local machine. When he shut his PC, the workflow died. Weekends at the office to keep things running.
- This forced him to learn webhooks and APIs properly.

---

## The unlock: Clay.com

- Tried Clay. Enriched 500 leads in ~10 minutes.
- The same job in n8n took hours.
- Realization: n8n is for unique, custom logic. Clay is for scale and enrichment. They're not substitutes — they're different layers of the stack.
- **This is the moment the "GTM Engineer" label clicked. He wasn't optimizing SDR work anymore. He was building systems.**

---

## The foundation (non-negotiable)

- Business understanding — you have to know why you're building before what you're building.
- "Everything is figureoutable" mindset — everything breaks, and you fix it. That's the job.
- Surface-level coding — not full-stack, but enough to read a payload, debug a webhook, modify a script.

---

## Teachers / influences

- Nick Saraev (YouTube) — n8n fundamentals.
- Lead Gen Jay (YouTube) — outbound mechanics.
- Hormozi basics — offer / value framing (optional tag in comments).
- Everything he learned was free. YouTube was the library. Time was the tuition.
- A few colleagues at Vujis helped, but he built every system end-to-end himself.

---

## His advice for someone starting today

- You don't "learn GTMe." You hit a bottleneck, solve it end-to-end, hit the next one, solve that. The stack builds itself.
- Start with the problem, not the tool.
- Ship ugly. Break it. Fix it. Courses don't teach this — shipping does.
- Portfolio = internal tools built with Claude Code / vibe coding, or a real workflow running end-to-end.
- Prior background (SDR, marketer, ops) isn't a disadvantage. SDR background is actually an advantage — you've felt the pain you're automating away.

---

## The hot take (defensible from his story)

"I thought I was becoming a better SDR. I was wrong. I was becoming a GTM Engineer and didn't know it yet." The label arrives after the work. Beginners fixate on the title. They should fixate on the bottleneck.

---

## The myth to kill

You need a CS background to be a GTMe. He didn't. Surface-level code + figureoutable mindset + business understanding is the real stack.

---

## The #1 waste for beginners (3 months lost)

Course-hopping and tool-hopping. Watching 40 hours of content, buying 3 paid courses, jumping between n8n / Make / Zapier / Clay without shipping one thing end-to-end. Shipping is the teacher.
