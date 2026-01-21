# Query Biolink Model first-order template graph

This work takes the ARS query logs and turns them into a finite set of first order patterns that are defined directly by the biolink model, rather than by observed usage. At the biolink model level, each admissible query can be abstracted as a typed mapping of the form (C_0,A_0,P,A_1,C_1), where C_0,C_1 are input and output categories, A_0,A_1 are their aspects, and P is a predicate whose domain and range are fixed by the biolink model. Using these constraints, one can systematically enumerate all possible first order templates and organize them as a template graph whose nodes are ("category" ,"aspect" ) pairs and whose edges are allowed predicate mappings between them.

## Set-up
### Locally:
git clone _this-repo_
cd biolink-templates
pip install -r requirements.txt
python generate_biolink_templates.py

### from a Google collab notebook:
#### Install dependencies (one-time)
!pip install bmt[toolkit] pandas pyyaml --quiet

#### Verify BMT works
from bmt import Toolkit
bmt = Toolkit()
print(f"✅ Biolink Model Toolkit v{bmt.version} ready!")
print(f"Found {len([p for p in bmt.get_all_elements() if bmt.is_predicate(p)])} predicates")

## Usage:
# Generate Biolink templates 

