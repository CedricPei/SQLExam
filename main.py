import json
from observer import Observer
from utils import get_schema_by_db_id
from tqdm import tqdm

if __name__ == "__main__":
    with open("mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    for q in tqdm(questions):
        question_id = str(q["question_id"])
        db_id = q["db_id"]
        question = q["question"]
        evidence = q["evidence"]
        gold_sql = q["SQL"]

        schema = get_schema_by_db_id(db_id)
        obs = Observer(schema, question_id, question, evidence, gold_sql)
        obs.call()
