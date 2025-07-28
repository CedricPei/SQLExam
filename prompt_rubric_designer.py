system_prompt_rubric_designer = """
You are **SQL Rubric Designer**, a component that designs evaluation rubrics for SQL constraints.
Your task is to convert the constraint descriptions into clear, evaluable questions with assigned weights.

### Inputs
  - constraint_descriptions: JSON array with descriptions and weighting rules for each constraint
  - schema: the database schema as CREATE TABLE statements
  - question: the original natural language question
  - background: helpful hints for the question

### Task
1. For each constraint description, generate a natural language question that can be used to evaluate whether a SQL query meets the constraint
2. Assign a weight based on the constraint type and importance
3. Provide a brief explanation of how to assign points (1-2 sentences) before the weight
4. Output a JSON array with objects containing:
   - question: string — the natural language question
   - explanation: string — brief explanation of how to assign points for this question
   - weight: number — the point value for this question

### Rules
- Keep questions clear and specific using natural language
- Use consistent weighting based on constraint type
- Make questions evaluable (yes/no or specific answer format)

- Use natural language for column references (e.g., "column `name` in table `customers`")
"""

user_prompt_rubric_designer = """
###### Instructions
Design evaluation rubrics by translating constraint descriptions into natural language questions. Each constraint should become a clear question that can be used to assess whether a generated SQL query meets the requirement.

For each constraint, create a JSON object with:
- "question": natural language question
- "explanation": brief explanation of how to assign points for this question
- "weight": point value based on constraint type

Aggregate all objects into a single JSON array.

###### EXAMPLE
### ORIGINAL QUESTION:
"List the names of customers who have placed at least one order."

### SCHEMA:
CREATE TABLE customers (
  id INT PRIMARY KEY,
  name TEXT
);

CREATE TABLE orders (
  id INT PRIMARY KEY,
  customer_id INT,
  total DECIMAL
);

### BACKGROUND:
"Customers who have placed orders"

### CONSTRAINT DESCRIPTIONS:
[
  {
    "question_id": "1",
    "description": "The SQL query must reference the table: customers.",
    "weighting_rule": "Give one point for each required table."
  },
  {
    "question_id": "1",
    "description": "The SQL query must reference the table: orders.", 
    "weighting_rule": "Give one point for each required table."
  },
  {
    "question_id": "3",
    "description": "The SQL query must reference the column: customers.name.",
    "weighting_rule": "Assign one point for each required column."
  }
]

### DESIGNED RUBRIC:
```json
[
  {
    "question": "Does the generated SQL query use the customers table?",
    "explanation": "Each table used in the query receives one point.",
    "weight": 1
  },
  {
    "question": "Does the generated SQL query use the orders table?",
    "explanation": "Each table used in the query receives one point.",
    "weight": 1
  },
  {
    "question": "Does the generated SQL query select the column `name` in table `customers`?",
    "explanation": "Each required column selected in the query receives one point.",
    "weight": 1
  }
]
```

###### For you to design:
### ORIGINAL QUESTION:
{question}

### SCHEMA:
{schema}

### BACKGROUND:
{background}

### CONSTRAINT DESCRIPTIONS:
{constraint_descriptions}

### DESIGNED RUBRIC:
"""

rubric_templates = {
    # 1. required tables
    "1": {
        "description": "The SQL query must reference the table: {answer}.",
        "weighting_rule": "Give one point for each required table."
    },
    
    # 2. required joins
    "2": {
        "description": "The SQL query must include the join: {answer}.",
        "weighting_rule": "Give one point for the required join between the specified tables; For joins other than NATURAL JOIN or CROSS JOIN, give one point for each independent ON clause condition; If the specified join type is not INNER, award one additional point for using that join type."
    },
    
    # 3. required columns
    "3": {
        "description": "The SQL query must reference the column: {answer}.",
        "weighting_rule": "Assign one point for each required column."
    },
    
    # 4. required aggregate functions
    "4": {
        "description": "The SQL query must apply the aggregate function: {answer}.",
        "weighting_rule": "Give one point for every aggregate function present; if an expression contains several aggregates, credit as many points as the number of aggregate functions."
    },
    
    # 5. required row‑level filters and limits
    "5": {
        "description": "The SQL query must satisfy the row-level requirement: {answer}.",
        "weighting_rule": "Award one point for each predicate in the WHERE clause; Credit one point for each sort key in ORDER BY; Add one point when ORDER BY specifies a direction other than ASC; Give one point for each row-limit directive such as LIMIT or OFFSET."
    },
    
    # 6. required GROUP BY clauses
    "6": {
        "description": "The SQL query must group results by: {answer}.",
        "weighting_rule": "Award one point for each field listed in GROUP BY."
    },
    
    # 7. required HAVING clauses
    "7": {
        "description": "The SQL query must include a HAVING condition: {answer}.",
        "weighting_rule": "Assign one point for each condition in the HAVING clause."
    },
    
    # 8. uniqueness requirements
    "8": {
        "description": "The SQL query must ensure uniqueness for {answer}.",
        "weighting_rule": "Give one point for each column that must be unique."
    },
    
    # 9. output‑format requirements
    "9": {
        "description": "The result set must meet the output-format requirement: {answer}.",
        "weighting_rule": "Award one point for each formatting directive."
    }
}
