# Reviewed coordinator dependency

`cycle.py` is the byte-identical source distribution of the existing
installed PMCR-O Cycle skill's `scripts/cycle.py`, SHA-256
`29ff64b78b1347535167885812a095984954ca810eec2d1743ee1bb21207c3a4`.
It is not a second authored coordinator. Do not edit this copy: update the
authoritative skill first, validate it, then refresh the pinned dependency
and integrity gate together. This distribution lets an otherwise isolated
CI runner execute the exact reviewed coordinator without private host access.
