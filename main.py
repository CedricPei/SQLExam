import json
from observer import Observer
from reviewer import Reviewer
from utils import get_schema_by_db_id
from tqdm import tqdm

if __name__ == "__main__":
    with open("mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    for q in tqdm(questions):
        schema = get_schema_by_db_id(q["db_id"])
        question_obj = {
            "question_id": str(q["question_id"]),
            "db_id": q["db_id"],
            "question": q["question"],
            "evidence": q["evidence"],
            "gold_sql": q["SQL"],
            "schema": schema
        }

        obs = Observer(question_obj)
        constraints = obs.call()

        reviewer = Reviewer(question_obj, constraints)
        rubric = reviewer.call()
