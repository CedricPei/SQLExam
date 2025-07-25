system_prompt_reviewer = """
You are **SQL Constraint Reviewer**.

Inputs:
  - question: the user’s natural‑language question.
  - schema: the database schema as CREATE TABLE statements.
  - constraint hypotheses: numbered lines of the form "<question_id>. <description>", stating what the user believes is mandatory.

For each hypothesis, output a JSON object with exactly these fields, in this order:
  question_id: string — the numeric prefix  
  reason: string — one or two concise sentences explaining why this constraint is or is not strictly required, given the question and schema  
  necessity: boolean — true if strictly necessary, false otherwise  

Return a single JSON array of these objects. Do not include any extra keys or commentary.
""".strip()

user_prompt_reviewer = """
### INSTRUCTIONS
For each hypothesis in the “CONSTRAINT HYPOTHESES” section above, decide whether it is strictly necessary to answer the QUESTION given the SCHEMA, justify your decision in the `reason`, and set `necessity` accordingly. Output **only** the JSON array as specified.

###### EXAMPLE
### QUESTION:
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

### CONSTRAINT HYPOTHESES:
1. The user believes that referencing **table customers** is essential in the SQL query.
2. The user believes that referencing **table orders** is essential in the SQL query.
3. The user believes that including the join **orders INNER JOIN customers ON orders.customer_id = customers.id** is indispensable.
4. The user believes that using **column customers.name** is necessary.
5. The user believes that ordering by **customers.id** is necessary.

### ANSWER:
```json
[
  {{
    "question_id": "1",
    "reason": "Customer names reside only in the customers table, so without it the query cannot return names.",
    "necessity": true
  }},
  {{
    "question_id": "2",
    "reason": "The question asks for customers who placed orders, so orders must be referenced to identify those customers.",
    "necessity": true
  }},
  {{
    "question_id": "3",
    "reason": "Joining orders to customers is required to match orders to customer names.",
    "necessity": true
  }},
  {{
    "question_id": "4",
    "reason": "The query must return customer names, so customers.name is mandatory.",
    "necessity": true
  }},
  {{
    "question_id": "5",
    "reason": "Sorting by customer ID does not affect which names are returned and is not required to answer the question.",
    "necessity": false
  }}
]
```

###### For you to answer:
### QUESTION:
{question}

### SCHEMA:
{schema}

### CONSTRAINT HYPOTHESES:
{constraints_desc}

### ANSWER:
""".strip()


constraint_templates = {
    # 1. tables
    "1": "The user believes that referencing the **{answer}** table is essential in the SQL query.",
    
    # 2. joins
    "2": "According to the user, the join **{answer}** must be included for the query to answer the question correctly.",
    
    # 3. columns
    "3": "The user considers the **{answer}** column indispensable for solving the problem via SQL.",
    
    # 4. aggregate functions
    "4": "The user deems the aggregate expression **{answer}** necessary in the SELECT clause of the query.",
    
    # 5. row-level filters / limits
    "5": "The user requires applying the row-level filter **{answer}** to obtain the desired result set.",
    
    # 6. GROUP BY clauses
    "6": "The user judges that grouping **{answer}** is mandatory in the SQL query.",
    
    # 7. HAVING clauses
    "7": "The user regards the HAVING condition **{answer}** as essential for filtering aggregated results.",
    
    # 8. unique columns
    "8": "The user insists that the output enforce uniqueness on the **{answer}** column.",
    
    # 9. output aliases
    "9": "The user specifies that the result column must be aliased as **{answer}**.",
    
    # 10. output format details
    "10": "The user expects the output to follow the format detail: **{answer}**."
}



