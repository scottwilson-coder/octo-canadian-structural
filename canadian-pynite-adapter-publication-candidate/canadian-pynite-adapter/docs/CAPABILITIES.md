# Capability and verification boundary

## Implemented and exercised by synthetic tests

First-order cantilever, simply supported, continuous/split beam and reduced beam response; uniform/triangular/partial distributed loads; point forces and end moments; signed factored combinations; stiffness and member-axis sensitivity; support reactions; release behavior; explicit self weight; input immutability; finite-positive property rejection; unstable model rejection; missing references and invalid units; implicit connectivity rejection; polynomial deflection extrema; ordinary combination alternatives and applicability rejection; CLI JSON/HTML/CSV generation.

The test summary is in verification.json. These tests are small deterministic benchmarks, not certification or proof for arbitrary models.

## Implemented but not comprehensively qualified

Arbitrary 3D multi-member topology, OSM mappings, every permitted release/load/axis combination, numerical conditioning and unusual scales, adversarial schemas, arbitrary HTML identifiers and large model performance. Polynomial root selection uses numerical tolerances. Equilibrium is against solver-assembled loads, not an independent integration of every original input. Tests do not verify every governing load-rule clause, revision or jurisdiction. Input data and source_ref strings are caller assertions.

## Unsupported / excluded from this distribution

Member resistance design and CSA O86 checks; historical wood tables; member selection; connection/assembly behavior; steel/concrete/foundation/geotechnical design; bearing/tension/torsion interaction; serviceability acceptance limits; P-delta/nonlinear/unilateral behavior; dynamic/modal response; automatic climate, snow, wind or seismic generation; diaphragms/shearwalls/collectors; panel load distribution; automatic CAD geometry inference; whole-building source load routing; batch design checker; seals or professional approval.

Reduced beams are independent explicitly idealized submodels. No whole-building continuity follows from solving them. Full frames require actual stiffness and explicit accepted topology.

## Runtime verification limits

Only Python 3.12/Linux and the recorded installed dependency versions were exercised. No clean internet installation, wheel release, package registry publication, Windows/macOS verification, external security audit or exhaustive engineering validation was performed. No GitHub actions run or remote repository exists as part of this preparation.
