#!/usr/bin/env python3

import json
import os
import random
from typing import List, Dict

def load_test_data():
    with open('test.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

def sample_data(data: List[Dict], num_true=None, num_false=None):
    # If counts are not provided, randomly pick up to 30 examples overall
    if num_true is None and num_false is None:
        k = 50 if len(data) >= 50 else len(data)
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

    return sampled_data

def save_sample(sampled_data: List[Dict], filename: str = 'sample.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sampled_data, f, ensure_ascii=False, indent=2)

def main():
    random.seed(24)
    test_data = load_test_data()
    sampled_data = sample_data(test_data)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    save_sample(sampled_data, os.path.join(project_root, 'sample.json'))

if __name__ == "__main__":
    main()
