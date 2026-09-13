# Exterior views at 2m and 10m

Eight perspective renders of `Saguramo_House_Second_Floor_Concept.blend`, from the southeast corner, southwest corner, south side and west side. Each direction uses an identical camera XY and focal length at both heights.

The height datum is the top of the model's outdoor parcel surface, Z=-0.74m. Cameras therefore sit at model Z=1.26m and Z=9.26m, exactly 2m and 10m above outdoor ground. The raised first-floor slab is Z=0m. The parcel grade remains the existing model's schematic assumption.

Open `index.html` for the gallery, `comparison.jpg` for all eight views together, or the individual 1920 × 1440 PNGs in `02m/` and `10m/`. `exterior-renders.zip` contains all eight full-resolution images and the comparison sheet. Rendering leaves the source model file unchanged.

To reproduce from the repository root:

```bash
blender --background Saguramo_House_Second_Floor_Concept.blend --threads 8 --python renders/exterior-heights/render_views.py
python3 renders/exterior-heights/package_views.py
```

Blender uses Cycles with 64 samples and denoising. The packaging script needs Pillow. Camera coordinates, projected framing bounds and source model hash are in `render_manifest.json`; PNG sizes, distinct hashes, camera heights and source preservation are checked in `verification.json`.
