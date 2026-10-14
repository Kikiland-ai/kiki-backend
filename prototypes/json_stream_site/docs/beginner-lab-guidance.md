# Beginner guidance after the first Simulink run

Date: 14 October 2026. The user stopped the lab sequence at the receiver stage: the observer correctly distinguished Carrier from Local carrier, but the guide said to open Local carrier settings without telling the user to create that separate source. Placement, wiring sequence and remembered progress were difficult to understand.

## Changes

The twelve source checkpoints and their scientific completion rules remain the lab ledger. A separately authored procedure in prototypes/lab_tracking/procedure.py expands them into forty ordered instructional actions. Each has a stable action ID, title, suggested relative placement, click/drag procedure, exact parameter table where relevant, expected result, observation rule and applicable criterion references. Creation precedes configuration and wiring; parameters and port assignments appear inline. The receiver starts with a third Sine Wave named Local carrier, then its settings, a second Product named Receiver product, Modulator-output wiring and local-reference wiring. Existing runs whose first Product is still named Product are told how to identify and rename it Modulator.

The main UI shows one current action, its placement/how/result, the next action, an earlier-stage recap and earlier observed action facts. A collapsible ordered procedure explains the stage without a checkbox checklist. Confirmation/response controls appear at the applicable action. Saving and conceptual explanation remain student reports; conceptual state remains unassessed. Suggested positions are for readability and are not strict coordinate requirements. Exact Simulink overlay/anchor placement remains the parallel writer's responsibility.

The observer prompt is dsb-step-observer/v3. It describes only present visible state in plain English, including relevant literal field values. It distinguishes the transmitter Carrier from the receiver Local carrier by identity, treats hidden/unreadable targets as unknown rather than absent or wrong, and checks each authored action as well as checkpoint criteria. Settings inspection proves displayed values; it does not independently establish a clicked Apply or saved model. User instructions remain authored and selected by the tracker; free-form observation prose does not choose actions or complete a checkpoint.

## Progress versus fresh evidence

Two matching observations from distinct frames can move an instructional action. Recent action support is scoped to visit/workspace/parameter revision/condition/capture segment, with existing freshness rules. A separate historical action map remembers what was tracked; unknown or offscreen views and pauses do not erase that procedure position. Mismatch revokes the relevant remembered action. Revisit, parameter/condition changes and checkpoint changes invalidate history. History never fulfils scientific checkpoint criteria. If all actions were done but required observations expired, the guide asks to show the named settings/connections again for a final check; it does not ask to recreate blocks. Pending final checks remain ordered before the next stage.

For the deliberate phase fault, Local carrier Phase pi and original Carrier Phase pi/2 can be read in separate dialogs. Only recent, correctly scoped action readings can aggregate that parameter criterion. Historical progress cannot do so, and a visible mismatch invalidates the aggregate. This is screen-inferred prototype evidence, not an assessment pass.

## Interfaces and compatibility

screen-guided-policy/v2 replaces the v1 criterion-first instruction selector; current_action and next_action are canonical structured guidance. It removes the old criterion_actions map and exports the Python-authored procedure/prompt to the temporary hosted Worker. Existing lab records, checkpoint/visit IDs, owned histories and reviewed-mode API behavior are preserved. Legacy analysis candidates without action_findings remain conservative; they supply no action matches. New provider requests require one action finding per authored action, with ID/evidence validation. Model response size increases from 1800 to 2600 maximum output tokens to fit bounded per-stage findings.

The screen-writing/v0.2 protocol is unchanged. A future cue broker should use current_action.id/verification_only as instruction identity, increase cue_sequence on instruction changes within a checkpoint, and cancel older cues. It must use the admitted current frame/context for anchors, never old procedure-history frames. Delivery acknowledgements and marks never complete a checkpoint. The writer still owns actual anchor resolution, transforms/rendering, cancellation and acknowledgements.

The deployed Site still uses its Worker compatibility adapter; the equivalent Python/FastAPI logic is local until the separate Python hosting dependency is connected. No pinned source snapshot or upstream lab JSON was modified.

## Verification and limits

Actual Gemini tests on four controlled screenshots passed: Carrier shown at the Local-carrier stage, correct Local carrier settings, an incorrect local phase, and obscured wiring with named blocks. The last two are held-out visual cases. Final v3 summaries included readable values instead of only saying settings were correct. These are small regression checks on synthetic UI, not general Simulink accuracy or real scientific execution. A fixture-only eval bug involving a null name/phase was corrected before the final four-case run; no provider failure was hidden.

Native captured-tab trials passed against both backend implementations. The receiver trial exercised all five actions in order, no parameter inference from the Carrier dialog, partial instruction progress without checkpoint completion, and the next stage beginning with filter creation. Mock browser providers are explicitly labelled. Current action cards and tables were visually inspected. Required Python, Worker, immutable-source and BB8 checks are recorded in active.md. The next acceptance run is the user's real Simulink workspace after they choose to resume; nothing in this work resumes their stopped sequence.
