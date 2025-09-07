import json
import os
import sys
import numpy as np
from sklearn.metrics import cohen_kappa_score

def merge_results_by_question_id(model_name):
    model_dir = model_name
    refuter_file = os.path.join(model_dir, "refuter_output.json")
    prover_file = os.path.join(model_dir, "prover_output.json")
    eval_file = os.path.join(model_dir, "eval_results.json")
    
    with open(refuter_file, 'r', encoding='utf-8') as f:
        refuter_data = json.load(f)
    with open(prover_file, 'r', encoding='utf-8') as f:
        prover_data = json.load(f)
    with open(eval_file, 'r', encoding='utf-8') as f:
        eval_data = json.load(f)
    
    refuter_dict = {item['question_id']: item['result'] for item in refuter_data}
    prover_dict = {item['question_id']: item['result'] for item in prover_data}
    eval_dict = {item['question_id']: item for item in eval_data}
    
    all_question_ids = set(refuter_dict.keys()) | set(prover_dict.keys()) | set(eval_dict.keys())
    
    merged_results = []
    for question_id in sorted(all_question_ids):
        merged_item = {"question_id": question_id}
        
        if question_id in eval_dict:
            eval_item = eval_dict[question_id]
            merged_item.update({
                "question": eval_item.get("question"),
                "evidence": eval_item.get("evidence"),
                "gold_sql": eval_item.get("gold_sql"),
                "predicted_sql": eval_item.get("predicted_sql"),
                "score": eval_item.get("score"),
                "label": eval_item.get("label")
            })
        
                
        if question_id in prover_dict:
            merged_item["prover_details"] = prover_dict[question_id]

        if question_id in refuter_dict:
            merged_item["refuter_details"] = refuter_dict[question_id]

        merged_results.append(merged_item)
    
    results_file = f"{model_name}_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, ensure_ascii=False, indent=2)

def analyze_results(model_name):
    results_file = f"{model_name}_results.json"
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 处理JSON中的布尔值（可能是字符串或布尔类型）
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
    
    model_dir = model_name
    os.makedirs(model_dir, exist_ok=True)
    
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
            "cohen_kappa": kappa
        },
        "error_cases": {
            "label_true_score_0_count": len(label_true_score_0),
            "label_false_score_1_count": len(label_false_score_1)
        }
    }
    
    stats_file = os.path.join(model_dir, f"{model_name}_statistics.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <model_name>")
        print("Example: python analyze.py deepseek-r1")
        sys.exit(1)
    
    model_name = sys.argv[1]
    merge_results_by_question_id(model_name)
    analyze_results(model_name)