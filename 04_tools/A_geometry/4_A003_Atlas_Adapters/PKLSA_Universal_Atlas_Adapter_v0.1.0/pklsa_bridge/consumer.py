"""Small downstream-reader for exported immutable SST atlas datasets.

Old and new falsifiers can read the dataset contract without installing the
original E010 source parsers or copying the mega-atlas into the consumer.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from .adapter import AtlasContractError, verify_export, sha256_file


class ConsumerDataset:
    """Verified read-only consumer dataset. Never qualifies physics."""
    def __init__(self, dataset_root):
        self.root=Path(dataset_root).expanduser().resolve()
        self.verification=verify_export(self.root)
        self.manifest=json.loads((self.root/'DATASET_MANIFEST.json').read_text(encoding='utf8'))
        self._by_id={item['atlas_record']['id']:item for item in self.manifest['records']}
        if len(self._by_id)!=len(self.manifest['records']):
            raise AtlasContractError('Duplicate IDs in exported consumer manifest')

    def list_ids(self):return list(self._by_id)

    def metadata(self, identity):
        if identity not in self._by_id:raise KeyError(identity)
        return self._by_id[identity]['atlas_record'].copy()

    def load(self, identity):
        """Return ordered list of Nx3 float64 arrays, verifying hashes on read."""
        if identity not in self._by_id:raise KeyError(identity)
        record=self._by_id[identity]
        components=[]
        for part in record['exported_components']:
            p=(self.root/part['relative_path']).resolve()
            if not p.is_relative_to(self.root):
                raise AtlasContractError('Consumer path escaping export root')
            if sha256_file(p)!=part['sha256']:
                raise AtlasContractError('Consumer component hash mismatch: '+str(p))
            data=np.loadtxt(p,dtype=np.float64,ndmin=2)
            if data.shape!=(part['exported_point_count'],3) or not np.isfinite(data).all():
                raise AtlasContractError('Invalid component shape or coordinates')
            components.append(data)
        return components
