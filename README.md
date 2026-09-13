# Saguramo house model

## Second-floor concept: mansard, terrace doors and east staircase

Open **Saguramo_House_Second_Floor_Concept.blend** on `feat/second-floor`. The roof follows the owner's marked red rectangle and blue ridge: two straight slopes form an upside-down V, with the highest ridge crest **5.00m above the wooden floor** (8.25064m above the main floor). The roof now reaches the wooden floor's **north and west edges**, with an **exactly 1m terrace strip on the east**. Its revised footprint is approximately **8.73 × 11.60m**; the blue ridge location is retained.

A broad shed dormer on the **south slope (negative local X)** contains an enclosed room, inspired by the supplied structural reference. Its black-framed central glazed door opens directly onto the upper wooden terrace, with full-height fixed glazing on both sides. The main sloping roof has an actual cut-out around the dormer. Timber-clad cheeks, front piers, rear wall and a sloping ceiling enclose the room. Its approximately 18.22m² gross footprint, 1.00m door width, 2.20m door height, cladding and charcoal roof finish are concept choices.

Matching central glass doors with fixed sidelights are installed in both the **east and west gables**, with real openings in the walls. The east door faces the 1m terrace strip; the west door is at the deck edge beside the unchanged black roof.

A **1.10m-wide east staircase** follows the owner's green outline: a lower flight along Terrace 2, four quarter-turn winding treads, then a flight up to the east deck edge opposite the door. Its 19 equal rises are approximately 171mm. Black steel framing and vertical-bar guards support timber treads matching the deck. Width, tread count and profiles are concept dimensions chosen to fit the actual floor rise and terrace footprint. The stair mouth is open through the upper railing.

The uncovered wooden floor is the upper terrace. **North railings are removed**, and the **west railing is retained only beside the open terrace**, ending at the mansard. The remaining upper guards are 1.10m high. The floor remains 300mm thick, with its top at 3.25064m, exactly 100mm above the highest existing black-roof crest. Its 177.1064m² footprint is unchanged. Both original black roofs and all 437 meshes from the flat-floor stage remain unchanged. The existing-house reference **Saguramo_House_Roof_Updated.blend** is preserved byte for byte.

Scenes **18 Mansard concept**, **19 Mansard plan**, **20 South dormer and terrace**, **21 East doors and staircase** and **22 West glass door** show the current stage. Renders, references, geometry and saved-file verification are in `mansard/`. Scenes 15–17 remain available; previews in `second-floor/` record the earlier flat-floor stage.

![Mansard and terrace access](mansard/concept.png)

![East staircase and glass door](mansard/east-stair.png)

Rebuild in this order; the first builder resets the concept to the historical flat-floor stage before the mansard is reapplied:

```bash
.venv/bin/python second-floor/prepare_floor.py
blender --background Saguramo_House_Roof_Updated.blend --threads 8 --python second-floor/build_concept.py
blender --background Saguramo_House_Second_Floor_Concept.blend --python second-floor/verify_concept.py
.venv/bin/python mansard/prepare_mansard.py
blender --background Saguramo_House_Second_Floor_Concept.blend --threads 8 --python mansard/build_mansard.py
blender --background Saguramo_House_Second_Floor_Concept.blend --python mansard/verify_mansard.py
```

Final verification reopens the saved model and checks the exact ridge height, roof alignment with both deck edges, the 1m east setback, 34 closed roof/room/stair solids, all three door openings, railing removals and the clear stair mouth. It measures every tread and final rise into the deck, checks the first tread and turning support sit on Terrace 2, and verifies preservation of all 437 baseline house/deck meshes and 49 approved south-dormer meshes. The earlier flat-stage validator checks deck thickness, clearance, original black-roof slopes and removal of red roof geometry before the new roof is added.

## Existing house: two columns per railing and matching terrace tiles

The Terrace 1 side of the basement railing now terminates at the existing black canopy column. Each railing has one additional 85mm square roof-height column, with its centre **1.00m from Bathroom 2's exterior wall** along the railing. The west railing also has a full-height end column replacing its former short end post, so **both east and west railings now have two full-height columns**. Their tops fit the existing sloping soffit. The east railing remains as previously approved; stair access remains open.

Terrace 1, Terrace 2 and the Terrace 1 entry steps share the same square-tile material with mottled grey, taupe and brown colouring, pale weathered patches and thin grout joints, based on the owner's tile photograph. **500mm tile size is an estimate**, not a supplied measurement. This is a self-contained procedural Blender material. Scene **13 Basement railings** shows the corrected supports and scene **14 Terrace 1 tiles** shows the finish; current previews are in `terrace-update/`.

Apply this final stage after the door/railing stage below:

```bash
blender --background Saguramo_House_Roof_Updated.blend --threads 8 --python terrace-update/update_terrace.py
blender --background Saguramo_House_Roof_Updated.blend --python terrace-update/verify_terrace.py
blender --background Saguramo_House_Roof_Updated.blend --threads 8 --python terrace-update/match_west_columns.py
blender --background Saguramo_House_Roof_Updated.blend --python terrace-update/verify_final_terraces.py
```

Final saved-file validation confirms two full-height columns per railing, the west end column’s roof and railing contacts, identical materials on both terraces, unchanged floor geometry, and preservation of the east railing and unrelated meshes. See `terrace-update/final_verification.json`. Earlier validators apply to their respective build stages.

## Childroom terrace door and basement railings

Open **Saguramo_House_Roof_Updated.blend**. The Childroom opening onto Terrace 1 now matches the supplied close-up: full-height glazing on both sides, a central pleated insect screen, black framing and a low threshold. Its surveyed width and position are retained; the 2.50m head height and panel proportions are photo estimates.

Both low brick guards beside the basement stairs are replaced with black metal railings: square posts, horizontal top/bottom rails and straight vertical bars. The original guard runs and 0.95m height are retained; profiles and spacing are estimated from the reference. Existing stair treads, room layouts, roof slopes and other openings are unchanged.

Scenes **12 Childroom terrace door** and **13 Basement railings** show the changes. Previews, source close-ups, geometry specification and verification are in `detail-update/`. The previous roof-only model remains in Git history.

To apply these details after rebuilding the roof model with the commands below:

```bash
.venv/bin/python detail-update/prepare_details.py
blender --background Saguramo_House_Roof_Updated.blend --threads 8 --python detail-update/update_details.py
blender --background Saguramo_House_Roof_Updated.blend --python detail-update/verify_details.py
```

The detail builder expects the roof-only stage as input. Use `detail-update/verify_details.py` at this build stage, before the final terrace refinements; the older roof validator applies before the detail stage.

## Drone roof and brick finish

Open **Saguramo_House_Roof_Updated.blend**. This includes the previous window corrections plus the roof reconstructed from the nine drone photographs. All newer roof sections remain black; the older hip roofs and raised gable are reddish. Scenes 09–11 show the roof from above and from both sides. The file opens with material preview enabled so the brick texture is visible.

The south black roof falls south at **2 cm/m (2%)**. The west black roof falls west at **6 cm/m (6%)**, including its annex projection. These slopes were specified by the owner and verified from the saved mesh geometry. The main walls and the high west wall at the red roof are **3.00m**, supplied by the owner. Keeping the confirmed 6% west slope gives approximately **2.73m** at the main west wall and **2.63m** at the projecting annex wall. The owner explicitly confirmed that 6cm/m takes priority over the approximate 2.55m low-wall figure. Roof surfaces sit 125mm above the wall datum (estimated build-up), with a main ridge at 4.625m. Red-roof pitch, overhangs and corrugated sheet details remain photo-based estimates.

The red-brown brick material uses procedural brick-by-brick colour variation, occasional dark bricks, mortar depth and fine surface texture. Existing interior plaster remains. No texture downloads or linked image assets are needed.

Validation checks that corrected window/door meshes and unrelated geometry remain identical, wall footprints are retained, and wall tops and ceilings follow the owner heights. All 11 roof panel solids are closed. See `roof-update/verification.json` and `ROOF_UPDATE_NOTES.txt` in that folder. Earlier `.blend` files remain available.

Rebuild from the window-corrected model using `roof-update/prepare_roof.py` followed by Blender with `--python roof-update/update_roof.py`. The builder calls `apply_wall_heights.py` to split wall meshes at the west roof transition and apply the owner heights. Run `roof-update/verify_roof.py` against the saved roof model to verify slopes and preserved geometry.

To reproduce the latest roof model from the included window-corrected file:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python roof-update/prepare_roof.py
blender --background Saguramo_House_Photo_Updated.blend --threads 8 --python roof-update/update_roof.py
blender --background Saguramo_House_Roof_Updated.blend --python roof-update/verify_roof.py
```

The optional `finalize_roof.py` refreshes perimeter trim and previews from the same geometry specification. `prepare_infills.py` and its JSON outputs are retained from the earlier roof iteration; the current builder uses the owner-height wall meshes directly.

## Photo-corrected version

The earlier window-only version is **Saguramo_House_Photo_Updated.blend**. It uses IMG_2621.HEIC, IMG_2622.HEIC and IMG_2623.HEIC to correct eight opening groups on the east, south and west facades. Scenes 06–08 provide direct facade views. The original model remains available as Saguramo_House.blend.

Window heights and the missing south window placement are photo-based estimates. Detailed values and provenance are in `photo-update/facade_adjustments.json`; renders are `photo-update/east.png`, `south.png`, `west.png` and `exterior.png`.

Verification: 317 unrelated original meshes remain identical; 133 corrected meshes are closed solids; 120 clearance samples confirm that wall geometry does not obstruct the corrected openings. The saved file was reopened successfully. Rebuild the update with `photo-update/prepare_facades.py`, then run Blender on the original file with `--python photo-update/update_facades.py`. Validate with `photo-update/verify_update.py` against the updated file.

Open **Saguramo_House.blend** in Blender 5.2.1 or newer. Choose a scene in the top bar:

- **01 Exterior** — complete house with estimated roof and finishes.
- **02 Roofless interior** — measured rooms, walls and openings.
- **03 Basement inspection** — basement and descending stairs without surrounding ground.
- **04 Survey site** — house on the surveyed parcel and easement.
- **05 Measured floor plan** — overhead view with room areas.

Use the middle mouse button to orbit, the wheel to zoom, and Shift + middle mouse to pan. Numpad 0 switches to the scene's prepared camera. Roofs are in collection **05 Roof - estimated**. Units are metres. Each survey mesh includes its source record in Custom Properties.

## What the model uses

The footprints of walls, rooms, windows, doors, veranda, terrace and basement come directly from the supplied `shp sartuli/unit_polygon.shp` and `shp sardafi/unit_polygon.shp`. Room layouts were visually compared with pages 2 and 4 of `შიდა აზომვით ნახაზი პდფ.pdf`. The three `shp/001.jpg`–`003.jpg` exterior photos informed the brick, dark frames, wood soffits and canopy. Parcel and easement shapes use `shp/nakveti.shp` and `shp/valdebuleba.shp`. The DWG files were not needed to reproduce the geometry; they were left untouched.

- Main rooms and veranda: **205.14 m²**.
- Terrace: **52.93 m²**.
- Main total including terrace: **258.08 m²**, matching the measured plan.
- Basement rooms: **52.83 m²**.
- Original plan ceiling heights: **2.90 m** and **2.52 m**. The latest model uses owner-supplied **3.00m** main wall/ceiling heights and sloping west ceilings; basement remains unchanged.

The February/March 2025 source files do not establish later changes. Roof geometry, opening elevations, finishes, frame divisions, door swings, post sizes, slab thicknesses, stair rises and surrounding grade are estimates. Room functions and furnishings are not invented. This is an editable architectural representation, not a structural or construction design. Full assumptions are in **MODEL_NOTES.txt** and the Blender text block **START HERE - sources and assumptions**.

## Verification

All 57 source polygons were checked against their stored survey areas. The saved Blender file was reopened and checked for finite coordinates, closed survey solids, measured wall heights and five inspection scenes. The largest projected area difference among the 63 checked source meshes was under **0.000003 m²**; this is a numerical import check, not a claim of survey accuracy. See `mesh_verification.json` and `validation.json`. Rendered views were visually inspected.

## Rebuild

`prepare_geometry.py` reads the unchanged source shapefiles into `survey_geometry.json`. It needs Python with pyshp, Shapely 2.1+ and matplotlib; the local `.venv` contains these packages. Run it from any working directory, then:

```bash
blender --background --threads 8 --python build_house.py
blender --background Saguramo_House.blend --python verify_house.py
```

Run the Blender commands in this output folder. The builder regenerates the `.blend`, four PNG previews, notes and area report. Materials are procedural and require no external textures. UTM origin and local axes are stored in the scene and JSON.
