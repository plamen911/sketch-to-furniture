# Evaluation and improvement protocol

This project improves its instructions, deterministic tooling and regression corpus. It does not fine-tune the underlying language model.

For each new sketch, retain a private source photo under `projects/`, then record:

1. A reviewed transcription with visible dimensions and confidence flags.
2. Client answers and a construction specification with confirmed versus provisional decisions.
3. The first interpretation, questions asked, elapsed time and any incorrect inference.
4. The correction and the smallest rule or code change that fixes the demonstrated problem.
5. A sanitized fixture and expected behavior checked independently of generated output.

Run the existing cases after every change. Add a difficult unseen design as a holdout when enough examples are available. Never derive the expected dimensions merely by copying the implementation's output.

Track: dimension transcription errors, closed dimension chains, questions repeated after an answer, questions needed before a useful preview, geometry/cut-list consistency, grain/kerf violations, completeness of sourced prices, and craftsperson corrections. Report observed counts and timings only. No accuracy or time-saving claim has yet been measured across multiple sketches.

Current real design coverage: one wardrobe reconstruction. Numeric/unit tests are broader than that one example, but they do not establish recognition accuracy on arbitrary furniture sketches. Future complex drawings should extend the corpus before broader claims are made.
