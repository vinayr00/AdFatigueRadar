# AdFatigueRadar — Training Datasets & Section 10 Taxonomy Labeling Guide
======================================================================
PERSON 1: AI / NLP Layer

## 1. Dataset Overview & Split Breakdown

This directory contains the training and validation datasets used to train the Stage 2 taxonomy classifier and fit the temperature calibration parameters.

- **`labels.jsonl` (Train Split)**: 640 records (exactly 80 per category across all 8 classes).
- **`val_labels.jsonl` (Validation Split)**: 160 records (exactly 20 per category across all 8 classes).
- **`source_manifest.json`**: Manifest documenting split counts, synthetic provenance, and leak-free verification.
- **Disjointness Guarantee**: 0 exact and 0 near-duplicate matches (token Jaccard >= 0.85) across train/val/test/stress splits.

---

## 2. Frozen 8-Class Taxonomy Definitions (Section 6 & 10)

Every comment ingested by Person 1 must be classified into **exactly one** of the following eight categories:

| Category | Definition & Core Semantics | Typical Triggers & Cues | Harmful Weight |
| :--- | :--- | :--- | :---: |
| `product_complaint` | Physical defects, poor build quality, missing promised features, malfunction, safety hazard, or failure to perform core function. | "broke on day 2", "cheap plastic", "doesn't turn on", "false advertising", "screen glitch" | High ($w = 1.00$) |
| `service_complaint` | Post-purchase fulfillment failure: delayed shipping, missing tracking updates, lost packages, refusal of refunds, or unresponsive support. | "ordered 3 weeks ago", "support won't reply", "where is my package", "refused refund" | High ($w = 1.00$) |
| `fatigue` | Audience exhaustion caused by repeated advertisement exposure. Mentions ad frequency, algorithmic over-delivery, or annoyance at seeing the ad. | "this ad again", "seen this 50 times", "stop showing me this", "on my feed every 5 mins" | Medium ($w = 0.70$) |
| `mockery` | Direct ridicule, sarcasm, or roasts aimed at the ad creative, actors, dialogue, cringey script, or unrealistic marketing claims. | "acting is pure cringe 💀", "who approved this script", "paid actor in a basement", "cringe overload" | Medium ($w = 0.50$) |
| `spam` | Bot promotions, unrelated commercial solicitations, crypto/forex signals, telegram links, WhatsApp links, or repetitive link dumps. | "click link in bio", "guaranteed 100x crypto", "t.me/free_signals", "follow for follow" | Low ($w = 0.10$) |
| `banter_meme` | Harmless humor, cultural slang, memes, light teasing between users, or viral copypastas. **Must never be penalized as harmful.** | "bro got unspoken rizz 🔥", "let him cook", "nah he wilding fr fr", "skull emoji 💀" (friendly) | Non-Harmful ($w = 0.00$) |
| `neutral` | Informational inquiries, product questions, sizing/pricing checks, shipping availability, friend tags with no text, or non-opinionated statements. | "how much with tax?", "is this available in blue?", "does it ship to Canada?", "@username" | Non-Harmful ($w = 0.00$) |
| `positive` | Genuine satisfaction, endorsement, excitement, praise for product quality, or repeat purchase confirmation. | "love this product!", "best purchase this year", "bought again, amazing!", "super fast shipping" | Non-Harmful ($w = 0.00$) |

---

## 3. Core Disambiguation & Semantic Boundary Rules

### A. Product Complaint vs. Service Complaint
* **Product Complaint**: Focuses on the *item itself* (defective hardware, broken seams, bad smell, software bug, low quality materials).
* **Service Complaint**: Focuses on *operations, logistics, or support* (late delivery, carrier delays, ignored emails, billing charge errors).
* *Adjudication Rule*: If a comment mentions both (e.g., *"Package arrived 2 weeks late and the item inside was broken"*), assign **`product_complaint`** because physical defect represents a severe downstream safety/quality issue.

### B. Fatigue vs. Mockery
* **Fatigue**: Complains about *exposure frequency* to the advertisement itself (*"I see this ad every 2 minutes"*).
* **Mockery**: Ridicules the *content/creatives of the ad* regardless of how many times they have seen it (*"The voiceover sounds like an AI that wants to die 💀"*).
* *Adjudication Rule*: If a user roasts the ad while noting repetition (*"Why does this cringe ad keep popping up on my feed 😂"*), assign **`fatigue`** because repetitive saturation is the root driver of audience irritation.

### C. Mockery vs. Banter / Meme
* **Mockery**: Hostile or derisive ridicule directed *at the brand, product, or ad actors/script* that damages brand reputation.
* **Banter / Meme**: General internet slang, humorous engagement, or playful memes that do not diminish brand perception (*"bro really dropped a whole cinematic trailer for a water bottle 😂🔥"*).
* *Adjudication Rule*: Banter must be assigned weight 0.00 downstream. When in doubt between mild sarcasm and playful meme slang, assign **`banter_meme`** to prevent false-alarm campaign pauses.

### D. Spam vs. Repeated Genuine Complaint
* **Spam**: External solicitations (crypto, telegram, whatsapp, fake giveaways, click-farms) with zero relevance to the advertised product.
* **Repeated Genuine Complaint**: An angry customer posting *"Give me my refund!"* 5 times on different ads is **`service_complaint`**, NOT spam.

### E. Neutral vs. Positive
* **Neutral**: Objective inquiries (*"Does this work with Android?"*), feature checks (*"What is the battery life?"*), or bare mentions.
* **Positive**: Subjective praise, recommendation, satisfaction, or intent to buy (*"Need this ASAP!"*, *"Looks amazing ❤️"*).

### F. The "Again" Disambiguation Rule (Crucial)
The word *"again"* has two mutually exclusive domain meanings:
1. **Ad-Exposure Repetition $\rightarrow$ `fatigue`**:
   - *"Bro this ad again 😂"*
   - *"Seen this same ad again today"*
   - *"Why am I getting this ad again"*
2. **Repeat Purchase / Reorder $\rightarrow$ `positive`**:
   - *"Bought again, love it!"*
   - *"Ordered again, best quality ever"*
   - *"Purchased again for my brother, highly recommend"*

---

## 4. Critical Complaint Classification Criteria (Section 8)

A comment is flagged with `critical_complaint = true` **strictly** when ALL of the following criteria are met:
1. Stage 2 predicted category is **either `product_complaint` or `service_complaint`**.
2. Calibrated confidence is **$\ge 0.85$** (`CRITICAL_COMPLAINT_CONFIDENCE_THRESHOLD`).
3. **Negative Constraint**: Keywords alone (e.g., *"broken"*, *"defective"*, *"hazard"*, *"refund"*) must **NEVER** force `critical_complaint = true` if the context is banter, inquiry, or positive (e.g., *"Bro this discount is broken! Bought again"* $\rightarrow$ `critical_complaint = false`).

---

## 5. Ambiguous Examples & Adjudication Table

| Comment Text | Correct Category | Critical? | Rationale & Adjudication Rule |
| :--- | :--- | :---: | :--- |
| *"Bro this ad again 😂"* | `fatigue` | `false` | Mentions ad repetition frequency. Banter emoji does not erase fatigue signal. |
| *"Bought again, love it!"* | `positive` | `false` | "again" paired with purchase verb is strong positive repeat endorsement. |
| *"Ordered again, thank you!"* | `positive` | `false` | Repeat purchase confirmation. |
| *"Ordered 3 weeks ago, support refuses to answer or refund"* | `service_complaint` | `true` (if conf $\ge 0.85$) | Clear fulfillment & support failure. |
| *"The plastic clip snapped on day 1, completely broken defect"* | `product_complaint` | `true` (if conf $\ge 0.85$) | Direct hardware malfunction / build defect. |
| *"Bro this price is broken, such an amazing deal bought again!"* | `positive` | `false` | Slang use of "broken" in positive deal context. Keyword must not trigger complaint. |
| *"The acting in this commercial is making my teeth hurt from pure cringe 💀"* | `mockery` | `false` | Ridicule of creative performance. Negative sentiment, but category is mockery. |
| *"Bro got that unspoken rizz let him cook 🔥"* | `banter_meme` | `false` | Youth slang / viral meme. Non-harmful ($w=0.00$). |
| *"Click the link in my bio for guaranteed 100x crypto signals daily 🚀"* | `spam` | `false` | External financial bot solicitation. |
| *"What is the retail price including local sales taxes?"* | `neutral` | `false` | Objective product pricing inquiry. |
| *"Does this have an iOS app available on App Store?"* | `neutral` | `false` | Technical capability inquiry. |
| *"Idi asalu panicheyatledu display lo purple lines vachayi ventane"* | `product_complaint` | `true` (if conf $\ge 0.85$) | Telugu-English hardware failure description (screen purple lines defect). |
| *"Bhai delivery bohot fast thi aur product ekdum top class hai ❤️"* | `positive` | `false` | Hinglish praise for logistics and quality. |
