import json
import os
import sys
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

def analyze_results(model_name):
    model_dir = _resolve_model_dir(model_name)
    data = _load_eval_results(model_dir)
    
    def is_true_label(item):
        label = item.get("label")
        return label is True or label == "true" or label == "True"
    
    def is_false_label(item):
        label = item.get("label")
        return label is False or label == "false" or label == "False"
    
    label_true_score_0 = [item for item in data if is_true_label(item) and item.get("score") == 0.0]
    label_false_score_1 = [item for item in data if is_false_label(item) and item.get("score") == 1.0]
    
    total_items = len(data)
    label_true_count = len([item for item in data if is_true_label(item)])
    label_false_count = len([item for item in data if is_false_label(item)])
    score_1_count = len([item for item in data if item.get("score") == 1.0])
    score_0_count = len([item for item in data if item.get("score") == 0.0])
    
    correct_predictions = len([item for item in data if 
                              (is_true_label(item) and item.get("score") == 1.0) or 
                              (is_false_label(item) and item.get("score") == 0.0)])
    
    incorrect_predictions = len(label_true_score_0) + len(label_false_score_1)
    
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
    label_true_score_0_file = os.path.join(model_dir, f"{model_name}_label_true_score_0.json")
    label_false_score_1_file = os.path.join(model_dir, f"{model_name}_label_false_score_1.json")
    
    with open(label_true_score_0_file, 'w', encoding='utf-8') as f:
        json.dump(label_true_score_0, f, ensure_ascii=False, indent=2)
    
    with open(label_false_score_1_file, 'w', encoding='utf-8') as f:
        json.dump(label_false_score_1, f, ensure_ascii=False, indent=2)
    
    stats = {
        "total_items": total_items,
        "label_true_count": label_true_count,
        "label_false_count": label_false_count,
        "score_1_count": score_1_count,
        "score_0_count": score_0_count,
        "correct_predictions": correct_predictions,
        "incorrect_predictions": incorrect_predictions,
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
        },
        "error_cases": {
            "label_true_score_0_count": len(label_true_score_0),
            "label_false_score_1_count": len(label_false_score_1)
        }
    }
    
    stats_dir = "output"
    os.makedirs(stats_dir, exist_ok=True)
    stats_file = os.path.join(stats_dir, f"{model_name}_statistics.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <model_name>")
        print("Example: python analyze.py deepseek-r1")
        sys.exit(1)
    
    model_name = sys.argv[1]
    analyze_results(model_name)
