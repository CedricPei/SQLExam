import json
import random

def extract_random_samples(input_file, output_file, num_samples=100):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    selected_samples = random.sample(data, num_samples)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_samples, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    random.seed(42)
    
    extract_random_samples(
        input_file="mini_dev_sqlite.json",
        output_file="100_samples.json",
        num_samples=100
    )