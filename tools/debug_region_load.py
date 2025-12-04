
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.utils.df import game_configs
from src.classes.region import NormalRegion, resolve_region
from src.classes.map import Map
from src.classes.animal import animals_by_id
from src.classes.plant import plants_by_id

print("Checking configs...")
print(f"Loaded {len(animals_by_id)} animals.")
print(f"Loaded {len(plants_by_id)} plants.")

# Check specific IDs
if 10 in animals_by_id:
    print(f"Animal 10 found: {animals_by_id[10].name}")
else:
    print("Animal 10 NOT found!")

# game_configs['normal_region'] is a list of dicts, not a DataFrame
normal_regions = game_configs.get('normal_region', [])
region_114 = next((r for r in normal_regions if r.get('id') == 114), None)

if region_114:
    print("Region 114 found in dataframe")
    print(f"Region 114 raw animal_ids: {region_114.get('animal_ids')}")
else:
    print("Region 114 NOT found in dataframe")

print("\n--- Instantiation Test ---")
try:
    # Manually create a NormalRegion to see if __post_init__ works
    # Note: Region base class requires 'cors' which we can mock
    
    # Mock data for 幽冥毒泽 (ID 113) - has animal 9
    r113 = NormalRegion(
        id=113,
        name="幽冥毒泽",
        desc="Test Desc",
        animal_ids=[9],
        plant_ids=[]
    )
    # Mock cors injection which usually happens in load_map
    r113.cors = [(0,0)] 
    # Re-trigger post_init logic that depends on cors if any, 
    # but NormalRegion.__post_init__ calls super().__post_init__ then populates animals
    # Let's check if animals are populated.
    
    print(f"Created Region 113: {r113.name}")
    print(f"Animals list length: {len(r113.animals)}")
    if r113.animals:
        print(f"First animal: {r113.animals[0].name}")
        print(f"Structured Info: {r113.get_structured_info()}")
    else:
        print("ANIMALS LIST IS EMPTY!")

except Exception as e:
    print(f"Instantiation Error: {e}")
    import traceback
    traceback.print_exc()

