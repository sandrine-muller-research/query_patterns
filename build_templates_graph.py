#!/usr/bin/env python3
"""
Generate Biolink Model first-order template graph in TSV + YAML formats
"""

import pandas as pd
import yaml
from bmt import Toolkit
from pathlib import Path
import os
import hashlib


NULL_NODE = "__NULL__"

import pandas as pd
from bmt import Toolkit

NULL_NODE = "__NULL__"

import pandas as pd
from bmt import Toolkit

NULL_NODE = "__NULL__"

def generate_biolink_templates(
    bmt: Toolkit,
    version: str | None = None
) -> pd.DataFrame:
    """
    Generate all possible Biolink templates:
      - Class → Predicate → Class
      - with optional subject/object aspects (qualifiers)
      - including NULL source/target nodes
    """

    classes = list(bmt.get_all_classes())
    predicates = [e for e in bmt.get_all_elements() if bmt.is_predicate(e)]

    templates = []

    def norm(x: str | None) -> str:
        return "NULL" if x is None else x.strip().lower()

    for src_class in classes + [NULL_NODE]:
        for pred in predicates:
            pred_el = bmt.get_element(pred)

            # ----- DOMAIN -----
            domain = getattr(pred_el, "domain", None)
            if src_class != NULL_NODE and domain:
                if (
                    src_class != domain
                    and src_class not in bmt.get_descendants(domain)
                ):
                    continue

            # ----- RANGE -----
            range_class = getattr(pred_el, "range", None)
            if range_class:
                tgt_classes = bmt.get_children(range_class)
                if not tgt_classes:
                    tgt_classes = [range_class]
            else:
                tgt_classes = [NULL_NODE]

            # ----- ASPECTS -----
            subj_aspects = [None]
            obj_aspects = [None]

            slots = getattr(pred_el, "slots", []) or []

            if "subject_aspect_qualifier" in slots:
                subj_aspects = (
                    bmt.get_children("biolink:GeneOrGeneProductAspect")
                    or [None]
                )

            if "object_aspect_qualifier" in slots:
                obj_aspects = (
                    bmt.get_children("biolink:GeneOrGeneProductAspect")
                    or [None]
                )

            # ----- TEMPLATES -----
            for tgt_class in tgt_classes:
                for src_aspect in subj_aspects:
                    for tgt_aspect in obj_aspects:

                        src_cat = (
                            None if src_class == NULL_NODE
                            else src_class.replace("biolink:", "")
                        )
                        tgt_cat = (
                            None if tgt_class == NULL_NODE
                            else tgt_class.replace("biolink:", "")
                        )
                        predicate = pred.replace("biolink:", "")

                        src_aspect_norm = (
                            None if not src_aspect
                            else src_aspect.replace("biolink:", "")
                        )
                        tgt_aspect_norm = (
                            None if not tgt_aspect
                            else tgt_aspect.replace("biolink:", "")
                        )

                        # Canonical deterministic key
                        template_key = "|".join(map(norm, [
                            src_cat,
                            predicate,
                            tgt_cat,
                            src_aspect_norm,
                            tgt_aspect_norm
                        ]))

                        template_id = hashlib.sha1(
                            template_key.encode("utf-8")
                        ).hexdigest()


                        templates.append({
                            
                            "template_id": f"{template_id}",
                            "src_cat": (
                                None if src_class == NULL_NODE
                                else src_class.replace("biolink:", "")
                            ),
                            "src_aspect": (
                                None if not src_aspect
                                else src_aspect.replace("biolink:", "")
                            ),
                            "predicate": pred.replace("biolink:", ""),
                            "tgt_cat": (
                                None if tgt_class == NULL_NODE
                                else tgt_class.replace("biolink:", "")
                            ),
                            "tgt_aspect": (
                                None if not tgt_aspect
                                else tgt_aspect.replace("biolink:", "")
                            ),
                        })

    return pd.DataFrame(templates).drop_duplicates()



def create_kgx_tsv(templates_df: pd.DataFrame, output_dir: str = 'biolink_templates_kgx'):
    """Create KGX-format TSV files"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Nodes
    nodes = []
    for _, row in templates_df.iterrows():
        nodes.extend([
            {'id': f"{row.src_cat}_{row.src_aspect}", 'name': row.src_cat, 'category': row.src_cat},
            {'id': f"{row.tgt_cat}_{row.tgt_aspect}", 'name': row.tgt_cat, 'category': row.tgt_cat}
        ])
    
    pd.DataFrame(nodes).drop_duplicates('id').to_csv(f'{output_dir}/nodes.tsv', sep='\t', index=False)
    
    # Edges
    edges = []
    for _, row in templates_df.iterrows():
        edges.append({
            'template_id': row.template_id,
            'subject': f"{row.src_cat}_{row.src_aspect}",
            'predicate': row.predicate,
            'object': f"{row.tgt_cat}_{row.tgt_aspect}"
        })
    
    pd.DataFrame(edges).to_csv(f'{output_dir}/edges.tsv', sep='\t', index=False)
    print(f"KGX TSVs: {output_dir}/")

def generate_yml_spec(templates_df: pd.DataFrame, version: str = '3.0.6') -> dict:
    """Generate YAML template specification"""
    template_groups = {}
    for _, row in templates_df.iterrows():
        src = f"{row['src_cat']}:{row['src_aspect']}"
        tgt = f"{row['tgt_cat']}:{row['tgt_aspect']}"
        if src not in template_groups:
            template_groups[src] = {}
        template_groups[src][tgt] = {
            'predicate': row['predicate'],
            'template_id': row['template_id']
        }
    
    return {
        'version': version,
        'biolink_model_version': version,
        'total_templates': len(templates_df),
        'templates': template_groups
    }

def main():
    print("Generating Biolink templates graph...")
    
    bmt = Toolkit()
    
    templates_df = generate_biolink_templates(bmt)
    templates_df.to_csv('biolink_templates.csv', index=False)
    
    create_kgx_tsv(templates_df)
    
    yml_spec = generate_yml_spec(templates_df)
    with open('biolink_templates.yml', 'w') as f:
        yaml.dump(yml_spec, f, sort_keys=False, indent=2, default_flow_style=False)
    
    print(f"""SUCCESS from Biolink:
   • {len(templates_df)} templates → biolink_templates.csv
   • KGX TSVs → biolink_templates_kgx/
   • YAML spec → biolink_templates.yml""")

if __name__ == "__main__":
    main()
