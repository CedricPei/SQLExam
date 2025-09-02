import json
from Pipe import SQLEvaluationPipeline
from helper import execute_and_compare, write_result_to_file, run_with_timeout
from tqdm import tqdm

model = "deepseek-chat"
if __name__ == "__main__":
    with open("samples_20.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    # questions = [q for q in questions if q["question_id"] == 1481]

    for question in tqdm(questions):
        pred_sql = question["predicted_sql"]
        
        try:
            if run_with_timeout(execute_and_compare, question["db_id"], question["gold_sql"], pred_sql, timeout=20):
                exec_score = 1.0
            else:
                exec_score = 0
            sementic_score = SQLEvaluationPipeline(model=model).eval(question, pred_sql)
        except Exception:
            semantic_score, exec_score = 0, 0
        
        score = sementic_score * 0.8 + exec_score * 0.2
        write_result_to_file(question, pred_sql, semantic_score, exec_score, score) 