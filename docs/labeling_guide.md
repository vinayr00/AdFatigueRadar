# AdFatigueRadar — Human Annotation & Labeling Guide
**Version**: 1.0 | **Author**: Person 1 (AI / NLP Layer) | **Scope**: 8-Class Ad-Fatigue Taxonomy

---

## 1. Objective & Guidelines
This document defines the ground-truth adjudication rules for labeling social ad comments into the frozen 8-class taxonomy for AdFatigueRadar. Strict adherence ensures consistency across human auditors and prevents label contamination.

---

## 2. The Frozen 8-Class Taxonomy

| Category ID | Harmful Weight ($w_c$) | Severity Profile | Core Description |
| :--- | :---: | :---: | :--- |
| `product_complaint` | **1.00** | Critical Candidate | Specific defect, malfunction, or poor physical/software quality of the product. |
| `service_complaint` | **1.00** | Critical Candidate | Logistics, delayed shipping, unauthorized charges, unhelpful support, or refund refusal. |
| `fatigue` | **0.80** | Harmful | Repetitive exposure to the advertisement (*"Bro this ad again"*). |
| `mockery` | **0.75** | Harmful | Direct ridicule of the ad creative, actors, script, cringe factor, or marketing approach. |
| `spam` | **0.60** | Low-Quality | Crypto scams, telegram channels, fake giveaways, affiliate links, and bot spam. |
| `banter_meme` | **0.00** | **Non-Harmful** | Playful slang, meme references, pop-culture humor, and viral engagement (*"let him cook"*). |
| `neutral` | **0.00** | **Non-Harmful** | Spec inquiries, price/size questions, delivery estimates, or tagging friends. |
| `positive` | **0.00** | **Non-Harmful** | Satisfaction, praise, purchase intent, and repeat purchases (*"bought again, love it"*). |

---

## 3. Disambiguation & Adjudication Rules

### 3.1 The 'Again' Disambiguation Rule (CRITICAL)
- **FATIGUE**: Apply **only** when the comment indicates repeated exposure to the advertisement itself.
  - *"Bro this ad again 😂"* $\longrightarrow$ **`fatigue`**
  - *"Why is this on my feed again?"* $\longrightarrow$ **`fatigue`**
  - *"Seen this same clip 10 times today"* $\longrightarrow$ **`fatigue`**
- **POSITIVE**: Apply when 'again' refers to a repeat purchase, reorder, or continued customer satisfaction.
  - *"Bought again, love it!"* $\longrightarrow$ **`positive`**
  - *"Ordered again, thank you for the fast shipping!"* $\longrightarrow$ **`positive`**
  - *"My second time purchasing from this brand"* $\longrightarrow$ **`positive`**

### 3.2 Product Complaint vs Service Complaint
- **`product_complaint`**: The physical or digital good is broken, defective, dangerous, or underperforming.
  - *"Broke on day 2"*
  - *"Battery dies in 15 minutes"*
  - *"The zipper teeth misaligned and locked shut"*
- **`service_complaint`**: The merchant/support process failed, irrespective of the physical product.
  - *"Ordered 3 weeks ago and support is ghosting my emails"*
  - *"Double charged my card and won't refund"*
  - *"Delivery driver left package in the rain"*

### 3.3 Mockery vs Banter / Meme
- **`mockery`** ($w=0.75$): The comment roasts or degrades the ad itself, the actors, the company's marketing, or script quality.
  - *"The acting in this ad is making my teeth hurt from cringe 💀"*
  - *"Bro thinks he is starring in a Hollywood movie 😭"*
  - *"Who approved this commercial? Pure clownery 🤡"*
- **`banter_meme`** ($w=0.00$): The comment uses viral slang or playful memes without degrading the product or campaign.
  - *"Bro got that unspoken rizz fr fr"*
  - *"Nah he cookin let him cook 🔥"*
  - *"Me at 3am watching this instead of sleeping 😂"*
  - *"Emotional damage right at the start lmao"*

### 3.4 Spam vs Repeated Genuine Complaint
- **`spam`** ($w=0.60$): Contains external promotional links, telegram handles, forex/crypto, whatsapp contacts, or bot copy.
  - *"Click link in bio for free crypto telegram signals"*
  - *"WhatsApp +123456789 for luxury replica watches"*
- **`product_complaint` / `service_complaint`**: Even if an angry user comments repeatedly, if it describes a legitimate product failure, label it as the appropriate complaint category (bot/brigade spam filters are handled upstream by anomaly detection).

---

## 4. Critical Complaint Classification Criteria

A comment qualifies for `critical_complaint = True` **if and only if**:
1. It is classified into `product_complaint` or `service_complaint`.
2. The calibrated model confidence is $\ge 0.85$.
3. It demonstrates severe failure (e.g., safety hazard, immediate defect, unauthorized billing, total loss).

> **Important Rule**: The presence of critical keywords (e.g., *"broken"*, *"scam"*, *"hazard"*) alone must **never** create a critical complaint flag unless the classifier confirms complaint semantics with $\ge 0.85$ confidence.

---

## 5. Ambiguous Examples & Reference Table

| Raw Comment Text | Ground Truth Category | Sentiment | Critical? | Rationale |
| :--- | :--- | :--- | :---: | :--- |
| *"Bro this ad again 💀"* | `fatigue` | `negative` | False | Repeated exposure signal |
| *"Bought again for my mom's birthday!"* | `positive` | `positive` | False | Repeat purchase satisfaction |
| *"The zipper snapped on the first pull"* | `product_complaint` | `negative` | True | Immediate physical defect ($conf \ge 0.85$) |
| *"Support closed my ticket without refunding"* | `service_complaint` | `negative` | True | Customer support failure ($conf \ge 0.85$) |
| *"Bro is fighting for his life reading that teleprompter"* | `mockery` | `negative` | False | Roasting ad actor |
| *"Bro really thought he cooked with that line fr fr"* | `banter_meme` | `positive` / `neutral` | False | Harmless social slang ($w=0.00$) |
| *"Is there international shipping to Australia?"* | `neutral` | `neutral` | False | Logistics inquiry |
| *"Join t.me/free_crypto for 10x gains link in bio"* | `spam` | `negative` | False | Bot promotion ($w=0.60$) |
