# LinkedIn Post — Bala's GTM Engineering Origin Story

---

June 2025. 150 demo calls in. I thought I was becoming a better SDR.

I was wrong.

Follow-up was breaking me. Quoted leads going cold. No system.

Just me, a spreadsheet, and manual sequences that couldn't keep up with the pipeline I was building.

That wall pushed me into n8n. Zero coding background. Couldn't parse the jargon. Watched Nick Saraev and Lead Gen Jay on YouTube — about 12 hours total.

Then shipped my first workflow: Apify scrape into personalized LinkedIn messages, sent through PhantomBuster.

It worked. Then it didn't scale. Things broke and I didn't know why. I couldn't read the errors.

So I went deeper. Learned webhooks. Built: Google Sheet → generate personalized cold email → write back to Sheet → feed into ReachInbox. Positive replies routed into Close CRM and Aimfox.

Then I noticed the problem: n8n ran on my local machine. When I shut my PC, the workflow died. I spent weekends at the office keeping it alive.

Then I tried Clay.

500 leads enriched in 10 minutes. The same job took hours in n8n.

That was the moment. Not because Clay was faster. Because it forced a distinction I hadn't made: n8n is for custom logic. Clay is for scale and enrichment. Not substitutes. Different layers of the same stack.

I wasn't optimizing SDR work anymore. I was building systems.

The label GTM Engineer arrived after that. Not before.

---

Beginners fixate on the label. They should fixate on the bottleneck.

You don't "learn GTMe." You hit a wall, solve it end-to-end, hit the next wall, solve that. The stack builds itself around the problems you keep running into.

Here's how I'd structure the first 90 days if I were starting today:

Days 1–30: Pick one bottleneck in your current role. Not a tool. A problem.
Solve it end-to-end with free tools. Ship ugly. Break it. Fix it.
Shipping is the teacher. Courses aren't.

Days 31–60: Add the adjacent layer. A webhook. A CRM integration. A second tool that handles what the first one can't.

Days 61–90: Wire two workflows together so they talk without you touching them.

The foundation under all of this: know why you're building before you decide what to build.
Pair that with "everything is figureoutable" — because everything breaks, and fixing it is the job.
Surface-level code helps. Not full-stack. Enough to read a payload and debug a webhook.

No CS degree. I didn't know a webhook from a payload 10 months ago.

Everything I learned was free. YouTube was the library. Time was the tuition.

What was the first bottleneck that pulled you into automation? Drop it below.

---

*Diagram placement suggestion:*
- `actual-path.png` → image 1 in the LinkedIn carousel (after the hook reads)
- `prescribed-path.png` → image 2 (after the application section)
