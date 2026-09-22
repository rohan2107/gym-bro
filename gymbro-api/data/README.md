# data/

`usda_foods.json` is a trimmed copy of three USDA FoodData Central bulk releases (Foundation,
Survey/FNDDS, SR Legacy - Branded excluded), built by
[`scripts/build_usda_dataset.py`](../scripts/build_usda_dataset.py) and loaded into the
`usda_food` table by an Alembic migration. See
[docs/adr/0010-usda-as-a-local-reference.md](../../docs/adr/0010-usda-as-a-local-reference.md)
for why this is committed data rather than a live API call.

The file's own `manifest` key records which releases it came from, when it was built, and the
licence (USDA FoodData Central is public domain, CC0; crediting FoodData Central as the source
is requested, not required).

To refresh after USDA issues a new release, update the dated filenames in
`RELEASES` in `build_usda_dataset.py`, re-run it, and write a new Alembic migration that loads
the regenerated file (do not edit an already-applied migration).
