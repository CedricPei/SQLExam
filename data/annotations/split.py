#!/usr/bin/env python3

import json
import os
from collections import defaultdict
from typing import Dict, List, Any

def load_annotation_files():
    annotation_files = [
        'annotations_1.json',
        'annotations_2.json', 
        'annotations_4.json',
        'annotations_5.json',
        'annotations-3.json'
    ]
    
    all_data = []
    
    for filename in annotation_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                
                if isinstance(data, dict) and 'Sheet1' in data:
                    print(f"Skipping {filename} (special format)")
                    continue
                elif isinstance(data, list):
                    all_data.extend(data)
                else:
                    print(f"Warning: {filename} has incorrect format")
        else:
            print(f"Warning: File {filename} does not exist")
    
    return all_data

def group_by_question_id(data: List[Dict]) -> Dict[int, List[Dict]]:
    grouped = defaultdict(list)
    
    for item in data:
        if 'question_id' in item:
            question_id = item['question_id']
            filtered_item = {
                'question_id': item['question_id'],
                'db_id': item.get('db_id', ''),
                'question': item.get('question', ''),
                'predicted_sql': item.get('predicted_sql', ''),
                'gold_sql': item.get('gold_sql', ''),
                'label': item.get('label', None),
                'reason': item.get('reason', ''),
                'evidence': item.get('evidence', '')
            }
            grouped[question_id].append(filtered_item)
    
    return grouped

def analyze_labels(grouped_data: Dict[int, List[Dict]]):
    test_cases = []
    argue_cases = []
    lack_cases = []
    
    for question_id, items in grouped_data.items():
        if len(items) == 1:
            lack_cases.append({
                'question_id': question_id,
                'items': items
            })
        elif len(items) >= 2:
            labels = [item['label'] for item in items]
            unique_labels = set(labels)
            
            if len(unique_labels) == 1:
                test_cases.append({
                    'question_id': question_id,
                    'items': items,
                    'label': list(unique_labels)[0]
                })
            else:
                argue_cases.append({
                    'question_id': question_id,
                    'items': items,
                    'labels': list(unique_labels)
                })
    
    return test_cases, argue_cases, lack_cases

def save_results(test_cases: List[Dict], argue_cases: List[Dict], lack_cases: List[Dict]):
    test_data = []
    for case in test_cases:
        if len(case['items']) >= 2:
            reasons = [item.get('reason', '') for item in case['items']]
            unique_reasons = list(set(reasons))
            
            test_record = {
                'question_id': case['question_id'],
                'db_id': case['items'][0].get('db_id', ''),
                'question': case['items'][0].get('question', ''),
                'predicted_sql': case['items'][0].get('predicted_sql', ''),
                'gold_sql': case['items'][0].get('gold_sql', ''),
                'label': case['label'],
                'evidence': case['items'][0].get('evidence', ''),
                'reason_1': unique_reasons[0] if len(unique_reasons) > 0 else '',
                'reason_2': unique_reasons[1] if len(unique_reasons) > 1 else ''
            }
            test_data.append(test_record)
    
    with open('test.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    argue_data = []
    for case in argue_cases:
        if len(case['items']) >= 2:
            reasons = [item.get('reason', '') for item in case['items']]
            unique_reasons = list(set(reasons))
            
            argue_record = {
                'question_id': case['question_id'],
                'db_id': case['items'][0].get('db_id', ''),
                'question': case['items'][0].get('question', ''),
                'predicted_sql': case['items'][0].get('predicted_sql', ''),
                'gold_sql': case['items'][0].get('gold_sql', ''),
                'evidence': case['items'][0].get('evidence', ''),
                'reason_1': unique_reasons[0] if len(unique_reasons) > 0 else '',
                'reason_2': unique_reasons[1] if len(unique_reasons) > 1 else ''
            }
            argue_data.append(argue_record)
    
    lack_data = []
    for case in lack_cases:
        for item in case['items']:
            lack_data.append(item)
    
    return len(test_data), len(argue_data), len(lack_data)

def count_test_labels(test_data):
    true_count = sum(1 for item in test_data if item.get('label') == True)
    false_count = sum(1 for item in test_data if item.get('label') == False)
    return true_count, false_count

def main():
    data = load_annotation_files()
    grouped_data = group_by_question_id(data)
    test_cases, argue_cases, lack_cases = analyze_labels(grouped_data)
    test_count, argue_count, lack_count = save_results(test_cases, argue_cases, lack_cases)
    
    test_data = []
    for case in test_cases:
        if len(case['items']) >= 2:
            test_data.append({
                'question_id': case['question_id'],
                'label': case['label']
            })
    
    true_count, false_count = count_test_labels(test_data)
    
    print(f"- Consistent annotations (question_id): {len(test_cases)}")
    print(f"- Inconsistent annotations (question_id): {len(argue_cases)}")
    print(f"- Single annotation (question_id): {len(lack_cases)}")
    print(f"- Test data true labels: {true_count}")
    print(f"- Test data false labels: {false_count}")

if __name__ == "__main__":
    main()
