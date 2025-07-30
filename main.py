import json
from constraint_extractor import ConstraintExtractor
from rubric_designer import RubricDesigner
from reviewer import Reviewer
from utils import get_schema_by_db_id
from tqdm import tqdm
import sqlparse

if __name__ == "__main__":
    with open("extracted_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    questions = [q for q in questions if q["question_id"] == 930]

    for q in tqdm(questions):
        schema = get_schema_by_db_id(q["db_id"])
        gold_sql = sqlparse.format(q["SQL"], reindent=True, keyword_case='upper')
        question_obj = {
            "question_id": str(q["question_id"]),
            "db_id": q["db_id"],
            "question": q["question"],
            "evidence": q["evidence"],
            "gold_sql": gold_sql,
            "schema": schema
        }

        constraint_extractor = ConstraintExtractor(question_obj)
        constraints = constraint_extractor.call()

        rubric_designer = RubricDesigner(question_obj, constraints)
        designed_rubric = rubric_designer.call()

        # reviewer = Reviewer(question_obj, constraints)
        # revised_constraints = reviewer.call()
