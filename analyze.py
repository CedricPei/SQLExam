import json
import os
import sys
import argparse
import numpy as np
from sklearn.metrics import cohen_kappa_score

def _resolve_model_dir(model_name: str) -> str:
    candidates = [
        os.path.join("output", model_name),
        os.path.join("output", model_name.upper()),
        os.path.join("output", model_name.lower()),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[0]


def _load_eval_results(model_dir: str) -> list:
    eval_file = os.path.join(model_dir, "eval_results.json")
    if not os.path.exists(eval_file):
        raise FileNotFoundError(f"eval_results.json not found in {model_dir}")
    with open(eval_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_results_for_dir(model_dir: str, mode: str, model_name: str | None = None, write_files: bool = True):
    data = _load_eval_results(model_dir)
    model_name = model_name or os.path.basename(model_dir)
    
    total_items = len(data)
    score_1_count = len([item for item in data if item.get("score") == 1.0])
    score_0_count = len([item for item in data if item.get("score") == 0.0])
    stats_dir = "output"
    os.makedirs(stats_dir, exist_ok=True)

    if mode == "l":
        has_label = any(item.get("label") in (True, False, "true", "false", "True", "False") for item in data)
        stats_file = os.path.join(stats_dir, f"{model_name}_statistics_by_label.json")

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
                "accuracy": accuracy,
                "confusion_matrix": {
                    "tp": tp,
                    "tn": tn,
                    "fp": fp,
                    "fn": fn
                },
                "performance_metrics": {
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score,
                    "mcc": mcc,
                    "cohen_kappa": kappa
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
        return {"count": n, "score_rate": score_rate}

    if mode == "d":
        buckets = {}
        for item in data:
            diff = item.get("difficulty", "unknown")
            buckets.setdefault(diff, []).append(item)
        by_diff = {diff: _simple_summary(items) for diff, items in buckets.items()}
        overall_rate = (score_1_count / total_items) if total_items else 0
        by_diff["overall"] = {"count": total_items, "score_rate": overall_rate}
        if write_files:
            by_diff_file = os.path.join(stats_dir, f"{model_name}_statistics_by_difficulty.json")
            with open(by_diff_file, 'w', encoding='utf-8') as f:
                json.dump(by_diff, f, ensure_ascii=False, indent=2)
        return by_diff
    
def analyze_results_all(mode: str):
    out_root = "output"
    results = {}
    if not os.path.isdir(out_root):
        print(json.dumps(results))
        return
    for name in os.listdir(out_root):
        model_dir = os.path.join(out_root, name)
        if not os.path.isdir(model_dir):
            continue
        eval_path = os.path.join(model_dir, "eval_results.json")
        if not os.path.exists(eval_path):
            continue
        try:
            res = analyze_results_for_dir(model_dir, mode, model_name=name, write_files=False)
            results[name] = res
        except Exception:
            continue
    out_file = os.path.join(out_root, f"statistics_by_{'difficulty' if mode=='d' else 'label'}.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=str, choices=["l", "d"], help="l: by label, d: by difficulty")
    parser.add_argument("model_name", nargs='?', type=str, default=None)
    args = parser.parse_args()
    if args.model_name:
        analyze_results_for_dir(_resolve_model_dir(args.model_name), mode=args.mode, model_name=args.model_name)
    else:
        analyze_results_all(mode=args.mode)
