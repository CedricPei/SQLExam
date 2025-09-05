import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any
from helper import get_schema, extract_json_from_response
from prompt_refuter import system_prompt_refuter, user_prompt_refuter

load_dotenv()


class Refuter:
    """Refuter validates predicted SQL against gold standard SQL to identify critical conflicts"""
    
    def __init__(self, model: str = None):
        self.model = model
    
    def call(self, question: Dict[str, Any], pred_sql: str, pred_result: Any, gold_result: Any) -> bool:
        """Validate predicted SQL against gold standard SQL for critical conflicts"""
        try:
            schema = get_schema(question["db_id"])
            
            user_content = user_prompt_refuter.format(
                question=question["question"],
                evidence=question.get("evidence", ""),
                predicted_sql=pred_sql,
                gold_sql=question["gold_sql"],
                schema=schema,
                pred_result=pred_result,
                gold_result=gold_result
            )
            
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_refuter},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )
            result = json.loads(extract_json_from_response(response.choices[0].message.content))
            # Save output to JSON file
            os.makedirs("refuter_outputs", exist_ok=True)
            with open(f"refuter_outputs/refuter_{question['question_id']}.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            return result.get("verdict", False)

        except Exception as e:
            print(f"Refuter error: {e}")
            return False
