import os
import sys
import json
import argparse
import re
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluators.utils import execute_sql, write_result_to_file, run_with_timeout
from evaluators.Prover import Prover


def _process_question(question, prover, output_dir):
    pred_sql = question["predicted_sql"]
    db_id = question["db_id"]
    pred_res = run_with_timeout(execute_sql, db_id, pred_sql, timeout=60)
    score = 0.0
    prover_verdict = None

    if pred_res is None:
        return 
    if pred_res is False:
        score = 0.0
        write_result_to_file(question, pred_sql, score, prover_verdict, None, output_dir)
        return 
    prover_verdict, _ = prover.call(question, pred_sql, pred_res)
    if prover_verdict is None:
        return 
    score = 1.0 if prover_verdict else 0.0
    write_result_to_file(question, pred_sql, score, prover_verdict, None, output_dir)
    return 

def main():
    parser = argparse.ArgumentParser(description="Prover Only ablation experiment")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads")
    parser.add_argument("--input", type=str, default="sample.json", help="Input file path")
    args = parser.parse_args()
    reasoning_model = "gemini-2.5-pro-thinking"

    input_stem = re.sub(r"(-result)$", "", os.path.splitext(os.path.basename(args.input))[0])
    output_dir = f"output/{input_stem}/{reasoning_model}-ProverOnly-{input_stem}-eval"
    os.makedirs(output_dir, exist_ok=True)

    prover = Prover(model=reasoning_model, output_dir=output_dir)

    num_threads = max(1, int(args.threads))
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

    progress = tqdm(total=to_process, dynamic_ncols=True, mininterval=0.5)

    def worker(idx):
        slice_questions = questions[idx::num_threads]
        for q in slice_questions:
            _process_question(q, prover, output_dir)
            progress.update(1)
        return []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for f in futures:
            f.result()

    progress.close()


if __name__ == "__main__":
    main()
