# aircloudy

[![PyPI - Version](https://img.shields.io/pypi/v/aircloudy.svg)](https://pypi.org/project/aircloudy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aircloudy.svg)](https://pypi.org/project/aircloudy)

Aircloudy is an unofficial python library that allow management of RAC (Room Air Conditioner) compatible with Hitachi Air Cloud.

This project IS NOT endorsed by Hitachi and is distributed as-is without warranty.

-----

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Development](#development)

## Installation

```console
pip install aircloudy
```

## Usage

```python
from __future__ import annotations
import asyncio
from aircloudy import HitachiAirCloud, InteriorUnit, compute_interior_unit_diff_description


def print_changes(dict: dict[int, tuple[InteriorUnit|None, InteriorUnit|None]]) -> None:
    for (id, change) in dict.items():
        print(f"Change on interior unit {id}: "+compute_interior_unit_diff_description(change[0], change[1]))

async def main() -> None:
    async with HitachiAirCloud("your@email.com", "top_secret") as ac:
        ac.on_change = print_changes

        unit_bureau = next((iu for iu in ac.interior_units if iu.name == "Bureau"), None)
        if unit_bureau is None:
            raise Exception("No unit named `Bureau`")

        await ac.set(unit_bureau.id, "ON")
        await ac.set(unit_bureau.id, requested_temperature=21, fan_speed="LV3")

        await asyncio.sleep(30)


asyncio.run(main())
```

## License

`aircloudy` is distributed under modified HL3 license. See `LICENSE.txt`.

## Development

```shell
poetry run task lint
```

```shell
poetry run task check
```

```shell
poetry run task test
```

```shell
poetry run task coverage
```

```shell
poetry --build publish
```

## Notes

Not read/used field from notification :
```
iduFrostWashStatus: IduFrostWashStatus
        active: bool
        priority: int
        astUpdatedA: int
        subCategory = None
        errorCode = None
specialOperationStatus: SpecialOperationStatus
        active: bool
        priority: int
        lastUpdatedAt: int
        subCategory = None
        errorCode = None
errorStatus: ErrorStatus
        active: bool
        priority: int
        lastUpdatedAt: int
        subCategory: str
        errorCode = None
cloudId: str
opt4: int
holidayModeStatus: HolidayModeStatus
        active: bool
        priority: int
        lastUpdatedAt: int
        subCategory = None
        errorCode = None
SysType: int
```

Not read/used field from API:
```
userId: str
iduFrostWash: bool
specialOperation: bool
criticalError: bool
zoneId: str
```