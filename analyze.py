import json
import os
import sys
import argparse
import numpy as np
from sklearn.metrics import cohen_kappa_score


def _load_eval_results(eval_dir: str) -> list:
	eval_file = os.path.join(eval_dir, "eval_results.json")
	if not os.path.exists(eval_file):
		raise FileNotFoundError(f"eval_results.json not found in {eval_dir}")
	with open(eval_file, 'r', encoding='utf-8') as f:
		return json.load(f)


def analyze_results_for_dir(eval_dir: str, mode: str, name: str = None, skip: bool = False):
	data = _load_eval_results(eval_dir)
	if skip and "test" in eval_dir:
		test_dir = eval_dir
		while not test_dir.endswith("test"):
			test_dir = os.path.dirname(test_dir)
		problem_file = os.path.join(test_dir, "problem_question_ids.json")
		if os.path.exists(problem_file):
			try:
				with open(problem_file, 'r', encoding='utf-8') as pf:
					problem_ids = set(str(x) for x in json.load(pf))
				data = [item for item in data if str(item.get("question_id")) not in problem_ids]
			except Exception:
				pass
	name = name or os.path.basename(eval_dir)
	
	total_items = len(data)
	score_1_count = len([item for item in data if item.get("score") == 1.0])
	score_0_count = len([item for item in data if item.get("score") == 0.0])
	stats_dir = os.path.dirname(os.path.dirname(eval_dir)) or "output"
	os.makedirs(stats_dir, exist_ok=True)

	if mode == "l":
		if not any(item.get("label") in (True, False, "true", "false") for item in data):
			return None
		
		tp = tn = fp = fn = 0
		labels = []
		scores = []
		
		for item in data:
			label = item.get("label")
			score = item.get("score")
			
			is_true_label = label in (True, "true")
			predicted_true = score == 1.0
			
			labels.append(1 if is_true_label else 0)
			scores.append(1 if predicted_true else 0)
			
			if is_true_label and predicted_true:
				tp += 1
			elif is_true_label and not predicted_true:
				fn += 1
			elif not is_true_label and predicted_true:
				fp += 1
			else:
				tn += 1
		
		accuracy = (tp + tn) / total_items if total_items > 0 else 0
		precision = tp / (tp + fp) if (tp + fp) > 0 else 0
		recall = tp / (tp + fn) if (tp + fn) > 0 else 0
		f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
		kappa = cohen_kappa_score(labels, scores) if labels else 0
		
		mcc_den = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
		mcc = ((tp * tn) - (fp * fn)) / (mcc_den ** 0.5) if mcc_den > 0 else 0
		
		return {
			"total_items": total_items,
			"confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
			"performance_metrics": {
				"accuracy": f"{accuracy * 100:.2f}%",
				"cohen_kappa": f"{kappa * 100:.2f}%",
				"mcc": f"{mcc * 100:.2f}%",
				"f1_score": f"{f1_score * 100:.2f}%"
			}
		}

	def _simple_summary(items: list) -> dict:
		n = len(items)
		if n == 0:
			return {"count": 0, "score_rate": "0.00%"}
		score_rate = sum(1 for x in items if x.get("score") == 1.0) / n
		return {"count": n, "score_rate": f"{score_rate * 100:.2f}%"}

	if mode == "d":
		buckets = {}
		any_difficulty = any("difficulty" in item for item in data)
		if not any_difficulty:
			return None
		for item in data:
			diff = item.get("difficulty", "unknown")
			buckets.setdefault(diff, []).append(item)
		by_diff = {diff: _simple_summary(items) for diff, items in buckets.items()}
		overall_rate = (score_1_count / total_items) if total_items else 0
		by_diff["overall"] = {"count": total_items, "score_rate": f"{overall_rate * 100:.2f}%"}
		return by_diff


def _load_eval_map(eval_file: str) -> dict:
	if not os.path.exists(eval_file):
		return {}
	with open(eval_file, 'r', encoding='utf-8') as f:
		items = json.load(f)
	return {int(x.get("question_id")): float(x.get("score", 0.0)) for x in items if "question_id" in x}


def _load_gold_false_ids(refuter_file: str) -> set:
	if not os.path.exists(refuter_file):
		return set()
	qids = set()
	with open(refuter_file, 'r', encoding='utf-8') as f:
		try:
			items = json.load(f)
			for x in items:
				qid = x.get("question_id")
				res = x.get("result", {}) if isinstance(x, dict) else {}
				gold = x.get("gold_correct") if "gold_correct" in x else res.get("gold_correct")
				if gold is False and qid is not None:
					qids.add(int(qid))
		except Exception:
			pass
	return qids


def _load_ambiguous_question_ids(refuter_file: str) -> set:
	if not os.path.exists(refuter_file):
		return set()
	qids = set()
	with open(refuter_file, 'r', encoding='utf-8') as f:
		try:
			items = json.load(f)
			for x in items:
				qid = x.get("question_id")
				res = x.get("result", {}) if isinstance(x, dict) else {}
				amb = x.get("ambiguity") if "ambiguity" in x else res.get("ambiguity")
				amb = str(amb or "").strip().lower()
				if amb == "ambiguous question" and qid is not None:
					qids.add(int(qid))
		except Exception:
			pass
	return qids




def analyze_quality_for_method(method_dir: str) -> dict:
	if not os.path.isdir(method_dir):
		return {}
	# locate EX and RA directories
	variants = [d for d in os.listdir(method_dir) if os.path.isdir(os.path.join(method_dir, d))]
	ex_dir = next((os.path.join(method_dir, d) for d in variants if d.startswith("EX-") and d.endswith("-eval")), None)
	ra_dir = next((os.path.join(method_dir, d) for d in variants if d.startswith("o3-") and d.endswith("-eval")), None)
	if not ex_dir or not ra_dir:
		return {}
	ex_eval = _load_eval_map(os.path.join(ex_dir, "eval_results.json"))
	ra_eval = _load_eval_map(os.path.join(ra_dir, "eval_results.json"))
	all_qids = set(ex_eval.keys()) | set(ra_eval.keys())
	# categories
	refuter_file = os.path.join(ra_dir, "refuter_output.json")
	gold_false_qids = _load_gold_false_ids(refuter_file)
	amb_qids = _load_ambiguous_question_ids(refuter_file) & all_qids
	def _discordant_count_within(qids: set) -> int:
		return sum(1 for qid in qids if (qid in ex_eval and qid in ra_eval and ex_eval[qid] != ra_eval[qid]))

	# total discordances across all questions
	overall_common = [qid for qid in all_qids if qid in ex_eval and qid in ra_eval]
	total_discordant = sum(1 for qid in overall_common if ex_eval[qid] != ra_eval[qid])

	# category counts
	gold_disc_cnt = _discordant_count_within(gold_false_qids)
	amb_disc_cnt = _discordant_count_within(amb_qids)
	gold_both = [qid for qid in gold_false_qids if qid in ex_eval and qid in ra_eval]
	amb_both = [qid for qid in amb_qids if qid in ex_eval and qid in ra_eval]
	# union (no double count)
	union_qids = set(gold_false_qids) | set(amb_qids)
	union_disc_cnt = _discordant_count_within(union_qids)
	union_both = [qid for qid in union_qids if qid in ex_eval and qid in ra_eval]

	# shares relative to total discordant across all questions
	gold_share = (gold_disc_cnt / total_discordant) if total_discordant else 0.0
	amb_share = (amb_disc_cnt / total_discordant) if total_discordant else 0.0
	union_share = (union_disc_cnt / total_discordant) if total_discordant else 0.0

	# discordant rate within category size
	gold_rate = (gold_disc_cnt / len(gold_both)) if gold_both else 0.0
	amb_rate = (amb_disc_cnt / len(amb_both)) if amb_both else 0.0
	union_rate = (union_disc_cnt / len(union_both)) if union_both else 0.0
	return {
		"GoldX": {"discordant_rate": f"{gold_rate * 100:.2f}%", "discordance_share": f"{gold_share * 100:.2f}%"},
		"AmbQ": {"discordant_rate": f"{amb_rate * 100:.2f}%", "discordance_share": f"{amb_share * 100:.2f}%"},
		"AmbQ+GoldX": {"discordant_rate": f"{union_rate * 100:.2f}%", "discordance_share": f"{union_share * 100:.2f}%"},
		"all": {"discordant_rate": f"{((total_discordant / len(overall_common)) if overall_common else 0.0) * 100:.2f}%"}
	}


def _has_nested_structure(method_dir: str) -> bool:
	subdirs = [d for d in os.listdir(method_dir) if os.path.isdir(os.path.join(method_dir, d))]
	if not subdirs:
		return False
	
	for subdir in subdirs:
		subdir_path = os.path.join(method_dir, subdir)
		variants = [d for d in os.listdir(subdir_path) if os.path.isdir(os.path.join(subdir_path, d))]
		if variants:
			for var in variants:
				eval_file = os.path.join(subdir_path, var, "eval_results.json")
				if os.path.exists(eval_file):
					return True
	return False


def analyze_method(method_dir: str, mode: str, skip: bool = False) -> dict:
	result = {}
	if not os.path.isdir(method_dir):
		return result
	
	if _has_nested_structure(method_dir):
		subdirs = [d for d in os.listdir(method_dir) if os.path.isdir(os.path.join(method_dir, d))]
		for subdir in subdirs:
			subdir_path = os.path.join(method_dir, subdir)
			variants = [d for d in os.listdir(subdir_path) if os.path.isdir(os.path.join(subdir_path, d))]
			subdir_result = {}
			for var in variants:
				eval_dir = os.path.join(subdir_path, var)
				try:
					res = analyze_results_for_dir(eval_dir, mode, name=var, skip=skip)
					subdir_result[var] = res
				except Exception:
					continue
			if subdir_result:
				result[subdir] = subdir_result
	else:
		variants = [d for d in os.listdir(method_dir) if os.path.isdir(os.path.join(method_dir, d))]
		for var in variants:
			eval_dir = os.path.join(method_dir, var)
			try:
				res = analyze_results_for_dir(eval_dir, mode, name=var, skip=skip)
				result[var] = res
			except Exception:
				continue
	return result


def analyze_results_all(mode: str, skip: bool = False):
	out_root = "output"
	results = {}
	if not os.path.isdir(out_root):
		print(json.dumps(results))
		return
	for method in os.listdir(out_root):
		method_dir = os.path.join(out_root, method)
		if not os.path.isdir(method_dir):
			continue
		results[method] = analyze_method(method_dir, mode, skip=skip)
	out_file = os.path.join(out_root, f"statistics_by_{'difficulty' if mode=='d' else 'label'}.json")
	with open(out_file, 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)


def analyze_quality_all():
	out_root = "output"
	results = {}
	if not os.path.isdir(out_root):
		print(json.dumps(results))
		return
	for method in os.listdir(out_root):
		if method == "test":
			continue
		method_dir = os.path.join(out_root, method)
		if not os.path.isdir(method_dir):
			continue
		res = analyze_quality_for_method(method_dir)
		if res:
			results[method] = res
	out_file = os.path.join(out_root, "statistics_by_type.json")
	with open(out_file, 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=str, choices=["l", "d", "t"], help="l: by label, d: by difficulty, t: type summary")
    parser.add_argument("method", nargs='?', type=str, default=None)
    parser.add_argument("--skip", action="store_true")
    args = parser.parse_args()
    if args.mode == "l":
        if args.method is not None:
            raise SystemExit("Label mode does not take a method argument. Use: python analyze.py l")
        method_dir = os.path.join("output", "test")
        res = analyze_method(method_dir, mode=args.mode, skip=args.skip)
        os.makedirs(method_dir, exist_ok=True)
        out_file = os.path.join(method_dir, "statistics_by_label.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    elif args.mode == "d":
        if args.method:
            method_dir = os.path.join("output", args.method)
            res = analyze_method(method_dir, mode=args.mode, skip=args.skip)
            os.makedirs(method_dir, exist_ok=True)
            out_file = os.path.join(method_dir, "statistics_by_difficulty.json")
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
        else:
            analyze_results_all(mode=args.mode, skip=args.skip)
    else:
        # t mode
        if args.method:
            method_dir = os.path.join("output", args.method)
            res = analyze_quality_for_method(method_dir)
            os.makedirs(method_dir, exist_ok=True)
            out_file = os.path.join(method_dir, "statistics_by_type.json")
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
        else:
            analyze_quality_all()
