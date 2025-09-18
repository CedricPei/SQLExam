import json
import os
import sys
import argparse
import numpy as np
from sklearn.metrics import cohen_kappa_score


def _resolve_method_dir(method_name: str) -> str:
	candidates = [
		os.path.join("output", method_name),
		os.path.join("output", method_name.upper()),
		os.path.join("output", method_name.lower()),
	]
	for path in candidates:
		if os.path.isdir(path):
			return path
	# default path even if not yet created
	return os.path.join("output", method_name)


def _load_eval_results(eval_dir: str) -> list:
	eval_file = os.path.join(eval_dir, "eval_results.json")
	if not os.path.exists(eval_file):
		raise FileNotFoundError(f"eval_results.json not found in {eval_dir}")
	with open(eval_file, 'r', encoding='utf-8') as f:
		return json.load(f)


def analyze_results_for_dir(eval_dir: str, mode: str, name: str = None, write_files: bool = True):
	data = _load_eval_results(eval_dir)
	name = name or os.path.basename(eval_dir)
	
	total_items = len(data)
	score_1_count = len([item for item in data if item.get("score") == 1.0])
	score_0_count = len([item for item in data if item.get("score") == 0.0])
	stats_dir = os.path.dirname(os.path.dirname(eval_dir)) or "output"
	os.makedirs(stats_dir, exist_ok=True)

	if mode == "l":
		has_label = any(item.get("label") in (True, False, "true", "false", "True", "False") for item in data)
		stats_file = os.path.join(stats_dir, f"{name}_statistics_by_label.json")

		if not has_label:
			raise ValueError("Label mode selected but no label found in eval_results.json")
		else:
			def is_true_label(item):
				label = item.get("label")
				return label is True or label == "true" or label == "True"
			
			def is_false_label(item):
				label = item.get("label")
				return label is False or label == "false" or label == "False"

			label_true_score_0 = [item for item in data if is_true_label(item) and item.get("score") == 0.0]
			label_false_score_1 = [item for item in data if is_false_label(item) and item.get("score") == 1.0]
			label_true_count = len([item for item in data if is_true_label(item)])
			label_false_count = len([item for item in data if is_false_label(item)])
			correct_predictions = len([item for item in data if 
									  (is_true_label(item) and item.get("score") == 1.0) or 
									  (is_false_label(item) and item.get("score") == 0.0)])
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
				"accuracy": round(accuracy, 4),
				"confusion_matrix": {
					"tp": tp,
					"tn": tn,
					"fp": fp,
					"fn": fn
				},
				"performance_metrics": {
					"precision": round(precision, 4),
					"recall": round(recall, 4),
					"f1_score": round(f1_score, 4),
					"mcc": round(mcc, 4),
					"cohen_kappa": round(kappa, 4)
				}
			}
			if write_files:
				with open(stats_file, 'w', encoding='utf-8') as f:
					json.dump(stats, f, ensure_ascii=False, indent=2)
			return stats

	def _simple_summary(items: list) -> dict:
		n = len(items)
		if n == 0:
			return {"count": 0, "score_rate": 0}
		score_rate = sum(1 for x in items if x.get("score") == 1.0) / n
		return {"count": n, "score_rate": round(score_rate, 4)}

	if mode == "d":
		buckets = {}
		for item in data:
			diff = item.get("difficulty", "unknown")
			buckets.setdefault(diff, []).append(item)
		by_diff = {diff: _simple_summary(items) for diff, items in buckets.items()}
		overall_rate = (score_1_count / total_items) if total_items else 0
		by_diff["overall"] = {"count": total_items, "score_rate": round(overall_rate, 4)}
		if write_files:
			by_diff_file = os.path.join(stats_dir, f"{name}_statistics_by_difficulty.json")
			with open(by_diff_file, 'w', encoding='utf-8') as f:
				json.dump(by_diff, f, ensure_ascii=False, indent=2)
		return by_diff


def analyze_method(method_dir: str, mode: str) -> dict:
	result = {}
	if not os.path.isdir(method_dir):
		return result
	variants = [d for d in os.listdir(method_dir) if os.path.isdir(os.path.join(method_dir, d))]
	for var in variants:
		eval_dir = os.path.join(method_dir, var)
		try:
			res = analyze_results_for_dir(eval_dir, mode, name=var, write_files=False)
			result[var] = res
		except Exception:
			continue
	return result


def analyze_results_all(mode: str):
	out_root = "output"
	results = {}
	if not os.path.isdir(out_root):
		print(json.dumps(results))
		return
	for method in os.listdir(out_root):
		method_dir = os.path.join(out_root, method)
		if not os.path.isdir(method_dir):
			continue
		results[method] = analyze_method(method_dir, mode)
	out_file = os.path.join(out_root, f"statistics_by_{'difficulty' if mode=='d' else 'label'}.json")
	with open(out_file, 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("mode", type=str, choices=["l", "d"], help="l: by label, d: by difficulty")
	parser.add_argument("method", nargs='?', type=str, default=None)
	args = parser.parse_args()
	if args.method:
		method_dir = _resolve_method_dir(args.method)
		res = analyze_method(method_dir, mode=args.mode)
		print(json.dumps(res, ensure_ascii=False, indent=2))
	else:
		analyze_results_all(mode=args.mode)
