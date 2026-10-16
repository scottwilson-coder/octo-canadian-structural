# Canadian PyNite adapter — publication candidate

Experimental independent wrapper around **PyNiteFEA 3.2.0**, not an official PyNite edition. This source-only extraction contains reusable analysis code from the existing 0.2 development adapter. It is not the project-specific integrated building runner or a complete Canadian-code design package.

**Publication gate:** review [PUBLICATION_CHECKLIST.md](PUBLICATION_CHECKLIST.md) before public posting. Rights to the local adapter have not been independently established and no open-source license has been assigned. Upstream PyNite's MIT license does not license this wrapper.

## Quick start

Tested with Python 3.12 on Linux. Make an isolated environment:

```sh
python3.12 -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-tested.txt
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m octo_pynite examples/cantilever.json --output outputs/cantilever.json
python -m octo_pynite examples/reduced_beam.json --output outputs/reduced_beam.json
```

Each CLI run produces JSON, CSV and an offline HTML report. No solve-time upload or web service is used. Installation downloads dependencies. The exact installed versions are recorded in requirements-tested.txt; new-machine installation and other platforms have not been verified. Basic source execution works from the extracted repository without the editable-install step once dependencies are available.

## Included

- Explicit first-order elastic 3D frame model: nodes, six support freedoms, material E/G/nu/weight density, A/Iy/Iz/J, member orientation and 12 end releases.
- Nodal forces/moments, member point forces/moments and partial linearly varying distributed force loads.
- Signed member demand extrema, support reactions and global resultant balance checks. Balance uses assembled PyNite equivalent nodal loads; it is not a fully independent verification of load assembly.
- Polynomial deflection extrema from PyNite segment internals; version-pinned, endpoints plus real derivative roots.
- Explicit self-weight ownership and rejection of labelled duplicate self-weight. Disguised/unlabelled duplicate loading still needs review.
- Explicit OSM-to-frame bindings; no automatic structural connectivity from graphical coincidence.
- Reduced planar Euler–Bernoulli beam response using supplied EI. Dummy inactive-channel properties are not physical section/material properties.
- BCBC 2024 ordinary D/L/S/W/E ULS combination subset, with explicit applicability flags. Supplemental seismic companion subsets are labelled. No code text, scanned references or material tables are distributed.
- Offline reports, synthetic examples and independent analytical/regression tests.

## Canadian combination helper

```python
from octo_pynite.combinations import generate_uls
```

See tests/test_combinations.py for the complete applicability dictionary. The flags are assertions supplied by the caller, not checks of the building or governing code. Do not set them true without checking. Alternative signed W/E cases are kept separate; multiple D cases are additive. Live-load patterning must already be resolved into one L case. No special H/P/T actions, crane, soil/fluid, equipment/storage-live, roof-parking or service-room exception is handled. Named snow/wind/seismic cases contain **user-supplied loads**, not generated environmental actions. Consult the cited official code and applicable revision independently.

## Units, results and responsibility

Input uses metres, kN and kN/m²; moments kNm, line loads kN/m, inertias m⁴. Full frame material E/G use kN/m² and weight density kN/m³. Reduced EI uses kNm². Reports label millimetre deflections explicitly. Member output axes are local; support reactions are global. Positive axial demand is compression. Separate extrema are not simultaneous interaction demands.

Analysis completion and equilibrium do not mean code compliance, adequate strength or safe construction. All member resistance statuses remain NOT_CHECKED. A qualified engineer must validate geometry, properties, loads, idealization, stability, combinations and all design checks for the intended use.

See [CAPABILITIES.md](docs/CAPABILITIES.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and [verification.json](docs/verification.json).
