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
	if skip:
		method_dir = os.path.dirname(eval_dir)
		problem_file = os.path.join(method_dir, "problem_question_ids.json")
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
		has_label = any(item.get("label") in (True, False, "true", "false") for item in data)
		if not has_label:
			return None
		def is_true_label(item):
			return item.get("label") in (True, "true")
		def is_false_label(item):
			return item.get("label") in (False, "false")
		if total_items == 0:
			accuracy = 0
			tp = tn = fp = fn = 0
			precision = recall = f1_score = mcc = kappa = 0
		else:
			label_true_score_0 = [item for item in data if is_true_label(item) and item.get("score") == 0.0]
			label_false_score_1 = [item for item in data if is_false_label(item) and item.get("score") == 1.0]
			correct_predictions = len([item for item in data if (is_true_label(item) and item.get("score") == 1.0) or (is_false_label(item) and item.get("score") == 0.0)])
			accuracy = correct_predictions / total_items if total_items > 0 else 0
			labels = [1 if is_true_label(item) else 0 for item in data]
			scores = [1 if item.get("score") == 1.0 else 0 for item in data]
			kappa = cohen_kappa_score(labels, scores) if len(labels) > 0 else 0
			tp = len([item for item in data if is_true_label(item) and item.get("score") == 1.0])
			tn = len([item for item in data if is_false_label(item) and item.get("score") == 0.0])
			fp = len(label_false_score_1)
			fn = len(label_true_score_0)
			precision = tp / (tp + fp) if (tp + fp) > 0 else 0
			recall = tp / (tp + fn) if (tp + fn) > 0 else 0
			f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
			mcc_den = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
			if mcc_den > 0:
				mcc = ((tp * tn) - (fp * fn)) / (mcc_den ** 0.5)
			else:
				mcc = 0
		stats = {
			"total_items": total_items,
			"confusion_matrix": {
				"tp": tp,
				"tn": tn,
				"fp": fp,
				"fn": fn
			},
			"performance_metrics": {
				"accuracy": f"{accuracy * 100:.2f}%",
				"cohen_kappa": f"{kappa * 100:.2f}%",
				"mcc": f"{mcc * 100:.2f}%",
				"f1_score": f"{f1_score * 100:.2f}%"
			}
			}
		return stats

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


def analyze_method(method_dir: str, mode: str, skip: bool = False) -> dict:
	result = {}
	if not os.path.isdir(method_dir):
		return result
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


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("mode", type=str, choices=["l", "d"], help="l: by label, d: by difficulty")
	parser.add_argument("method", nargs='?', type=str, default=None)
	parser.add_argument("--skip", action="store_true")
	args = parser.parse_args()
	if args.method:
		method_dir = os.path.join("output", args.method)
		res = analyze_method(method_dir, mode=args.mode, skip=args.skip)
		os.makedirs(method_dir, exist_ok=True)
		out_file = os.path.join(method_dir, f"statistics_by_{'difficulty' if args.mode=='d' else 'label'}.json")
		with open(out_file, 'w', encoding='utf-8') as f:
			json.dump(res, f, ensure_ascii=False, indent=2)
	else:
		analyze_results_all(mode=args.mode, skip=args.skip)
