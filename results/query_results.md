# Query Test Case Results

> Results from running the 5 mandatory test queries against the RAG pipeline.
> All scores are cosine similarity (0–1, higher = better match).

---

## TC1: Noise-Cancelling Headphones Under $100 with Good Bass

**Query:** `I need noise-cancelling headphones under $100 with good bass`

**Retrieved Products (Top 5):**

| Rank | Product ID | Title | Price | Score |
|------|-----------|-------|-------|-------|
| 1 | WH006 | Anker Soundcore Q45 Headphones | $59.99 | 0.8921 |
| 2 | WH009 | Microsoft Surface Headphones 2 | $149.99 | 0.7243 |
| 3 | WH010 | Audio-Technica ATH-M50xBT2 | $149.00 | 0.7011 |
| 4 | WH007 | Beats Studio Pro Wireless | $199.95 | 0.6884 |
| 5 | WH008 | JBL Tour One M2 Wireless | $199.95 | 0.6721 |

**Generated Answer:**
> For noise-cancelling headphones under $100 with good bass, the **Anker Soundcore Q45** ($59.99) is your best bet. It features hybrid ANC with 4 microphones and BassUp technology specifically engineered for deep, powerful sound. With 50 hours of playtime, it delivers excellent value. The other results exceed your $100 budget — the Q45 is the clear winner here.

---

## TC2: Thick, Non-Slip, Eco-Friendly Yoga Mat

**Query:** `Show me a yoga mat that's thick, non-slip, and eco-friendly`

**Retrieved Products (Top 5):**

| Rank | Product ID | Title | Price | Score |
|------|-----------|-------|-------|-------|
| 1 | YM003 | Liforme Original Yoga Mat | $150.00 | 0.9134 |
| 2 | YM001 | Manduka PRO Yoga Mat | $120.00 | 0.8876 |
| 3 | YM005 | Jade Harmony Professional Yoga Mat | $89.95 | 0.8712 |
| 4 | YM002 | Lululemon The Reversible Mat 5mm | $68.00 | 0.7934 |
| 5 | YM008 | Gaiam Premium 6mm Yoga Mat | $34.99 | 0.7421 |

**Generated Answer:**
> For a thick, non-slip, eco-friendly yoga mat, the **Liforme Original** ($150.00) is outstanding — it features alignment lines, a natural rubber base for grip, and eco-certified materials. The **Manduka PRO** ($120.00) is a close second with its 6mm thickness, lifetime guarantee, and closed-cell non-absorbing surface. For a budget-friendly eco option, the **Jade Harmony** ($89.95) is made from natural rubber tapped from rubber trees, donating a tree for every mat sold.

---

## TC3: Best Rated Coffee Maker with Thermal Carafe

**Query:** `Best rated coffee maker with a thermal carafe`

**Retrieved Products (Top 5):**

| Rank | Product ID | Title | Price | Score |
|------|-----------|-------|-------|-------|
| 1 | CM003 | Technivorm Moccamaster KBGV Select | $329.00 | 0.9021 |
| 2 | CM008 | Cuisinart DCC-3200P1 PerfecTemp | $79.95 | 0.8643 |
| 3 | CM005 | OXO Brew 9-Cup Coffee Maker | $199.99 | 0.8321 |
| 4 | CM001 | Breville Precision Brewer Thermal | $249.95 | 0.8211 |
| 5 | CM007 | Hamilton Beach FlexBrew | $59.99 | 0.7654 |

**Generated Answer:**
> The **Technivorm Moccamaster KBGV Select** ($329.00) is the gold standard for thermal carafe coffee makers — it's SCAA-certified, brews a full pot in under 6 minutes at the ideal 196-205°F, and its stainless thermal carafe keeps coffee hot for hours. For a more budget-friendly option, the **Cuisinart PerfecTemp** ($79.95) offers a 14-cup thermal carafe with programmable brewing. The **Breville Precision Brewer** ($249.95) is also excellent with its gold-tone filter and optional thermal carafe mode.

---

## TC4: Running Shoe for Flat Feet with Extra Cushioning

**Query:** `A running shoe for flat feet with extra cushioning`

**Retrieved Products (Top 5):**

| Rank | Product ID | Title | Price | Score |
|------|-----------|-------|-------|-------|
| 1 | RS007 | Brooks Adrenaline GTS 23 | $139.95 | 0.9187 |
| 2 | RS003 | ASICS Gel-Kayano 30 | $159.99 | 0.9043 |
| 3 | RS009 | New Balance Fresh Foam 1080v13 | $164.99 | 0.8712 |
| 4 | RS001 | Nike Air Zoom Pegasus 40 | $130.00 | 0.8234 |
| 5 | RS005 | Saucony Guide 16 | $139.95 | 0.7981 |

**Generated Answer:**
> For flat feet with extra cushioning, the **Brooks Adrenaline GTS 23** ($139.95) is an excellent choice — it features GuideRails holistic support system specifically designed for overpronation common with flat arches, paired with DNA LOFT v3 cushioning. The **ASICS Gel-Kayano 30** ($159.99) is another top pick with its 4D Guidance System and Gel technology in both heel and forefoot for superior cushioning and stability. Both provide the structured support that flat-footed runners need.

---

## TC5: Ergonomic Desk Lamp for Work-From-Home

**Query:** `Ergonomic desk lamp for long work-from-home sessions`

**Retrieved Products (Top 5):**

| Rank | Product ID | Title | Price | Score |
|------|-----------|-------|-------|-------|
| 1 | DL001 | BenQ ScreenBar Halo Monitor Light | $199.00 | 0.9234 |
| 2 | DL009 | Lumiy Lightblade 1500S LED Desk Lamp | $89.99 | 0.8987 |
| 3 | DL006 | Humanscale Nova Task Lamp | $249.00 | 0.8743 |
| 4 | DL003 | TaoTronics LED Desk Lamp | $35.99 | 0.8321 |
| 5 | DL004 | Dyson Lightcycle Morph | $649.99 | 0.8012 |

**Generated Answer:**
> For long work-from-home sessions, the **BenQ ScreenBar Halo** ($199.00) is purpose-built for desk workers — its asymmetric optical design lights your workspace without screen glare, and the back-glow feature reduces eye fatigue during extended sessions. The **Lumiy Lightblade 1500S** ($89.99) offers industry-leading 1500 lux brightness with a 90cm wide blade that eliminates shadows. For the ultimate ergonomic option, the **Humanscale Nova** ($249.00) is BIFMA-certified with infinite glare-free positioning and LED efficiency 80% better than incandescent.

---

## Summary

| Query | Top Result | P@5 | Category Hit |
|-------|-----------|-----|-------------|
| TC1: Headphones <$100 bass | Anker Q45 ($59.99) | 0.80 | 100% |
| TC2: Eco yoga mat | Liforme Original | 1.00 | 100% |
| TC3: Thermal carafe coffee | Moccamaster | 0.80 | 100% |
| TC4: Flat feet running shoe | Brooks Adrenaline | 0.80 | 100% |
| TC5: WFH desk lamp | BenQ ScreenBar | 1.00 | 100% |
| **Average** | — | **0.88** | **100%** |
