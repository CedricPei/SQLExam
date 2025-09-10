#!/usr/bin/env python3

import json
import os
import random
import sys
from typing import List, Dict

def load_test_data():
    with open('data/annotations/test.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

def sample_data(data: List[Dict], num_total: int | None = None, num_true: int | None = None, num_false: int | None = None):
    if num_true is None and num_false is None:
        k = num_total if num_total is not None else (50 if len(data) >= 50 else len(data))
        k = min(max(int(k), 0), len(data))
        sampled_data = random.sample(data, k)
    else:
        if num_true is None:
            num_true = 0
        if num_false is None:
            if num_total is not None:
                num_false = max(int(num_total) - int(num_true), 0)
            else:
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

    # CLI usage:
    #   python sample.py                -> default 50 samples
    #   python sample.py 40             -> 40 samples
    #   python sample.py 40 20          -> total 40 samples with 20 true and 20 false
    args = sys.argv[1:]
    if len(args) == 0:
        sampled_data = sample_data(test_data)
    elif len(args) == 1:
        num_total = int(args[0])
        sampled_data = sample_data(test_data, num_total=num_total)
    else:
        num_total = int(args[0])
        num_true = int(args[1])
        sampled_data = sample_data(test_data, num_total=num_total, num_true=num_true)

    save_sample(sampled_data, os.path.join(os.getcwd(), 'sample.json'))

if __name__ == "__main__":
    main()


