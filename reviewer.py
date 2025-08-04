import os
import json
import openai
from dotenv import load_dotenv
from prompt_reviewer import system_prompt_reviewer, user_prompt_reviewer, constraint_templates

load_dotenv()

class Reviewer:
    def __init__(self, question_obj: dict, constraints: list):
        # self.question_obj = question_obj
        self.constraints = constraints
        self.schema = question_obj["schema"]
        self.evidence = question_obj["evidence"]
        self.gold_sql = question_obj["gold_sql"]
        self.question_id = question_obj["question_id"]
        self.question = question_obj["question"]
        self.output_dir = "reviewer_outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def call(self) -> list:
        constraints_desc, mapping = build_constraints_desc(self.constraints, constraint_templates)

        user_content = user_prompt_reviewer.format(
            schema=self.schema,
            question=self.question,
            evidence=self.evidence,
            gold_sql=self.gold_sql,
            constraints_desc=constraints_desc
        )
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt_reviewer},
                {"role": "user", "content": user_content}
            ],
            response_format={
                'type': 'json_object'
            }
        )
        response_content = response.choices[0].message.content
        try:
            review = json.loads(response_content)
            if not isinstance(review, list):
                print(response_content)
                raise ValueError("Review JSON is not an array")
        except json.JSONDecodeError as e:
            print(response_content)
            raise ValueError(f"Response is not valid JSON: {e}")

        filename = os.path.join(self.output_dir, f"{self.question_id}_review.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(review, f, ensure_ascii=False, indent=2)
        
        revised_constraints = prune_constraints(mapping, review)
        filename = os.path.join(self.output_dir, f"{self.question_id}_revised.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(revised_constraints, f, ensure_ascii=False, indent=2)
        return revised_constraints

def build_constraints_desc(constraints, templates):
    lines = []
    mapping = {}
    n = 1
    for item in constraints:
        qid = str(item.get("question_id"))
        answers = item.get("answer")
        if answers == "NA":
            continue
        tmpl = templates.get(qid)
        for ans in answers:
            lines.append(f"{n}. {tmpl.format(answer=str(ans))}")
            mapping[str(n)] = {"question_id": qid, "answer": ans}
            n += 1
    return "\n".join(lines), mapping

def prune_constraints(mapping, review_results):
    remove = {r["question_id"] for r in review_results if not r.get("necessity")}
    retained = []
    for ln, info in mapping.items():
        if ln not in remove:
            retained.append(info)
    return retained

