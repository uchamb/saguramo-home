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

The current upside-down-V roof has its ridge exactly 5m above the wooden floor,
not 5m above ground. Axes: +X north, +Y west. The latest owner plan is
`mansard/reference/roof-plan-expanded-terrace.png`.

Both east and west end terraces are exactly 1.50m deep, giving roof Y bounds
[-6.45, 3.15]. The north eave remains at X=8.58m. The red south roof boundary is
estimated from the latest drawing at X=-1.60m. The roof is 10.18 x 9.60m;
its ridge and both end glass doors must share the centered X=3.49m axis.

The yellow outline expands the wooden deck south to a continuous X=-6.85m
edge, aligned with the Entrance-side corner. Its rectangular bounds are
[-6.85, -7.95, 8.58, 4.65], area 194.418m2, retaining its height and 300mm thickness.
The south dormer follows the widened slope with its glazed terrace door.
Black 1.10m guards run along the entire west terrace and expanded south edge.
North railings stay removed; preserve the clear east stair mouth.

The east staircase stays in its approved position (center X=3.95m) and connects
to the wider east landing. Its 19 equal rises are about 171mm, with four winding
treads, timber treads and black steel framing/guards. The end doors are centered
on the mansard independently of the existing stair position.

South boundary tracing, dormer proportions, finishes and stair profiles are
concept choices; the image does not supply construction measurements for them.

Scenes 18–22 and `mansard/` contain the current previews, build and validation.
`second-floor/` contains the historical flat-floor stage. Its builder resets the
active concept: preserve later edits before rerunning it, then apply the mansard
builder and final verifier as documented in README.md.
