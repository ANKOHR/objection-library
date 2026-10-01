# Lessons for KOML

The domain needs a distinction between an objection occurrence, an attempted response awaiting outcome, and a completed trial. Counting pending responses as failures would misstate the observed evidence. Exact text grouping is reproducible but does not unify paraphrases, so consistent manual naming is an operating responsibility.

Validated locally: the engine can reconcile 200 planted records, including all four outcomes and per-response IDs, against independent hand arithmetic. Corrupting one accepted outcome changes the computed counts and identified accepted cases. This validates counting from explicit inputs, not the assumption that a library improves outbound results. That assumption remains untested until real use.

Operating rule for future builds: ship an independently labelled oracle and a mutation test before drawing conclusions from a plausible-looking report. Keep engineering acceptance separate from adoption evidence and leave the final business verdict pending until measured.
