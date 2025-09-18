import json
import os
import argparse
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from evaluators.PartialGrader import PartialScoringPipeline
from evaluators.utils import execute_sql, write_result_to_file, run_with_timeout, compare_result
from tqdm import tqdm
from evaluators.Prover import Prover
from evaluators.Refuter import Refuter

 

def _process_question(question):
    pred_sql = question["predicted_sql"]
    db_id = question["db_id"]
    gold_sql = question["gold_sql"]

    pred_res = run_with_timeout(execute_sql, db_id, pred_sql, timeout=45)
    gold_res = run_with_timeout(execute_sql, db_id, gold_sql, timeout=45)

    score = 0.0
    refuter_verdict = None
    prover_verdict = None
    qid = str(question.get("question_id"))

    if pred_res is None or gold_res is None:
        return qid
    if pred_res is False:
        score = 0.0
        write_result_to_file(question, pred_sql, score, prover_verdict, refuter_verdict, output_dir)
        return None

    if compare_result(pred_res, gold_res):
        refuter_verdict = Refuter.call(question, pred_sql)
        if refuter_verdict is None:
            return qid
        score = 1.0 if not refuter_verdict else 0.0
    elif pred_res is not None:
        prover_verdict, prover_reason = Prover.call(question, pred_sql, pred_res)
        if prover_verdict is None:
            return qid
        if prover_verdict:
            refuter_verdict = Refuter.call(question, pred_sql, pred_res, gold_res, prover_reason)
            if refuter_verdict is None:
                return qid
            score = 1.0 if not refuter_verdict else 0.0

        if score != 1.0 and partial:
            score = PartialEval.eval(question, pred_sql)

    write_result_to_file(question, pred_sql, score, prover_verdict, refuter_verdict, output_dir)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--input", type=str, default="sample.json")
    args = parser.parse_args()
    reasoning_model = "o3"
    instruct_model = "deepseek-chat"
    partial = False

    input_stem = re.sub(r"(-result)$", "", os.path.splitext(os.path.basename(args.input))[0])
    output_dir = f"output/{input_stem}/{reasoning_model}-{input_stem}-eval"
    os.makedirs(output_dir, exist_ok=True)

    Prover = Prover(model=reasoning_model, output_dir=output_dir)
    Refuter = Refuter(model=reasoning_model, output_dir=output_dir)
    PartialEval = PartialScoringPipeline(model=instruct_model)

    problem_ids: List[str] = []
    num_threads = max(1, int(args.threads))
    method_root_dir = os.path.join("output", input_stem)
    problems_file_path = os.path.join(method_root_dir, "problem_question_ids.json")
    existing_results_path = os.path.join(output_dir, "eval_results.json")

    with open(args.input, "r", encoding="utf-8") as f:
        questions = json.load(f)

    existing_ids = set()
    if os.path.exists(existing_results_path):
        try:
            with open(existing_results_path, "r", encoding="utf-8") as ef:
                existing_data = json.load(ef)
                for item in existing_data:
                    qid = str(item.get("question_id"))
                    if qid:
                        existing_ids.add(qid)
        except Exception:
            existing_ids = set()

    total_input = len(questions)
    questions = [q for q in questions if str(q.get("question_id")) not in existing_ids]
    to_process = len(questions)
    print(f"Input total: {total_input}, To process: {to_process}")

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

    if len(problem_ids) > 0:
        os.makedirs(method_root_dir, exist_ok=True)
        with open(problems_file_path, "w", encoding="utf-8") as f:
            json.dump(problem_ids, f, ensure_ascii=False, indent=2)