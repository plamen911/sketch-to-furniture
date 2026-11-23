# Competitor evaluation — 23 November 2026

## Outcome

This session did not establish a winner. It verified access restrictions, generated the known local reference and attempted one Srezio modeling run plus a follow-up photo submission. Later user-supplied text and screenshots show a Srezio transcription and a preliminary model after clarifications. No competitor manufacturing export was obtained, so dimensional accuracy, nesting quality and end-to-end speed cannot be ranked.

| Product / stage | Observed result | Scope and limitation |
| --- | --- | --- |
| Sketch to Furniture 0.3.1, known reference | Generated CAD, viewer, PNGs, CSV and cutting plans; 28 panel parts, 2 particleboard and 2 MDF sheets | Reviewed JSON input, previously used in development. Not a blind photo-recognition result. HDF back/drawer bottoms are excluded from nesting because no stock format is declared. |
| Srezio browser editor | Opened without creating an account; assistant and construction controls visible | The presence of controls does not verify their numerical behavior. |
| Srezio photo test (A), follow-up | Attachment filename appeared in a fresh blank project after the user enabled Chrome file-URL permission; request then remained Not sent | Initial send, one retry, and one further retry after explicit project sync did not produce a reply. Project status became Synced, while the message still showed Not sent. No dimension transcription or model was obtained; the cause was not exposed. This is not an accuracy result. |
| Srezio reviewed-specification test (B) | Prompt submitted in Bulgarian; project sync confirmed; no model or substantive answer before tester stopped the run | Last pre-stop observations showed Thinking 3:03 and agent elapsed 3:15, with 0 tokens / 0 credits displayed. Stop was acknowledged. This is one incomplete session, not proof that the service cannot generate the project. |
| Coobic design trial | Design link led to a sign-in page | No account was created and no AI generation was tested. |
| Coobic production exports | Not tested | Official page stated $149/month and that the three-day trial covers design/photos while cut lists, drawings and machine files require a subscription. No purchase was made. |

## Local evidence

The generator produced 28 panel parts and four nested stock sheets from `examples/wardrobe/project.json`. Its report proves minimum counts of two particleboard and two MDF sheets only under the declared rectangular-panel, stock, trim, kerf, grain and rotation constraints. HDF parts `BACK`, `D1_BOTTOM` and `D2_BOTTOM` are explicitly excluded; four sheets is not the complete purchase requirement for every material.

Eleven geometry/export tests and seven costing tests passed during this session. The saved cut list distinguishes finished from raw sizes and per-edge band thickness. Labor, profit and client selling price remain unfilled. Supplier prices in the example are a dated snapshot and were not refreshed for a current quotation in this test.

Private runtime outputs, exact request, competitor project URL and original photo are not published. The public protocol is [competitor-test-protocol.md](competitor-test-protocol.md).

## Follow-up photo submission

The user enabled the required Chrome extension setting. A new blank Srezio project was used to avoid supplying the reviewed dimensions through the earlier conversation. The original photo appeared in the attachment list. The Bulgarian request asked for visible dimensions, layout and material notes first, distinguishing uncertain readings and allowing at most three clarification questions. No expected dimensions or corrected material code were included in the request.

Sending produced the visible status `Not sent`. One immediate retry did not resolve it. Explicitly uploading/syncing the blank project succeeded, but a further retry after that state change still left the message unsent. No recognition output was available to assess. Attachment selection is verified; receipt or processing of the photo by the AI backend is not verified. There was no active model run to stop in this follow-up.

## What this changes

1. Do not present photo-to-CAD-to-cutting as a unique feature. Several products advertise it; our specific value must be demonstrated on workshop tasks.
2. Keep recognition tests separate from specification-to-output tests. The current reference has development exposure, so use unseen drawings for the next acceptance session.
3. Compare construction assumptions before part counts. Different legitimate drawer boxes or back attachments can change a cut list.
4. Prefer a review table tied to the source sketch for uncertain dimensions and banded edges. It provides inspectable evidence before production rather than a general claim of AI confidence.
5. Re-test Srezio after image upload is available, using the same prompt and declared observation window. Only test Coobic exports if a suitable authorized account is available; do not purchase a subscription just to complete this comparison.

## Sources and evidence level

- [Srezio official product page](https://srez.io/): vendor claims about photo input, browser/mobile editing, Bulgarian and workshop exports; editor access was observed directly.
- [Srezio editor](https://srez.io/editor): direct browser observations above. No image accuracy or manufacturing claim independently validated.
- [Coobic official product page](https://coobic.co/): vendor claims about photo/sketch input, 3D and workshop files; current pricing/trial restrictions observed directly.
- [Coobic design entry](https://coobic.co/design): sign-in requirement observed directly.

Prices and access rules can change. All observations are bounded to this session on 23 November 2026. No performance score or broad reliability conclusion is justified by these results.

## Later manual test evidence supplied by the user

The user supplied a Srezio transcription and screenshots of a generated wardrobe. This updates the earlier automated-session limitation: Srezio did produce a preliminary model in the user's separate manual session. Its first transcription read the main width/depth, asked eight clarification questions, and mixed visible facts with uncertain shelf counts and suggested back thicknesses. The model screenshots show overall dimension labels, internal panels, visible workflow stages and a separate assumptions control. A credit-limit message interrupted further assistant work; a screenshot also showed a 0/5 task counter despite visible geometry. These are user-supplied observations, not downloaded model/cut-list measurements. Internal dimensions, panel thicknesses, edging and production exports remain unverified. The manual result must not be conflated with our earlier stopped or unsent requests.
