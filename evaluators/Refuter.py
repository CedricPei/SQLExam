import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any
from .utils import get_db_info, extract_json_from_response, append_to_json_file
from prompts.prompt_refuter import system_prompt_refuter, user_prompt_refuter, user_prompt_refuter_without_results

load_dotenv()


class Refuter:
    """Refuter validates predicted SQL against gold standard SQL to identify critical conflicts"""
    
    def __init__(self, model: str = None, output_dir: str = "output"):
        self.model = model
        self.output_dir = output_dir
    
    def call(self, question: Dict[str, Any], pred_sql: str, pred_result: Any = None, gold_result: Any = None, prover_reason: str = None) -> bool:
        """Validate predicted SQL against gold standard SQL for critical conflicts"""
        try:
            db_info = get_db_info(question["db_id"], [pred_sql, question["gold_sql"]])
            
            if pred_result is not None and gold_result is not None:

                pred_result = pred_result.head(20)
                gold_result = gold_result.head(20)
                
                user_content = user_prompt_refuter.format(
                    question=question["question"],
                    evidence=question.get("evidence", ""),
                    predicted_sql=pred_sql,
                    gold_sql=question["gold_sql"],
                    db_info=db_info,
                    pred_result=pred_result,
                    gold_result=gold_result,
                    prover_reason=prover_reason
                )
            else:
                user_content = user_prompt_refuter_without_results.format(
                    question=question["question"],
                    evidence=question.get("evidence", ""),
                    predicted_sql=pred_sql,
                    gold_sql=question["gold_sql"],
                    db_info=db_info,
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
            # print(response.choices[0].message.content)
            # Save output to a single JSON file (append mode)
            output_data = {
                "question_id": question["question_id"],
                "result": result
            }
            output_file = os.path.join(self.output_dir, "refuter_output.json")
            append_to_json_file(output_data, output_file)

            return result.get("verdict", False)

        except Exception as e:
            print(f"Refuter error: {e}")
            return False
