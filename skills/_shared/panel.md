# The panel

The panel lives in the session DB — same SQLite file as the DAG, separate
`panelists` table (see [running on skillflow](running-on-skillflow.md)).
`panel/panelists.json` is only the seed source. Every room is formed the same
mechanical way: match panelists to the situation's tensions semantically,
then enforce diversity. No fixed cast, no turn order, no prose judgment
calls — the DAG does it.

## What a panelist is

Each entry has a name, an id, a lens (the question it cannot stop asking),
attributes (what it notices, how it argues, what it refuses to let slide), a
family (exactly one of `clarity`, `risk`, `measure`, `incentives`, `human`),
and tags (topics that match it). The roster holds 128 panelists, from
general lenses to narrow specialists.

## How a room forms

1. Name the live tensions — two to five, harvested from what has been said.
2. Run the selector (`panel/select_room.py`) with those tensions. It ranks
   panelists by tag overlap, then enforces diversity: at most one per family,
   three to five seats, at least three families covered. Score proposes;
   diversity disposes.
3. The selected room collides over the round's question. No turn order.
4. End the round with collisions and new tensions. New tensions re-run the
   selector and re-form the room.

Add panelists by appending entries: id, lens, attributes, family, tags. The
selector and the diversity rule need no changes.
