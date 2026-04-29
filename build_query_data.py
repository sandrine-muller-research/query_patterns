import sqlite3
import hashlib
import requests
import csv

from translatorutils.dataExtraction.TranslatorExtract import get_KG_table, add_table_from_dict, get_trapi_message

# CONFIG
DB_FILE = "ars_query_usage.db"
INSTANCE = ["test"]
BATCH_SIZE = 30
pk_location = 'data/pk_list.csv'

# KGX log columns
KGX_COLUMNS = [
    "query_pk",
    "timestamp",
    "input_category",
    "input_aspect",
    "predicate_value",
    "output_aspect",
    "output_category",
    "template_id"
]

def generate_template_id(subject, predicate, object_):
    """Create a reproducible template ID using SHA1"""
    raw = f"{subject}|{predicate}|{object_}".encode()
    return hashlib.sha1(raw).hexdigest()[:16]

def process_pk_to_rows(pk):
    """
    Convert a PK into a list of dicts for SQLite insertion.
    """
    rows = []
    KG_table = get_KG_table(pk, INSTANCE)
    
    # Get timestamp from TRAPI message
    trapi_msg = get_trapi_message(pk, INSTANCE)
    timestamp = trapi_msg.get("fields", {}).get("timestamp", None)

    for row in KG_table[1:]:  # skip header
        _, subject, subject_name, subject_cat, object_, object_name, object_cat, predicate = row
        rows.append({
            "query_pk": pk,
            "timestamp": timestamp,
            "input_category": subject_cat,
            "input_aspect": subject_name,
            "predicate_value": predicate,
            "output_aspect": object_name,
            "output_category": object_cat
        })
    return rows

def main():
    pk_list = []
    with open(pk_location, 'r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
    
        # Read data rows
        for row in csv_reader:
            pk_list.append(row[0])
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_FILE)
    print(f"Using database: {DB_FILE}")

    for i in range(0, len(pk_list), BATCH_SIZE):
        batch_pks = pk_list[i:i+BATCH_SIZE]
        for pk in batch_pks:
            try:
                rows = process_pk_to_rows(pk)
                for row in rows:
                    # Insert into DB using TranslatorUtils helper
                    add_table_from_dict(row, "query_template_logs", conn)
            except Exception as e:
                print(f"Error processing PK {pk}: {e}")

    conn.close()
    print("Database creation completed.")

if __name__ == "__main__":
    main()
