import pandas as pd
import yaml
from pathlib import Path

def generate_biolink_templates():
    templates = []
    template_counter = 0
    
    # Demo data (replace with full BMT extraction)
    demo_templates = [
        {'template_id': 't001', 'src_cat': 'chemical_substance', 'src_aspect': 'chemical_substance', 
         'predicate': 'treats', 'tgt_cat': 'disease', 'tgt_aspect': 'disease'},
        {'template_id': 't002', 'src_cat': 'gene', 'src_aspect': 'gene', 
         'predicate': 'encodes', 'tgt_cat': 'protein', 'tgt_aspect': 'protein'},
        {'template_id': 't003', 'src_cat': 'disease', 'src_aspect': 'disease', 
         'predicate': 'caused_by', 'tgt_cat': 'chemical_substance', 'tgt_aspect': 'chemical_substance'},
    ]
    
    df = pd.DataFrame(demo_templates)
    df.to_csv('biolink_templates.csv', index=False)
    
    # YAML spec
    yml_data = {
        'version': '3.0.6',
        'total_templates': len(df),
        'templates': {f"{row.src_cat}_{row.src_aspect}": {
            f"{row.tgt_cat}_{row.tgt_aspect}": {
                'predicate': row.predicate,
                'template_id': row.template_id
            }
        } for _, row in df.iterrows()}
    }
    with open('biolink_templates.yml', 'w') as f:
        yaml.dump(yml_data, f, indent=2)
    
    print("✅ Generated: biolink_templates.csv + biolink_templates.yml")
    return df

templates_df = generate_biolink_templates()
templates_df.head()