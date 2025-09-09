import json
import os
from Pipe import SQLEvaluationPipeline
from helper import execute_sql, write_result_to_file, run_with_timeout, compare_result
from tqdm import tqdm
from Prover import Prover
from Refuter import Refuter

# "deepseek-r1-distill-qwen-32b"

reasoning_model = "o3"
instruct_model = "deepseek-chat"
partial = False

output_dir = f"output/{reasoning_model}"
os.makedirs(output_dir, exist_ok=True)

Prover = Prover(model=reasoning_model, output_dir=output_dir)
Refuter = Refuter(model=reasoning_model, output_dir=output_dir)
PartialEval = SQLEvaluationPipeline(model=instruct_model)

if __name__ == "__main__":
    with open("test.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    # questions = [q for q in questions if int(q["question_id"]) in {1501}]
    problem_ids = []
    
    for question in tqdm(questions):
        pred_sql = question["predicted_sql"]
        db_id = question["db_id"]
        gold_sql = question["gold_sql"]

        pred_res = run_with_timeout(execute_sql, db_id, pred_sql, timeout=45)
        gold_res = run_with_timeout(execute_sql, db_id, gold_sql, timeout=45)

        score = 0.0
        refuter_verdict = None
        prover_verdict = None

        if not isinstance(pred_res, bool) and not isinstance(gold_res, bool):
            if compare_result(pred_res, gold_res):
                refuter_verdict = Refuter.call(question, pred_sql)
                score = 1.0 if not refuter_verdict else 0.0
            elif pred_res is not None:
                prover_verdict, prover_reason = Prover.call(question, pred_sql, pred_res)
                if prover_verdict:
                    refuter_verdict = Refuter.call(question, pred_sql, pred_res, gold_res, prover_reason)
                    score = 1.0 if not refuter_verdict else 0.0

            if score != 1.0 and partial:
                score = PartialEval.eval(question, pred_sql)
        else:
            problem_ids.append(question.get("question_id"))
            continue
        write_result_to_file(question, pred_sql, score, prover_verdict, refuter_verdict, output_dir)

    with open(os.path.join(output_dir, "problem_question_ids.json"), "w", encoding="utf-8") as f:
        json.dump(problem_ids, f, ensure_ascii=False, indent=2)