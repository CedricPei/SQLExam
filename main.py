import json
import os
from Pipe import SQLEvaluationPipeline
from helper import execute_sql, write_result_to_file, run_with_timeout, compare_result
from tqdm import tqdm
from Prover import Prover
from Refuter import Refuter

# "deepseek-r1-distill-qwen-32b"

reasoning_model = "deepseek-r1-distill-qwen-32b"
instruct_model = "deepseek-chat"
partial = False

output_dir = f"output/{reasoning_model}"
os.makedirs(output_dir, exist_ok=True)

Prover = Prover(model=reasoning_model, output_dir=output_dir)
Refuter = Refuter(model=reasoning_model, output_dir=output_dir)
PartialEval = SQLEvaluationPipeline(model=instruct_model)

if __name__ == "__main__":
    with open("samples_20.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    for question in tqdm(questions):
        pred_sql = question["predicted_sql"]
        db_id = question["db_id"]
        gold_sql = question["gold_sql"]

        pred_res = run_with_timeout(execute_sql, db_id, pred_sql, timeout=20)
        gold_res = run_with_timeout(execute_sql, db_id, gold_sql, timeout=20)

        score = 0.0
        refuter_res = None
        prover_res = None

        if not isinstance(pred_res, bool) and not isinstance(gold_res, bool):
            if compare_result(pred_res, gold_res):
                refuter_res = Refuter.call(question, pred_sql)
                score = 1.0 if not refuter_res else 0.0
            elif pred_res is not None:
                prover_res = Prover.call(question, pred_sql, pred_res)
                if prover_res:
                    refuter_res = Refuter.call(question, pred_sql, pred_res, gold_res)
                    score = 1.0 if not refuter_res else 0.0

            if score != 1.0 and partial:
                score = PartialEval.eval(question, pred_sql)

        write_result_to_file(question, pred_sql, score, prover_res, refuter_res, output_dir)