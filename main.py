import json
from constraint_extractor import ConstraintExtractor
from rubric_designer import RubricDesigner
from rubric_grader import RubricGrader
from rule_checker import RuleChecker
from utils import execute_and_compare, get_ddl, get_schema
from tqdm import tqdm
import sqlparse
import os

def calculate_usefulness_score(grading_results, rubric_questions):
    total_score = sum(float(r["score"]) for r in grading_results)
    total_weight = sum(float(q["weight"]) for q in rubric_questions)
    return round(total_score / total_weight, 4) if total_weight > 0 else 0.0

def write_result_to_file(question_obj, predicted_sql, usefulness_score, output_file="usefulness_results.json"):
    result = {"question_id": question_obj["question_id"], "question": question_obj["question"], "predicted_sql": predicted_sql, "usefulness": usefulness_score}
    
    existing_results = json.load(open(output_file, encoding="utf-8")) if os.path.exists(output_file) else []
    existing_results.append(result)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_results, f, ensure_ascii=False, indent=2)

model = "deepseek-chat"
if __name__ == "__main__":
    with open("extracted_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    # questions = [q for q in questions if q["question_id"] == 671]

    for q in tqdm(questions):
        pred_sql = q["SQL"]
        question_obj = {
            "question_id": str(q["question_id"]),
            "question": q["question"],
            "evidence": q["evidence"],
        }

        if execute_and_compare(q["db_id"], q["SQL"], pred_sql):
            schema_dict = get_schema(q["db_id"])
            if RuleChecker(schema_dict).sqlglot_equivalent(q["SQL"], pred_sql):
                usefulness_score = 1.0
            else:
                usefulness_score = 0.0
        else:
            question_obj["gold_sql"] = sqlparse.format(q["SQL"], reindent=True, keyword_case='upper')
            question_obj["schema"] = get_ddl(q["db_id"])

            # Constraint Extractor
            constraint_extractor = ConstraintExtractor(question_obj, model=model)
            constraints = constraint_extractor.call()

            # Rubric Designer
            rubric_designer = RubricDesigner(question_obj, constraints, model=model)
            designed_rubric = rubric_designer.call()

            # Rubric Grader
            rubric_grader = RubricGrader(question_obj, designed_rubric, model=model)
            grading_results = rubric_grader.call(pred_sql)

            usefulness_score = calculate_usefulness_score(grading_results, designed_rubric)
        
        # Write score to file
        write_result_to_file(question_obj, pred_sql, usefulness_score)