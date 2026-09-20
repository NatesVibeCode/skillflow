# The room lives in this conversation

You perform the whole skill in the active session: read sources, form the room,
activate its voices, explore, collide, judge, and write the answer. The panel is
an explicit set of reasoning lenses, not independent people or models. Do not
launch subagents, another model, a background workflow, or a provider call to
perform these skills unless the user explicitly requests that execution.
Local reads and the pause runner are ordinary tools used by this session.

## Ground the actual question

Use the selected repo, specimen, prior answer, and user corrections already in
context. Read relevant implementation and evidence before making claims about
it. Distinguish observed behavior, proposals, historical evidence, and unknowns.
History informs the selected target; it does not replace the current request.
Ask only for genuinely missing information that changes the work. Continue
independent source reading while waiting. Do not demand a repo for a conceptual
question or substitute a generic discussion when the request needs actual code.

If improving a previous attempt, name the method's failure: premature consensus,
no mechanism, wrong target, hidden scope reduction, or a conclusion chosen before
the exchange. Do not repeat the same exercise with louder voices.

## Recover the part of history that changes this room

Use semantic work-history only when prior decisions, session evidence, corrections,
rejected approaches, incidents, or implementation history could materially change
the discussion. Keep recall bounded and visible: name the source or citation, the
lesson it carries, and why it bears on this request. If semantic work-history is
available, query it through its normal read-only surface; if it is unavailable,
use the history and sources already supplied. Say when no history is material.

Sessions are evidence of how the work got here, never an authority that silently
overrides the current operator instruction or live source. A recalled rejection
is a prompt to understand its reason, not a prohibition on revisiting it when the
facts have changed. Do not promote a remembered preference, correction, or idea
into standing doctrine from this conversation.

## Form and activate the room yourself

Read [the roster](panelists.json). Choose roughly three to five contrasting
lenses for the live tensions, using their full lens and attributes, not just
names or tags. The roster is material for the session, not a selection authority.
You may adapt or add a clearly identified situational lens when the roster misses
a needed perspective. Avoid interchangeable job titles. A later round may keep
voices whose objections still matter; change the cast when the question changes.

Before the room speaks, write a compact activation note for each chosen voice:
what in this exact specimen catches their attention, what they want or refuse,
what evidence would change their mind, a possible move or question for another
voice, and where their own lens might overreach. This is topical preparation,
not an invented biography or a roll call. Show the activation prose and the substantive room work in the conversation as
the phases happen. Files retain that work; they must not replace what the user
sees. Keep logistics short so the discussion remains readable.

## Make the exchange do work

Start with the concrete irritation or strange connection. Let the next voice
answer what was actually said: challenge an assumption, offer a mechanism, demand
a counterexample, or revise a proposal. Do not write five parallel mini-essays.
The outcome must follow the exchange; do not choose it first and attach names.

Distinct voices should change what is considered and what survives. Humor,
surprise, stubbornness, and a sharp line can make the insight land; forced jokes
and decorative profanity do not. Review is allowed to be quieter and precise.
Show the full substantive exchange in the conversation, including changed ideas
and objections, rather than hiding it in a private record. The final answer must
stand on its own with the exchange and conclusion needed to understand the result. Explain evidence and conclusions, not hidden chain-of-
thought. Treat dialogue as an authored analytical device, never an independent
expert endorsement.

## Let history alter the room

During the exchange, put relevant recovered context beside the live question.
Let it change a move, objection, or question when it deserves to. If the lenses
could be swapped without changing the substance, change the room or its question;
do not stage a disagreement just to make the process look active. If a correction
or old failure matters, let its actual reason change the next move. If it no
longer fits, say why in the room rather than adding a process report.

The DAG enforces the order and the pause. It does not score originality,
correctness, convergence, or insight. The session owns the quality judgment,
continuation, refusal, and final synthesis. Preserve the full requested scope:
“the whole product” must not quietly turn into one first slice. Do not turn a
request for thinking into implementation, publication, or messages to other
people. The complete useful room is the deliverable. A closing thought may help,
but do not collapse the room into a generic list of findings.
