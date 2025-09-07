#!/usr/bin/env python3
"""
从test.json中随机选择30个例子，15个label为true，15个label为false
"""

import json
import random
from typing import List, Dict

def load_test_data():
    """加载test.json数据"""
    with open('test.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

def load_dev_data():
    """加载dev.json数据"""
    with open('dev.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

def create_evidence_mapping(dev_data: List[Dict]):
    """创建question_id到evidence的映射"""
    evidence_map = {}
    for item in dev_data:
        question_id = item.get('question_id')
        evidence = item.get('evidence', '')
        if question_id is not None:
            evidence_map[question_id] = evidence
    return evidence_map

def sample_data(data: List[Dict], evidence_map: Dict[int, str], num_true: int = 15, num_false: int = 15):
    """从数据中采样指定数量的true和false样本，并添加evidence信息"""
    # 按label分组
    true_samples = [item for item in data if item.get('label') == True]
    false_samples = [item for item in data if item.get('label') == False]
    
    print(f"原始数据统计:")
    print(f"- label为true的记录数: {len(true_samples)}")
    print(f"- label为false的记录数: {len(false_samples)}")
    
    # 检查是否有足够的样本
    if len(true_samples) < num_true:
        print(f"警告: true样本不足，只有{len(true_samples)}个，请求{num_true}个")
        num_true = len(true_samples)
    
    if len(false_samples) < num_false:
        print(f"警告: false样本不足，只有{len(false_samples)}个，请求{num_false}个")
        num_false = len(false_samples)
    
    # 随机采样
    sampled_true = random.sample(true_samples, num_true)
    sampled_false = random.sample(false_samples, num_false)
    
    # 合并并打乱顺序
    sampled_data = sampled_true + sampled_false
    random.shuffle(sampled_data)
    
    # 为每个样本添加evidence信息
    for item in sampled_data:
        question_id = item.get('question_id')
        if question_id in evidence_map:
            item['evidence'] = evidence_map[question_id]
        else:
            item['evidence'] = ""
            print(f"警告: question_id {question_id} 在dev.json中未找到evidence")
    
    return sampled_data

def save_sample(sampled_data: List[Dict], filename: str = 'sample.json'):
    """保存采样数据到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sampled_data, f, ensure_ascii=False, indent=2)
    
    # 统计采样结果
    true_count = sum(1 for item in sampled_data if item.get('label') == True)
    false_count = sum(1 for item in sampled_data if item.get('label') == False)
    
    print(f"\n采样结果:")
    print(f"- 总样本数: {len(sampled_data)}")
    print(f"- label为true: {true_count}个")
    print(f"- label为false: {false_count}个")
    print(f"- 已保存到: {filename}")

def main():
    print("开始从test.json中采样数据...")
    
    # 设置随机种子以确保结果可重现（可选）
    random.seed(20)
    
    # 加载数据
    test_data = load_test_data()
    dev_data = load_dev_data()
    print(f"加载了 {len(test_data)} 条test记录")
    print(f"加载了 {len(dev_data)} 条dev记录")
    
    # 创建evidence映射
    evidence_map = create_evidence_mapping(dev_data)
    print(f"创建了 {len(evidence_map)} 个question_id到evidence的映射")
    
    # 采样数据
    sampled_data = sample_data(test_data, evidence_map, num_true=15, num_false=15)
    
    # 保存采样结果
    save_sample(sampled_data, 'sample.json')
    
    print("\n采样完成！")

if __name__ == "__main__":
    main()
