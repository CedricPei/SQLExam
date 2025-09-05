import json
import os

def analyze_ex0_usefulness1(input_file="eval_results.json", output_file="ex0_score1.json"):
    if not os.path.exists(input_file):
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Filter for ex=0 and usefulness=1.0
    filtered_results = []
    for result in results:
        if result.get('ex') == 0 and result.get('score') == 1.0:
            filtered_results.append(result)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=2)

def analyze_ex1_usefulness0(input_file="eval_results.json", output_file="ex1_score0.json"):
    if not os.path.exists(input_file):
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Filter for ex=1 and usefulness=0.0
    filtered_results = []
    for result in results:
        if result.get('ex') == 1 and result.get('score') == 0.0:
            filtered_results.append(result)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    analyze_ex0_usefulness1()
    analyze_ex1_usefulness0()
