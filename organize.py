#!/usr/bin/env python3

import json
import os
from collections import defaultdict

def load_annotations_ids():
    gold_false_file = 'data/annotations/gold_false_ids.json'
    ambq_file = 'data/annotations/ambq_ids.json'
    
    gold_false_ids = set()
    ambq_ids = set()
    
    if os.path.exists(gold_false_file):
        with open(gold_false_file, 'r', encoding='utf-8') as f:
            gold_false_ids = set(json.load(f))
    
    if os.path.exists(ambq_file):
        with open(ambq_file, 'r', encoding='utf-8') as f:
            ambq_ids = set(json.load(f))
    
    return gold_false_ids, ambq_ids

def extract_gold_false_from_model(model_path):
    refuter_file = os.path.join(model_path, 'RA-test-eval', 'refuter_output.json')
    
    if not os.path.exists(refuter_file):
        return []
    
    with open(refuter_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    gold_false_ids = []
    for item in data:
        if item.get('result', {}).get('gold_correct') == False:
            gold_false_ids.append(item.get('question_id'))
    
    return gold_false_ids

def extract_ambiguous_question_from_model(model_path):
    refuter_file = os.path.join(model_path, 'RA-test-eval', 'refuter_output.json')
    
    if not os.path.exists(refuter_file):
        return []
    
    with open(refuter_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ambq_ids = []
    for item in data:
        ambiguity = item.get('result', {}).get('ambiguity', '').upper()
        if 'AMBIGUOUS QUESTION' in ambiguity:
            ambq_ids.append(item.get('question_id'))
    
    return ambq_ids


def organize_ids():
    test_dir = 'output/test'
    annotations_gold_false, annotations_ambq = load_annotations_ids()
    
    for model_name in os.listdir(test_dir):
        model_path = os.path.join(test_dir, model_name)
        if os.path.isdir(model_path):
            model_gold_false = extract_gold_false_from_model(model_path)
            model_ambq = extract_ambiguous_question_from_model(model_path)
            
            if model_gold_false or model_ambq:
                print(f"Model {model_name}:")
                
                if model_gold_false:
                    model_gold_false_set = set(model_gold_false)
                    overlap_count = len(model_gold_false_set.intersection(annotations_gold_false))
                    
                    output_file = os.path.join(model_path, 'RA-test-eval', 'gold_false_ids.json')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(model_gold_false, f, ensure_ascii=False, indent=2)
                    
                    print(f"  - RA found gold false count: {len(model_gold_false)}")
                    print(f"  - Overlap with annotations: {overlap_count}")
                    print(f"  - Saved to: {output_file}")
                
                if model_ambq:
                    model_ambq_set = set(model_ambq)
                    overlap_count = len(model_ambq_set.intersection(annotations_ambq))
                    
                    output_file = os.path.join(model_path, 'RA-test-eval', 'ambq_ids.json')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(model_ambq, f, ensure_ascii=False, indent=2)
                    
                    print(f"  - RA found ambiguous question count: {len(model_ambq)}")
                    print(f"  - Overlap with annotations: {overlap_count}")
                    print(f"  - Saved to: {output_file}")
                
                print()

if __name__ == "__main__":
    organize_ids()
