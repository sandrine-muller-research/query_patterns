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

BLOCKLIST = [
    # Abstract roots (not instantiable)
    'biolink:Entity',
    'biolink:Annotation',
    
    # Mixins (behavioral, not data entities)
    'biolink:macromolecular_machine_mixin',
    'biolink:genomic_entity_mixin',
    'biolink:physical_entity_mixin',
    'biolink:information_content_entity',
    'biolink:association_mixin',
    
    # Deprecated/legacy classes (check ChangeLog)
    'biolink:behavior',  # Often deprecated variants
    'biolink:conceptual_entity',
    
    # Pure utilities (no direct data instances)
    'biolink:association_slot',
    'biolink:node_category',
    
    # Overly generic or meta
    'biolink:thing_with_taxonomic_origin',
    'biolink:occurrence'
]

def get_filtered_classes(bmt=None, debug=False):
    if bmt is None:
        bmt = Toolkit()
    
    classes = {}
    
    namedthing_descendants_formatted = set(bmt.get_descendants('named thing', True))
    namedthing_descendants_unformatted = set(bmt.get_descendants('named thing', False))
    all_classes = bmt.get_all_classes()
    
    for name in all_classes:
        try:
            elem = bmt.get_element(name)
            
            # 1. Deprecated
            is_deprecated = getattr(elem, 'deprecated', False)
            
            # 2. NamedThing descendant
            is_namedthing_descendant = (
                name in namedthing_descendants_unformatted or
                name in namedthing_descendants_formatted
            )
            
            # 3. Safe mixin check
            mixins = getattr(elem, 'mixins', [])
            has_mixins = any('mixin' in str(mixin).lower() for mixin in mixins)
            
            # 4. FIXED: Use real BMT method for inherited slots
            try:
                all_slots_for_class = bmt.get_all_slots_with_class_domain(name, check_ancestors=True)
                has_slots = len(all_slots_for_class) > 0
            except:
                has_slots = len(getattr(elem, 'slots', [])) > 0  # Fallback
            
            # 5. Abstract
            is_abstract = getattr(elem, 'abstract', False)
            
            if debug:
                print('*********')
                print(name)
                print(f"  dep={is_deprecated}, namedthing={is_namedthing_descendant}, "
                      f"mixin={has_mixins}, slots={has_slots}, abstract={is_abstract}")
            
            # Essential biomedical classes pass even with minimal slots
            if (not is_deprecated 
                and not is_abstract
                and is_namedthing_descendant 
                and (has_slots or name in ['transcript', 'protein', 'polypeptide', 
                                          'coding sequence', 'snv', 'gene', 'mrna'])):
                
                classes[name] = elem
                if debug:
                    print(f"  ✓ KEPT")
            else:
                if debug:
                    print(f"  ✗ SKIPPED")
                    
        except Exception as e:
            if debug:
                print(f"{name}: ERROR {e}")
    
    if debug:
        print(f"\nFinal count: {len(classes)} classes")
    
    return classes


def generate_biolink_templates(
    bmt: Toolkit,
    version: str | None = None
) -> pd.DataFrame:
    """
    Generate all possible Biolink templates:
      - Class → Predicate → Class
      - with optional subject/object aspects (qualifiers)
      - including NULL source/target nodes
      - returns both CURIE and unprefixed variants
    """

    classes = get_filtered_classes(bmt, True)
    predicates = [e for e in bmt.get_all_elements() if bmt.is_predicate(e)]

    templates = []

    def norm(x: str | None) -> str:
        return "NULL" if x is None else x.strip().lower()

    for src_class in list(classes.keys()) + [NULL_NODE]:
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

                        # CURIE forms (may be NULL_NODE)
                        src_cat_curie = None if src_class == NULL_NODE else src_class
                        tgt_cat_curie = None if tgt_class == NULL_NODE else tgt_class
                        predicate_curie = pred

                        src_aspect_curie = (
                            None if not src_aspect else src_aspect
                        )
                        tgt_aspect_curie = (
                            None if not tgt_aspect else tgt_aspect
                        )

                        # Unprefixed forms (strip 'biolink:')
                        def strip_bl(x):
                            if not x:
                                return None
                            return x.replace("biolink:", "")

                        src_cat = strip_bl(src_cat_curie)
                        tgt_cat = strip_bl(tgt_cat_curie)
                        predicate = strip_bl(predicate_curie)
                        src_aspect_norm = strip_bl(src_aspect_curie)
                        tgt_aspect_norm = strip_bl(tgt_aspect_curie)

                        # Canonical deterministic key (unprefixed)
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

                            # Unprefixed
                            "src_cat": src_cat,
                            "src_aspect": src_aspect_norm,
                            "predicate": predicate,
                            "tgt_cat": tgt_cat,
                            "tgt_aspect": tgt_aspect_norm,

                            # CURIE versions
                            "src_cat_curie": src_cat_curie,
                            "src_aspect_curie": src_aspect_curie,
                            "predicate_curie": predicate_curie,
                            "tgt_cat_curie": tgt_cat_curie,
                            "tgt_aspect_curie": tgt_aspect_curie,
                        })

    return pd.DataFrame(templates).drop_duplicates()


def create_kgx_tsv(templates_df: pd.DataFrame, output_dir: str = 'data/biolink_templates_kgx'):
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
    templates_df.to_csv('data/biolink_templates.csv', index=False)
    
    create_kgx_tsv(templates_df)
    
    yml_spec = generate_yml_spec(templates_df)
    with open('data/biolink_templates.yml', 'w') as f:
        yaml.dump(yml_spec, f, sort_keys=False, indent=2, default_flow_style=False)
    
    print(f"""SUCCESS from Biolink:
   • {len(templates_df)} templates → biolink_templates.csv
   • KGX TSVs → biolink_templates_kgx/
   • YAML spec → biolink_templates.yml""")

if __name__ == "__main__":
    main()
