---
name: toc-common
description: Common modules and configuration files for the ToC auto-generation system. Referenced by other ToC-related skills.
allowed-tools: []
user-invocable: false
---

# toc-common

Provides common modules and configuration files for the ToC auto-generation system (rules_toc.yaml / specs_toc.yaml).

## Overview

This skill is not invoked directly but is referenced by the following skills:

- `merge-rules-toc` - rules_toc.yaml merge processing
- `merge-specs-toc` - specs_toc.yaml merge processing
- `create-toc-checksums` - Checksum file generation

## Provided Files

| File | Purpose |
|------|---------|
| `toc_utils.py` | Common utility functions |

## Usage (from scripts)

```python
import sys
from pathlib import Path

# Add common module path
COMMON_DIR = Path(__file__).parent.parent / "toc-common"
sys.path.insert(0, str(COMMON_DIR))

from toc_utils import load_config, parse_simple_yaml, yaml_escape
```
