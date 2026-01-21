# Query Biolink Model first-order template graph

This work takes the ARS query logs and turns them into a finite set of first order patterns that are defined directly by the biolink model, rather than by observed usage. At the biolink model level, each admissible query can be abstracted as a typed mapping of the form (C_0,A_0,P,A_1,C_1), where C_0,C_1 are input and output categories, A_0,A_1 are their aspects, and P is a predicate whose domain and range are fixed by the biolink model. Using these constraints, one can systematically enumerate all possible first order templates and organize them as a template graph whose nodes are ("category" ,"aspect" ) pairs and whose edges are allowed predicate mappings between them.

## Set-up
### Locally:
````
git clone _this-repo_
cd biolink-templates
pip install -r requirements.txt
python generate_biolink_templates.py
````

### from a Google collab notebook:
#### Install dependencies (one-time)
````
!pip install bmt[toolkit] pandas pyyaml --quiet
````

#### Verify BMT works
````
from bmt import Toolkit
bmt = Toolkit()
print(f"Biolink Model Toolkit v{bmt.version} ready!")
print(f"Found {len([p for p in bmt.get_all_elements() if bmt.is_predicate(p)])} predicates")
````

## Usage:
### Generate Biolink first order templates 
````
"""Generate complete Biolink template graph for ARS log analysis"""

print("Generating Biolink templates graph...")

### Initialize Biolink Model Toolkit
bmt = Toolkit()

### 1. Generate templates from Biolink ontology
templates_df = generate_biolink_templates(bmt)
templates_df.to_csv('biolink_templates.csv', index=False)

### 2. Create KGX graph format (nodes/edges TSVs)
create_kgx_tsv(templates_df)

### 3. Generate human-readable YAML specification
yml_spec = generate_yml_spec(templates_df)
with open('biolink_templates.yml', 'w') as f:
    yaml.dump(yml_spec, f, sort_keys=False, indent=2, default_flow_style=False)

print(f"""SUCCESS from Biolink:
   • {len(templates_df)} templates → biolink_templates.csv
   • KGX TSVs → biolink_templates_kgx/
   • YAML spec → biolink_templates.yml""")
````

## Output files:

File	Purpose	For
biolink_templates.csv	Core template table	Computational team log processing
biolink_templates_kgx/	Graph visualization	Neo4j, Cytoscape, analysis
biolink_templates.yml	Documentation	Reference, reproducibility
