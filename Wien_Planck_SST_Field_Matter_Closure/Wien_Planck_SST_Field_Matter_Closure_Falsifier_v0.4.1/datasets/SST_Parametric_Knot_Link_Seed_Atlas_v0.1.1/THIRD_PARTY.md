# Third-party / redistribution note

PKLSA v0.1.1 uses topology/geometry provenance from the user-provided Knot Atlas source archive and Brian Gilbert Fourier records. The upstream `Ideal_Sources` provenance explicitly marks redistribution/licence status of the original record files as unresolved. Those upstream `.gz` files are **not** included in this archive.

The atlas does include derived sampled coordinates for internal SST research/reproducibility. Before distributing PKLSA as public or journal supplementary data, resolve the upstream licensing question or distribute only the reconstruction recipe/manifests and require users to obtain the upstream source independently.

The optional SYCL code in `gpu_template/` is newly written integration scaffolding for this package and does not contain upstream shader source.
