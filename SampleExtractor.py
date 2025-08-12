import json
import os
import glob
import random
from pathlib import Path

def extract_random_samples(input_file, num_samples=100):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    selected_samples = random.sample(data, num_samples)
    return selected_samples

def extract_predicted_data(predicted_folder):
    json_pattern = os.path.join(predicted_folder, "*.json")
    json_files = [f for f in glob.glob(json_pattern) if not os.path.basename(f).startswith('~')]
    
    predicted_data = {}
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            question_id = None
            predicted_sql = None
            exec_res = None
            
            for node in data:
                if question_id is None and 'question_id' in node:
                    question_id = node['question_id']
                
                if node.get('node_type') == 'revision':
                    predicted_sql = node.get('PREDICTED_SQL', '')
                    exec_res = node.get('exec_res', None)
            predicted_data[question_id] = {'predicted_sql': predicted_sql, 'ex': exec_res}
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    return predicted_data

def combine_data(samples, predicted_data):
    combined_results = []
    
    for sample in samples:
        question_id = sample['question_id']
        result = {
            'question_id': question_id,
            'db_id': sample['db_id'],
            'question': sample['question'],
            'evidence': sample['evidence'],
            'gold_sql': sample['gold_sql'],
            'predicted_sql': predicted_data[question_id]['predicted_sql'],
            'ex': predicted_data[question_id]['ex']
        }
        combined_results.append(result)
    return combined_results

if __name__ == "__main__":
    random.seed(42)

    mini_dev_file = "mini_dev_sqlite.json"
    num_samples = 500
    samples = extract_random_samples(mini_dev_file, num_samples)

    predicted_folder = "../bird_dev_deepseek_v3"
    predicted_data = extract_predicted_data(predicted_folder)

    combined_results = combine_data(samples, predicted_data)
    output_file = f"samples_{num_samples}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=2)
