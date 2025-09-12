import json
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from evaluators.PartialGrader import PartialScoringPipeline
from evaluators.utils import execute_sql, write_result_to_file, run_with_timeout, compare_result
from tqdm import tqdm
from evaluators.Prover import Prover
from evaluators.Refuter import Refuter

reasoning_model = "o3"
instruct_model = "deepseek-chat"
partial = False

output_dir = f"output/{reasoning_model}"
os.makedirs(output_dir, exist_ok=True)

Prover = Prover(model=reasoning_model, output_dir=output_dir)
Refuter = Refuter(model=reasoning_model, output_dir=output_dir)
PartialEval = PartialScoringPipeline(model=instruct_model)

def _process_question(question):
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
        qid = question.get("question_id")
        return str(qid)

    write_result_to_file(question, pred_sql, score, prover_verdict, refuter_verdict, output_dir)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-threads", type=int, default=1)
    parser.add_argument("--input", type=str, default="sample.json")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        questions = json.load(f)

    problem_ids: List[str] = []
    num_threads = max(1, int(args.num_threads))

    def worker(idx):
        local_problems = []
        slice_questions = questions[idx::num_threads]
        bar = tqdm(total=len(slice_questions), position=idx, leave=False, desc=f"T{idx}")
        for q in slice_questions:
            pid = _process_question(q)
            if pid:
                local_problems.append(pid)
            bar.update(1)
        bar.close()
        return local_problems

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for f in futures:
            problem_ids.extend(f.result())

    with open(os.path.join(output_dir, "problem_question_ids.json"), "w", encoding="utf-8") as f:
        json.dump(problem_ids, f, ensure_ascii=False, indent=2)