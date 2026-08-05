from pathlib import Path
from sst21d.table import static_campaign
if __name__=='__main__':
    print(static_campaign(Path('data/ideal_favorites.txt'),Path('outputs/static_favorites'),samples=600,metadata_path=Path('data/sst21_metadata_seed.csv'),require_native=True))
