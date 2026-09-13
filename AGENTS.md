# House model repository instructions

Room names and survey IDs are recorded in the parent project instructions at
`../../AGENTS.md` and `../../Room names/room_names.json`.

## Active second-floor concept

Use `Saguramo_House_Second_Floor_Concept.blend` for second-floor work.
Preserve `Saguramo_House_Roof_Updated.blend` as the existing-house reference.
Continue the owner's `feat/second-floor` branch and PR targeting `main`.

The former red roof is replaced by a 300mm timber deck, with its top exactly
100mm above the highest original black-roof crest (top approximately 3.25064m).
Both original black roof sections and their slopes remain unchanged.

The current stage adds the owner-marked upside-down-V mansard roof. Its visible
ridge is exactly 5m above the wooden floor, not 5m above ground. Red boundaries
and blue ridge are traced in `mansard/mansard_geometry.json`. The south slope
(negative local X; +X north and +Y west) has a broad shed dormer containing an
enclosed room with a glazed door onto the upper wooden terrace. Black 1.10m
vertical-bar railings guard the remaining terrace edges; there are no north
railings, and the west run is retained only beside the open terrace.

The roof meets the north and west wooden-floor edges and leaves exactly 1m on
the east. The ridge XY and approved south dormer remain unchanged. Matching
glazed doors are in both east and west gables. A 1.10m-wide east staircase runs
from Terrace 2 through a quarter-turn to the upper east deck, opposite its door;
leave its upper railing mouth open. The stair has 19 equal rises of about 171mm,
with four winding treads, timber treads and black steel framing/guards.

Roof footprint is about 8.73 x 11.60m. Dormer room size, timber cladding,
charcoal roof finish, glazing layout and railing profiles are concept choices;
the reference images do not establish construction dimensions for these details.

Scenes 18–22 and `mansard/` contain the current previews, build and validation.
`second-floor/` contains the historical flat-floor stage. Its builder resets the
active concept: preserve later edits before rerunning it, then apply the mansard
builder and final verifier as documented in README.md.
