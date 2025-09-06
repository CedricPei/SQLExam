import json
import os
import sys

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
                "ex": eval_item.get("ex"),
                "score": eval_item.get("score")
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
    
    ex0_score1 = [item for item in data if item.get("ex") == 0 and item.get("score") == 1.0]
    ex1_score0 = [item for item in data if item.get("ex") == 1 and item.get("score") == 0.0]
    
    model_dir = model_name
    ex0_file = os.path.join(model_dir, f"{model_name}_ex0_score1.json")
    ex1_file = os.path.join(model_dir, f"{model_name}_ex1_score0.json")
    
    with open(ex0_file, 'w', encoding='utf-8') as f:
        json.dump(ex0_score1, f, ensure_ascii=False, indent=2)
    
    with open(ex1_file, 'w', encoding='utf-8') as f:
        json.dump(ex1_score0, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <model_name>")
        print("Example: python analyze.py deepseek-r1")
        sys.exit(1)
    
    model_name = sys.argv[1]
    merge_results_by_question_id(model_name)
    analyze_results(model_name)