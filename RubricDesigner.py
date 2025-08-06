import os
import json
import openai
from dotenv import load_dotenv
from prompt_rubric_designer import system_prompt_rubric_designer, user_prompt_rubric_designer, rubric_templates
from helper import extract_json_from_response

load_dotenv()

class RubricDesigner:
    def __init__(self, question_obj: dict, constraints: list, output_dir: str = "rubric_outputs", model: str = "deepseek-chat"):
        self.model = model
        self.schema = question_obj["schema"]
        self.question_id = question_obj["question_id"]
        self.question = question_obj["question"]
        self.evidence = question_obj["evidence"]
        self.gold_sql = question_obj["gold_sql"]
        self.constraints = constraints
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def call(self) -> list:
        constraint_descriptions = self.build_constraint_description(self.constraints)
        # print(constraint_descriptions)
        user_content = user_prompt_rubric_designer.format(
            schema=self.schema,
            question=self.question,
            background=self.evidence,
            gold_sql=self.gold_sql,
            constraint_descriptions=constraint_descriptions
        )
        # print(user_content)
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt_rubric_designer},
                {"role": "user", "content": user_content}
            ],
            # response_format={
            #     'type': 'json_object'
            # }
            temperature=0
        )
        response_content = response.choices[0].message.content

        try:
            answer = extract_json_from_response(response_content)
            designed_rubric = json.loads(answer)
            if not isinstance(designed_rubric, list):
                print(response_content)
                raise ValueError("Response JSON is not an array")
        except json.JSONDecodeError as e:
            print(response_content)
            raise ValueError(f"Response is not valid JSON: {e}")

        designed_rubric = [{"id": str(i), **question} for i, question in enumerate(designed_rubric, 1)]
        filename = os.path.join(self.output_dir, f"{self.question_id}_rubric.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(designed_rubric, f, ensure_ascii=False, indent=2)

        return designed_rubric

    def build_constraint_description(self, constraints: list) -> str:
        lines = []
        idx = 1
        for constraint in constraints:
            qid = constraint.get("question_id")
            answers = constraint.get("answer")
            if answers == "NA":
                continue
            template_info = rubric_templates.get(qid)

            if qid in ["1", "3"]:
                if isinstance(answers, list) and len(answers) > 0:
                    description = template_info["description"].format(answer=", ".join(answers))
                    lines.append(f"{idx}. {description}")
                    idx += 1
            else:
                for answer in answers:
                    description = template_info["description"].format(answer=answer)
                    lines.append(f"{idx}. {description}")
                    idx += 1
        return "\n".join(lines) 