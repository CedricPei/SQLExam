import json
from constraint_extractor import ConstraintExtractor
from rubric_designer import RubricDesigner
from rubric_grader import RubricGrader
from reviewer import Reviewer
from utils import get_schema_by_db_id
from tqdm import tqdm
import sqlparse
import os

def calculate_usefulness_score(grading_results, rubric_questions):
    total_score = sum(float(r["score"]) for r in grading_results)
    total_weight = sum(float(q["weight"]) for q in rubric_questions)
    return round(total_score / total_weight, 4) if total_weight > 0 else 0.0

def write_result_to_file(question_obj, predicted_sql, usefulness_score, output_file="usefulness_results.json"):
    result = {"question_id": question_obj["question_id"], "question": question_obj["question"], "predicted_sql": predicted_sql, "usefulness": usefulness_score}
    
    existing_results = json.load(open(output_file)) if os.path.exists(output_file) else []
    existing_results.append(result)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    with open("extracted_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    # questions = [q for q in questions if q["question_id"] == 726]

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

        rubric_grader = RubricGrader(question_obj, designed_rubric)
        grading_results = rubric_grader.call(q["SQL"])
        
        usefulness_score = calculate_usefulness_score(grading_results, designed_rubric)
        write_result_to_file(question_obj, q["SQL"], usefulness_score)



