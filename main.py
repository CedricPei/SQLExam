import json
from Pipe import SQLEvaluationPipeline
from helper import execute_sql, write_result_to_file, run_with_timeout, compare_result
from tqdm import tqdm

model = "deepseek-chat"
partial = True

if __name__ == "__main__":
    with open("samples_20.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    # questions = [q for q in questions if q["question_id"] == 1481]

    Prover = Prover(model=model)
    Refuter = Refuter(model=model)
    PartialEval = SQLEvaluationPipeline(model=model)
    
    for question in tqdm(questions):
        pred_sql = question["predicted_sql"]
        db_id = question["db_id"]
        gold_sql = question["gold_sql"]


        pred_res = run_with_timeout(execute_sql, db_id, pred_sql, timeout=20)
        gold_res = run_with_timeout(execute_sql, db_id, gold_sql, timeout=20)

        score = 0.0
        if compare_result(pred_res, gold_res):
            score = 1.0 if not Refuter.call(question, pred_sql, gold_sql) else score
        elif Prover.call(question, pred_sql):
            score = 1.0 if not Refuter.call(question, pred_sql, gold_sql) else score

        if score != 1.0 and partial:
            score = PartialEval.eval(question, pred_sql)

        write_result_to_file(question, pred_sql, score)