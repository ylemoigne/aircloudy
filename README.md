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
import asyncio
from typing import Tuple, Optional
from aircloudy import HitachiAirCloud, InteriorUnit, compute_interior_unit_diff_description


def print_changes(dict: dict[int, Tuple[Optional[InteriorUnit], Optional[InteriorUnit]]]) -> None:
    for (id, change) in dict.items():
        print(f"Change on interior unit {id}: "+compute_interior_unit_diff_description(change[0], change[1]))

async def main() -> None:
    async with HitachiAirCloud("your@email.com", "top_secret") as ac:
        ac.on_change = print_changes

        unit_bureau = next((iu for iu in ac.interior_units if iu.name == "Bureau"), None)
        if unit_bureau is None:
            raise Exception("No unit named `Bureau`")

        await ac.set_power(unit_bureau, "ON")
        await ac.set(unit_bureau.copy(requested_temperature=21, fan_speed="LV3"))

        await asyncio.sleep(30)


asyncio.run(main())
```

## License

`aircloudy` is distributed under modified HL3 license. See `LICENSE.txt`.

## Development

```console
poetry run task lint
```

```console
poetry run task check
```

```console
poetry run task test
```

```console
poetry run task coverage
```