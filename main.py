import json
from SQLGlotEval import SQLGlotEval
from VeriEQL import VeriEQL
from Pipe import SQLEvaluationPipeline
from helper import execute_and_compare, write_result_to_file
from tqdm import tqdm

model = "deepseek-chat"
if __name__ == "__main__":
    with open("extracted_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    # questions = [q for q in questions if q["question_id"] == 671]

    for question in tqdm(questions):
        pred_sql = question["SQL"]

        if not VeriEQL(question["SQL"], pred_sql, question["db_id"]):
            usefulness_score = 0.0
            # try:
            #     if execute_and_compare(question["db_id"], question["SQL"], pred_sql):
            #         if SQLGlotEval(question["db_id"], question["SQL"], pred_sql):
            #             usefulness_score = 1.0
            #         else:
            #             usefulness_score = 0.0
            #     else:
            #         usefulness_score = SQLEvaluationPipeline(model=model).eval(question, pred_sql)
            # except Exception as e:
            #     usefulness_score = 0.0        
        else:
            usefulness_score = 1.0
        
        write_result_to_file(question, pred_sql, usefulness_score)