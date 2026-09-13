# Saguramo house model

## Latest: Childroom terrace door and basement railings

Open **Saguramo_House_Roof_Updated.blend**. The Childroom opening onto Terrace 1 now matches the supplied close-up: full-height glazing on both sides, a central pleated insect screen, black framing and a low threshold. Its surveyed width and position are retained; the 2.50m head height and panel proportions are photo estimates.

Both low brick guards beside the basement stairs are replaced with black metal railings: square posts, horizontal top/bottom rails and straight vertical bars. The original guard runs and 0.95m height are retained; profiles and spacing are estimated from the reference. Existing stair treads, room layouts, roof slopes and other openings are unchanged.

Scenes **12 Childroom terrace door** and **13 Basement railings** show the changes. Previews, source close-ups, geometry specification and verification are in `detail-update/`. The previous roof-only model remains in Git history.

To apply these details after rebuilding the roof model with the commands below:

```bash
.venv/bin/python detail-update/prepare_details.py
blender --background Saguramo_House_Roof_Updated.blend --threads 8 --python detail-update/update_details.py
blender --background Saguramo_House_Roof_Updated.blend --python detail-update/verify_details.py
```

The detail builder expects the roof-only stage as input. The current full model is checked with `detail-update/verify_details.py`; the older roof validator applies before the detail stage.

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
