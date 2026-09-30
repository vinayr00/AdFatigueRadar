# AdFatigueRadar — Formal Annotation Guidelines
======================================================
**Version**: `v2.0-real-world`  
**Applicability**: Supervised Human Annotation & Ground Truth Verification  
**Primary Taxonomy**: 8-Class Mutually Exclusive Disjoint Schema  

---

## 1. Executive Overview & Annotation Principles

Every social media comment ingested into AdFatigueRadar must be annotated into **exactly one** of the 8 canonical classes.
Annotators must adhere to three foundational rules:

1. **Objectivity Over Emotion**: Annotate the literal and communicative intent of the comment in the context of an advertisement, not the annotator's personal reaction.
2. **Harmful Weight Alignment**: The downstream system applies risk weights ($w \in [0.0, 1.0]$) to protect ad campaigns from false-alarm pauses. Non-harmful engagement (banter, memes, neutral questions, positive feedback) must **never** be misclassified into harmful categories.
3. **No Model-Biased Labeling**: Annotators must evaluate text strictly against these guidelines without consulting or accepting model guesses as default.

---

## 2. The 8 Frozen Taxonomy Classes: Detailed Specifications

### Class 1: `product_complaint`
* **Weight**: High ($w = 1.00$)
* **Core Definition**: A complaint addressing the physical, structural, functional, safety, software, or cosmetic flaws of the advertised product or item itself.
* **Inclusion Criteria**:
  - Reports defective hardware, broken parts, missing promised functionality, or dangerous flaws.
  - Complaints that the physical item did not match the advertisement description ("false advertising", "cheap plastic").
* **Exclusion Criteria**:
  - Complaints about shipping delays or customer support responses (assign `service_complaint`).
  - Sarcastic roasts about the video production/actors without owning or discussing the physical item (assign `mockery`).
* **Positive Examples**:
  - *"The zipper broke on day 2, complete waste of money."*
  - *"Screen has horizontal green lines out of the box."*
  - *"Battery only lasts 45 minutes instead of 8 hours claimed."*
* **Negative Examples**:
  - *"Delivery took 4 weeks!"* $\rightarrow$ `service_complaint`
  - *"Worst ad ever made 💀"* $\rightarrow$ `mockery`
* **Borderline Case & Resolution Rule**:
  - *Case*: *"Item broke after 2 days and support refused my refund."* (Mentions both product defect and service).
  - *Resolution Rule*: Assign **`product_complaint`** because physical defect is the primary severe risk indicator.

---

### Class 2: `service_complaint`
* **Weight**: High ($w = 1.00$)
* **Core Definition**: A complaint addressing post-purchase fulfillment, delivery operations, courier handling, customer support unresponsiveness, warranty denials, or billing errors.
* **Inclusion Criteria**:
  - Mentions late packages, missing tracking numbers, courier damage in transit.
  - Mentions unreturned emails, ghosting customer service, or disputed unauthorized charges.
* **Exclusion Criteria**:
  - Physical quality defects of an undamaged delivered product (assign `product_complaint`).
  - General complaints about seeing the ad repeatedly (assign `fatigue`).
* **Positive Examples**:
  - *"Ordered a month ago and tracking still says label created."*
  - *"Support emailed me once and then completely ghosted me."*
  - *"Charged my credit card twice for one order."*
* **Negative Examples**:
  - *"Material feels cheap and thin."* $\rightarrow$ `product_complaint`
  - *"Seen this ad 100 times."* $\rightarrow$ `fatigue`
* **Borderline Case & Resolution Rule**:
  - *Case*: *"I've posted on 5 ads already asking where my order is!"*
  - *Resolution Rule*: Assign **`service_complaint`**, NOT `spam` or `fatigue`. Multiple identical complaint posts by a frustrated customer represent genuine customer service failure.

---

### Class 3: `fatigue`
* **Weight**: Medium ($w = 0.70$)
* **Core Definition**: Frustration, boredom, exhaustion, or irritation caused specifically by repeated algorithmic over-exposure to the advertisement itself.
* **Inclusion Criteria**:
  - References frequency of seeing the ad ("again", "stop showing me", "50 times today", "every 2 scroll steps").
  - References over-saturation in the user's feed, timeline, or FYP.
* **Exclusion Criteria**:
  - Repeat purchase confirmation containing "bought again" or "ordered again" (assign `positive`).
  - Roasting the actor/script with no mention of ad frequency (assign `mockery`).
* **Positive Examples**:
  - *"Bro this ad again 😂"*
  - *"Why is this sponsor on my feed every 5 minutes?"*
  - *"I swear I have seen this 20 times today alone."*
  - *"Stop showing me this ad, I already bought one!"*
* **Negative Examples**:
  - *"I bought it again for my sister, she loved it!"* $\rightarrow$ `positive`
  - *"This actor is so cringe 💀"* $\rightarrow$ `mockery`
* **Borderline Case & Resolution Rule**:
  - *Case*: *"Why does this cringe ad keep popping up on my feed 😂"* (Mentions both cringe and repetition).
  - *Resolution Rule*: Assign **`fatigue`**. Frequency saturation is the root trigger for campaign audience exhaustion.

---

### Class 4: `mockery`
* **Weight**: Medium ($w = 0.50$)
* **Core Definition**: Derisive sarcasm, ridicule, roasts, or parody targeted directly at the advertisement creative, actor performance, dialogue, script, graphics, or unrealistic marketing promises.
* **Inclusion Criteria**:
  - Sarcastic or hostile mockery directed at the commercial or brand.
  - Ridiculing bad acting, cheesy AI voiceovers, or ridiculous product demonstrations.
* **Exclusion Criteria**:
  - Playful slang or friendly meme humor that does not denigrate the brand or product (assign `banter_meme`).
  - Genuine product breakdown complaints by an actual user (assign `product_complaint`).
* **Positive Examples**:
  - *"Who approved this script? High school drama club acting 💀"*
  - *"The voiceover sounds like an AI that lost the will to live."*
  - *"Bro really hired a Fiverr actor in a garage for a luxury brand 😂"*
* **Negative Examples**:
  - *"Bro let him cook 🔥"* $\rightarrow$ `banter_meme`
  - *"Broke after one use."* $\rightarrow$ `product_complaint`
* **Borderline Case & Resolution Rule**:
  - *Case*: *"Bro got that 1000 yard stare in this commercial 😭"*
  - *Resolution Rule*: If the comment is lighthearted social teasing without attacking brand legitimacy, assign **`banter_meme`**. If it explicitly devalues the product/commercial as fake or laughable scam, assign **`mockery`**.

---

### Class 5: `spam`
* **Weight**: Low ($w = 0.10$)
* **Core Definition**: Unsolicited third-party commercial promotions, crypto/forex signals, external link dumps, bot scams, WhatsApp/Telegram solicitations, or irrelevant copypastas.
* **Inclusion Criteria**:
  - Contains external promotion links (t.me, wa.me, bit.ly, bio link solicitations).
  - Unrelated financial/crypto scams or "DM me to earn money" comments.
* **Exclusion Criteria**:
  - Repeated genuine customer complaints across multiple ads (assign `service_complaint` or `product_complaint`).
  - Legitimate questions asking for a purchase link (assign `neutral`).
* **Positive Examples**:
  - *"Check link in my bio for free iPhone 15 giveaways!"*
  - *"Earn $500 daily trading forex, text +1234567890 on WhatsApp."*
  - *"t.me/free_crypto_signals_daily join now"*
* **Negative Examples**:
  - *"Where can I get the discount link?"* $\rightarrow$ `neutral`
  - *"Refund my money you scammers!"* $\rightarrow$ `service_complaint`

---

### Class 6: `banter_meme`
* **Weight**: Non-Harmful ($w = 0.00$)
* **Core Definition**: Harmless humor, Gen-Z / internet slang, cultural memes, playful banter between users, or viral copypastas.
* **Inclusion Criteria**:
  - Slang terms: "rizz", "let him cook", "fr fr", "skibidi", "no cap", "gigachad", "skull emoji 💀".
  - Light teasing between friends or general friendly humor.
* **Exclusion Criteria**:
  - Sarcastic roasts explicitly disparaging product quality or advertisement legitimacy (assign `mockery`).
  - Direct complaints about product defect (assign `product_complaint`).
* **Positive Examples**:
  - *"Bro really thought we wouldn't notice that background 😂🔥"*
  - *"He got that unspoken rizz ngl"*
  - *"let him cook fr fr"*
  - *"tagging @friend you need this bro 😂"*
* **Negative Examples**:
  - *"Paid actor in a basement 💀"* $\rightarrow$ `mockery`
  - *"Scam company do not buy"* $\rightarrow$ `product_complaint`
* **Safety Rule**: When ambiguous between harmless meme slang and mild mockery, default to **`banter_meme`** to prevent unnecessary campaign pauses.

---

### Class 7: `neutral`
* **Weight**: Non-Harmful ($w = 0.00$)
* **Core Definition**: Objective informational inquiries, sizing/pricing questions, compatibility checks, shipping geography queries, bare user tags, or unemotional statements.
* **Inclusion Criteria**:
  - Questions asking for price, dimensions, color options, or technical compatibility.
  - Bare tags: "@john_doe".
* **Exclusion Criteria**:
  - Inquiries loaded with frustration about previous orders (assign `service_complaint`).
  - Explicit praise or purchase intent (assign `positive`).
* **Positive Examples**:
  - *"Does this work with iPhone 14 Pro?"*
  - *"How much is shipping to Germany?"*
  - *"Is this waterproof up to 50 meters?"*
  - *"@alexander"*
* **Negative Examples**:
  - *"Looks amazing, ordered one!"* $\rightarrow$ `positive`
  - *"Why hasn't my order shipped yet?"* $\rightarrow$ `service_complaint`

---

### Class 8: `positive`
* **Weight**: Non-Harmful ($w = 0.00$)
* **Core Definition**: Authentic customer satisfaction, endorsement, excitement, complimenting the product/ad, or confirmation of repeat purchases.
* **Inclusion Criteria**:
  - Expressions of love, excitement, or recommendation.
  - Repeat purchase confirmation ("ordered again", "buying a second one").
* **Exclusion Criteria**:
  - Purely sarcastic "praise" intended as a roast (assign `mockery`).
  - Neutral inquiries without enthusiasm (assign `neutral`).
* **Positive Examples**:
  - *"Best purchase I made all year, works perfectly!"*
  - *"Bought it again for my dad, super fast shipping too!"*
  - *"Can't wait for mine to arrive ❤️"*
  - *"Quality is top notch, 10/10 recommend."*
* **Negative Examples**:
  - *"Oh yeah 'great quality', broke in 5 minutes 🤡"* $\rightarrow$ `mockery` (or `product_complaint` if factual defect)
  - *"Is it good quality?"* $\rightarrow$ `neutral`

---

## 3. High-Confusion Boundary Matrix & Resolution Rules

| Pair | Boundary Distinction | Resolution Rule |
| :--- | :--- | :--- |
| **`mockery` vs `banter_meme`** | Mockery attacks brand/ad legitimacy; Banter is playful social engagement. | If slang/meme does not insult brand credibility $\rightarrow$ `banter_meme`. |
| **`product_complaint` vs `service_complaint`** | Product = item defect; Service = logistics/delivery/support. | If both present (e.g. broken item + late shipping) $\rightarrow$ `product_complaint`. |
| **`product_complaint` vs `fatigue`** | Product = physical defect; Fatigue = seeing the ad too many times. | If customer complains about broken item $\rightarrow$ `product_complaint`. |
| **`banter_meme` vs `complaint`** | Slang ("💀", "crying") used jokingly vs genuine consumer frustration. | Sarcastic complaint about product $\rightarrow$ `product_complaint`; harmless meme $\rightarrow$ `banter_meme`. |
| **`neutral` vs `fatigue`** | Neutral = objective question; Fatigue = complaint about frequency. | Mentions repetition of ad $\rightarrow$ `fatigue`; asks basic product question $\rightarrow$ `neutral`. |
| **"Again" Disambiguation** | Repetition of *buying* vs Repetition of *seeing ad*. | "bought again" $\rightarrow$ `positive`; "this ad again" $\rightarrow$ `fatigue`. |

---

## 4. Annotation Decision Tree

```
[Incoming Comment]
       │
       ├─► Contains external commercial promotion / crypto / bot links? ──► [SPAM]
       │
       ├─► Contains repeat purchase affirmation ("bought again")? ───────► [POSITIVE]
       │
       ├─► Mentions ad over-exposure / seeing it again? ────────────────► [FATIGUE]
       │
       ├─► Mentions physical product defect / malfunction? ─────────────► [PRODUCT_COMPLAINT]
       │
       ├─► Mentions shipping delay, courier, lost package, support? ────► [SERVICE_COMPLAINT]
       │
       ├─► Derisive sarcasm / roasting the commercial / actors? ────────► [MOCKERY]
       │
       ├─► General praise / positive endorsement? ──────────────────────► [POSITIVE]
       │
       ├─► Social slang / meme humor / harmless teasing? ───────────────► [BANTER_MEME]
       │
       └─► Objective inquiry / sizing / pricing / neutral tag? ─────────► [NEUTRAL]
```
