# Stoyan's on-site workflow

Stoyan is an experienced cabinetmaker and interior designer. He draws by hand while discussing an idea with the customer. The assistant should help turn that conversation into a reviewable design before he returns to his computer, then support workshop preparation.

## On site: photo to a design the customer can review

1. Read the uploaded photo and the existing conversation. State the interpreted furniture, overall dimensions and visible arrangement in one short Bulgarian sentence. Use written dimension chains, not perspective pixel measurements.
2. Ask only what changes the geometry, visible finish or material cost. Bundle 1–3 short questions with 2–3 concrete choices each; suggest a reasonable option where appropriate. Use real single-choice controls when supported, otherwise a short numbered list. Never invent a button or claim a selection was recorded without a response.
3. Reuse answers already given. Do not make Stoyan specify every hinge, drilling point and hidden joint before showing a preliminary exterior/interior view. Record those choices as pending for workshop preparation.
4. Generate the views from the explicit panel model. Return exterior.png and interior.png inline first, with dimensions, finish names and only the assumptions needed to understand what the customer is approving. Offer the interactive viewer as a supplement; a phone chat must not depend on access to a localhost URL on the author's Mac.
5. Provide a dated material-only estimate. Current user preference: leave labor, installation, profit and final selling price unfilled. Never convert a partial material subtotal into a final quote.

## Workshop: approved idea to a verified cut plan

Resolve exact stock formats, grain/rotation, finished-versus-raw dimensions, all banded edges, joinery, drawer hardware allowances and rear-panel attachment. Then regenerate from the same project data. Print-ready plans remain preliminary until these are reviewed by the craftsperson.

Compare the strip-layout candidates. Report achieved board count, yield, useful offcuts and the proven lower bound when available. A matching lower bound proves minimum board count only under the declared rectangular-panel constraints; it does not prove shortest cutting time or CNC readiness.

## Pricing rules

- Browse current Bulgarian supplier pages for the exact product variant, thickness, format and finish. The user-selected preferred sources are Kedar (https://www.kedar-ood.com/) and ROSI (https://rosi.bg/bg). Start there for prices, colors, textures, stock formats and hardware; consult other suppliers or the manufacturer when the needed evidence is missing. Do not base a current quote on a search snippet when a live page can be read.
- Store supplier, product SKU, direct URL, observed date, unit, price, VAT basis, packaging, purchase increment, availability and any promotion. Unknown promotion expiry remains unknown.
- Price bought whole sheets according to the current nesting; do not price only the visible panel area or charge the same sheet waste twice. If offcuts are reused from inventory, record their dimensions and assigned value explicitly.
- Match edge thickness and color exactly. A 0.8 mm cream band is not a verified price for a selected 1 mm band. Hardware quotes must include required plates, clips and companion parts where applicable.
- Do not infer hinge counts only from door height; check weight, width and manufacturer guidance. Distinguish pieces, pairs and complete drawer systems. Do not price both a complete metal drawer system and a redundant wooden box without an explicit design reason.
- Missing HDF stock, unresolved carcass banding or unspecified hardware keeps the estimate incomplete. Missing values are null, never silently zero.
- Refresh selected prices before each current estimate. The local JSON catalog is a dated snapshot, not an automatic price feed. Labor and profit can be added later only when the user supplies the pricing method.

## Improving from future sketches

For each new design, retain the original privately, a reviewed transcription, the confirmed project data, observed failure, corrected rule and a regression case. Generalize only conventions supported by the evidence; a single wardrobe is not a universal construction standard. Call this iterative skill and evaluation improvement, not model fine-tuning. Do not claim measured time savings, accuracy or customer approval before recording them.

Kedar also lists decor/texture search and cutting, edge-banding, CNC and hardware-drilling services. Service availability does not establish a price; retrieve the relevant price or leave it pending.
