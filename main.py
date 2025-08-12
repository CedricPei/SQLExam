import json
import os, sys, zipfile, shutil
from Pipe import SQLEvaluationPipeline
from RandomDBEval import RandomDBEval
from helper import execute_and_compare, write_result_to_file, run_with_timeout
from tqdm import tqdm
from ETM import ETM

model = "deepseek-chat"
if __name__ == "__main__":
    with open("samples_500.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    # questions = [q for q in questions if q["question_id"] == 671]

    for question in tqdm(questions):
        pred_sql = question["predicted_sql"]
        etm = run_with_timeout(ETM, question, pred_sql, timeout=5)
        
        if etm:
            eval_path = "ETM"
            usefulness_score = 1.0
        else:
            try:
                if execute_and_compare(question["db_id"], question["gold_sql"], pred_sql):
                    eval_path = "RandomDBEval"
                    usefulness_score = RandomDBEval(question, pred_sql)
                else:
                    eval_path = "SQLEvaluationPipeline"
                    usefulness_score = SQLEvaluationPipeline(model=model).eval(question, pred_sql)
            except Exception:
                eval_path = "Exception"
                usefulness_score = 0.0
            # eval_path = "Exception"
            # usefulness_score = 0.0
        
        write_result_to_file(question, pred_sql, usefulness_score, eval_path) 