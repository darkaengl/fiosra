# Refinement Verification Results

## Portfolio verification

The rebuilt local UI was opened after the refinement build. The course portfolio now renders only live API values for course workspaces, module totals, and assignment totals; the earlier fabricated totals for enrolled learners, current sessions, and pending reviews no longer appear. Course identifiers entered in the standard `CODE: Title` convention render as separate code and title elements. The portfolio material-guidance action now directs educators to module-specific grounding rather than simulating ingestion.

## Remaining browser checks

The next browser checks exercise the new source-grounded scaffold, its publication guardrail, the public student assignment projection, and the repaired filtered review endpoint.

## Published student-launch verification

A browser opened the test course’s module page and confirmed the readiness indicators: objectives mapped, one source grounded, and one student task published. The source card displayed its actual title, type, grounding state, and a truthful “KC mapping pending” indicator rather than claiming an unavailable mapping.

Selecting the published task’s **Student canvas** link successfully initialized a student session and loaded the same Mohenjo-daro prompt, course source, generic history KCs, and bounded hint availability. The prompt preserved the teacher-selected setting, source, and cognitive trap; no French Revolution task content was present. This validates the repaired teacher card → public-assignment projection → student session handoff.

## Tutor-turn regression discovered

The student-canvas launch and prompt provenance are correct, and the public assignment response contains neither `vault_token` nor `reference_solution`. However, sending an otherwise relevant Mohenjo-daro response exposed a remaining content-contamination defect in the dialogue engine: its follow-up Socratic turn asked about the French Declaration, women voting, and slavery in the Caribbean. The tutor response must be generated from the active public assignment’s prompt, sources, and target KCs rather than a fixed French Revolution template. This is a release-blocking regression and is being corrected before final validation.

## Tutor repair validation

The corrected server was restarted. The previous incorrect French-language tutor turn remains visible in the already-recorded local test session, as expected for an append-only evidence log. A new response was entered into that same active session to verify that only the subsequent tutor turn is affected by the repair; historical evidence was not silently altered.

## Tutor repair outcome

The next live tutor turn correctly used the assignment-specific rung-zero prompt: “State a provisional claim, then name the observation that most directly supports it. What remains uncertain?” It did not surface French Revolution content or an unrelated taxonomy diagnosis. The older contaminated turns remain in the test session as historical evidence, while future turns are constrained by the active public assignment’s curated hint ladder and target KCs.

## Student submission validation

The student trace was submitted successfully from the UI. The server changed its status to `submitted`, appended the submission event to the visible chronological trace, and surfaced an educator-review link. This action preserved the earlier events rather than replacing them, consistent with the append-only evidence model.

## Filtered educator-review verification

The student submission appeared immediately in the filtered AutoSCORE queue for its course. The review screen returned a count of one, loaded the matching assignment title, rendered the evidence dossier, and preserved the educator’s separate finalization authority. No conflicting zero-result or fetch-failure state appeared. The test deliberately stopped before finalizing a grade, so the local test evidence remains available for review rather than being sealed as a completed decision.
