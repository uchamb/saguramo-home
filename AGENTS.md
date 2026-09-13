# House model repository instructions

Room names and survey IDs are recorded in the parent project instructions at
`../../AGENTS.md` and `../../Room names/room_names.json`.

## Active second-floor concept

For work on the second-floor concept, use
`Saguramo_House_Second_Floor_Concept.blend`. Preserve
`Saguramo_House_Roof_Updated.blend` as the existing-house reference.

The current owner-requested stage is a flat timber-finished floor, 300mm thick,
with its top exactly 100mm above the highest point of the black roof (including
corrugation crests). This replaces the red roof. Keep both black roof sections
and their slopes. The current top is approximately 3.25064m above the main floor.
Do not add a mansard, upper walls or other upper-storey construction unless the
owner requests the next design step. The former red roof footprint is retained.

Scenes 15–17 and `second-floor/` contain the initial concept previews, build
scripts and validation. `build_concept.py` starts from the existing house and
resets the concept to this first stage; preserve later concept edits before
rerunning it. Floor thickness and roof clearance are owner-supplied; board sizes are visual assumptions.
