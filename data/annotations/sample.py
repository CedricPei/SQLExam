#!/usr/bin/env python3

import json
import os
import random
from typing import List, Dict

def load_test_data():
    with open('test.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

def load_dev_data():
    with open('dev.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

def create_evidence_mapping(dev_data: List[Dict]):
    evidence_map = {}
    for item in dev_data:
        question_id = item.get('question_id')
        evidence = item.get('evidence', '')
        if question_id is not None:
            evidence_map[question_id] = evidence
    return evidence_map

def sample_data(data: List[Dict], evidence_map: Dict[int, str], num_true=None, num_false=None):
    # If counts are not provided, randomly pick up to 30 examples overall
    if num_true is None and num_false is None:
        k = 30 if len(data) >= 30 else len(data)
        sampled_data = random.sample(data, k)
    else:
        # Backward-compatible path: sample by label counts
        if num_true is None:
            num_true = 0
        if num_false is None:
            num_false = 0
        true_samples = [item for item in data if item.get('label') == True]
        false_samples = [item for item in data if item.get('label') == False]
        if len(true_samples) < num_true:
            num_true = len(true_samples)
        if len(false_samples) < num_false:
            num_false = len(false_samples)
        sampled_true = random.sample(true_samples, num_true) if num_true > 0 else []
        sampled_false = random.sample(false_samples, num_false) if num_false > 0 else []
        sampled_data = sampled_true + sampled_false
        random.shuffle(sampled_data)

    for item in sampled_data:
        question_id = item.get('question_id')
        if question_id in evidence_map:
            item['evidence'] = evidence_map[question_id]
        else:
            item['evidence'] = ""
            print(f"警告: question_id {question_id} 在dev.json中未找到evidence")
    
    return sampled_data

def save_sample(sampled_data: List[Dict], filename: str = 'sample.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sampled_data, f, ensure_ascii=False, indent=2)

def main():
    random.seed(50)
    test_data = load_test_data()
    dev_data = load_dev_data()
    evidence_map = create_evidence_mapping(dev_data)
    sampled_data = sample_data(test_data, evidence_map)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    save_sample(sampled_data, os.path.join(project_root, 'sample.json'))

if __name__ == "__main__":
    main()
