import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any
from helper import get_schema, extract_json_from_response, append_to_json_file
from prompts.prompt_refuter import system_prompt_refuter, user_prompt_refuter, user_prompt_refuter_without_results

load_dotenv()


class Refuter:
    """Refuter validates predicted SQL against gold standard SQL to identify critical conflicts"""
    
    def __init__(self, model: str = None):
        self.model = model
    
    def call(self, question: Dict[str, Any], pred_sql: str, pred_result: Any = None, gold_result: Any = None) -> bool:
        """Validate predicted SQL against gold standard SQL for critical conflicts"""
        try:
            schema = get_schema(question["db_id"])
            
            if pred_result is not None and gold_result is not None:

                pred_result = pred_result.head(20)
                gold_result = gold_result.head(20)
                
                user_content = user_prompt_refuter.format(
                    question=question["question"],
                    evidence=question.get("evidence", ""),
                    predicted_sql=pred_sql,
                    gold_sql=question["gold_sql"],
                    schema=schema,
                    pred_result=pred_result,
                    gold_result=gold_result
                )
            else:
                user_content = user_prompt_refuter_without_results.format(
                    question=question["question"],
                    evidence=question.get("evidence", ""),
                    predicted_sql=pred_sql,
                    gold_sql=question["gold_sql"],
                    schema=schema
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
            # Save output to a single JSON file (append mode)
            output_data = {
                "question_id": question["question_id"],
                "result": result
            }
            append_to_json_file(output_data, "output/refuter_output.json")

            return result.get("verdict", False)

        except Exception as e:
            print(f"Refuter error: {e}")
            return False
