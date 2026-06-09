# openEHR Archetype Inclusion Patterns
Interactive network visualization of archetype inclusion (containment) relationships extracted from openEHR templates across multiple Clinical Knowledge Manager (CKM) repositories.
👉 **[View the live visualization](https://martinkochdesign.github.io/openEHR_archetype_inclusion_patterns/)**

## Overview
This tool analyses openEHR Operational Templates (`.oet` files) from several international CKM mirrors to discover how archetypes are nested within one another. It builds a directed graph of parent → child archetype containment and classifies each relationship by frequency (**often** or **sometimes**), providing a bird's-eye view of common modelling patterns in the openEHR ecosystem.
## Data Sources
Templates are fetched from the following CKM mirrors:

| Repository | Scope |
| --- | --- |
| [openEHR/CKM-mirror](https://github.com/openEHR/CKM-mirror) | International CKM |
| [AppertaFoundation/apperta-uk-ckm-mirror](https://github.com/AppertaFoundation/apperta-uk-ckm-mirror) | United Kingdom (Apperta) |
| [CKMCatSalut/CKM-mirror](https://github.com/CKMCatSalut/CKM-mirror) | Catalonia (CatSalut) |
| [Arketyper-no/ckm](https://github.com/Arketyper-no/ckm) | Norway |
| [openEHR-de/CKM-mirror](https://github.com/openEHR-de/CKM-mirror) | Germany |

## How It Works
1. **Download** — ZIP archives of each CKM repository are fetched via the GitHub API.
2. **Extract** — All `.oet` template files are flattened into a temporary working directory.
3. **Parse** — Each template's XML tree is walked recursively to identify `archetype_id` references and their parent-child containment relationships.
4. **Aggregate** — Inclusion pairs are counted across all templates and classified:
   - **often** — the pair appears in more than 10 templates.
   - **sometimes** — the pair appears in 10 or fewer templates.
5. **Visualise** — A `dataset.js` file is generated containing [vis.js](https://visjs.org/) `DataSet` definitions (nodes and edges) ready for interactive graph rendering.
## Output
| File | Description |
|---|---|
| `dataset.js` | vis.js nodes & edges for the interactive network graph |
| `source_data.xlsx` | Flat table of all containment relationships with source CKM |

## Requirements
- Python 3.8+
- Dependencies:
```bash
pip install lxml requests pandas openpyxl
```
## Usage

```
python main.py
```
The script will download the latest templates, parse them, and regenerate dataset.js and source_data.xlsx.

Note: The first run downloads several large ZIP archives and may take a few minutes depending on your connection.

## Licence
Apache 2.0

## Author
**Martin A. Koch, PhD**
martinandreaskoch@catsalut.cat

© 2026, Servei Català de la Salut (CatSalut)