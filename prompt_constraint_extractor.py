system_prompt_constraint_extractor = """
You are an **Constraint Extractor** in an LLM-based SQL-evaluation pipeline.

### Inputs
- `SCHEMA`: database schema (text)
- `QUESTION`: user's natural-language question
- `BACKGROUND` : helpful hints for the question
- `GOLD_SQL`: gold-standard SQL query

### Task
1. For every atomic requirement listed in the checklist, output one JSON object containing exactly: {{ "question_id", "answer" }}.
    - `question_id`: the numbering string from the checklist (e.g. "2.3").  
    - `answer`: concrete value(s) you extract (JSON array).  
    - If the requirement does not apply to the question, set `"answer": "NA"`.

2. Aggregate all objects into a single JSON array and enclose it in a markdown code block that begins with ```json.

### Rules
- Prioritize the question and schema; use GOLD_SQL only as a supplementary reference, ignoring any elements it includes but are not necessary.
- **IMPORTANT** Always write the full table names in your answer, not shorthand such as `T1` or `c`.
- One object per atomic requirement; no missing question_ids.  
- Keep answers concise; use arrays when multiple values apply.  
- Never add extra keys or change key names.
- **CRITICAL**: For complex SQL queries with multiple independent SELECT structures (subqueries, CTEs, UNION clauses), analyze EACH independent SELECT structure separately and combine the requirements. Do not focus only on the main SELECT structure.
""".strip()


user_prompt_constraint_extractor = """
######  Instructions
For each checklist item below, output **one** JSON object with exactly:
- "question_id": the item's identifier (e.g., "2").
- "answer": the extracted value(s) (JSON array).
    - If the requirement does not apply, set "answer": "NA".
    - Do NOT use table aliases in your answer—always write full table names.

**IMPORTANT** Extract only information that the user has explicitly required or is mandatory for answering the question.
**IMPORTANT: TREAT GOLD_SQL AS REFERENCE ONLY**, ignore any operation it contains that the user did not request (e.g., extra aliases or formatting).

**CRITICAL FOR COMPLEX QUERIES**: If the SQL query contains multiple independent SELECT structures (subqueries, CTEs, UNION/INTERSECT/EXCEPT clauses), analyze EACH independent SELECT structure separately and combine all requirements. Do not focus only on the main SELECT structure. For example:
- If there's a subquery in WHERE clause, analyze both the main query AND the subquery
- If there are CTEs (WITH clauses), analyze each CTE separately
- If there are UNION clauses, analyze each SELECT in the UNION separately
- Combine all tables, joins, columns, etc. from ALL independent SELECT structures

After completing all items, aggregate the objects into a **single JSON array** and enclose it in a markdown code block that begins with ```json.  

######  CHECKLIST BEGIN

1. List NECESSARY set operators that the query MUST use to combine multiple result sets.
    - Example: ["UNION", "EXCEPT"]

2. List NECESSARY tables the answer MUST reference and that MUST appear in the provided schema.

3. List each NECESSARY join that is STRICTLY REQUIRED to answer the question.
    - Consider `JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`, `CROSS JOIN`, `INNER JOIN`, `OUTER JOIN`, `NATURAL JOIN`, `SELF JOIN`.
    - Record both the join type and the join keys.
    - Example: ["orders INNER JOIN customers ON orders.customer_id = customers.id"]

4. List all NECESSARY columns that appear in the provided schema.  
    - **IMPORTANT** DO NOT output derived columns like `COUNT(order_id)` or bare column names.
    - Express each column in fully-qualified `table.column` form.
    - Include all columns in `WHERE`, `SELECT`, `ORDER BY`, `HAVING`, and `GROUP BY` clauses, except for those in ON clause.
    - For ambiguous questions, include only the minimal column(s) needed.
        - for "Which/What <Entity>?" query, return either id or name (not both).
    - If all columns of one table are required, use `table.*`.

5. List NECESSARY functions that the query MUST call in the SELECT clause.
    - **IMPORTANT** IGNORE any functions that appear in WHERE, ORDER BY, GROUP BY, or HAVING clauses.
    - Include aggregate, window, and string functions.
    - COUNT, SUM, AVG, MAX, MIN, RANK(), DENSE_RANK(), SUBSTR
    - If a function is embedded in an arithmetic or concatenation expression, record the entire expression.
    - Example: ["COUNT(customer_id)", "SUM(amount)/COUNT(order_id)", "RANK() OVER (ORDER BY sales DESC)"]

6. List NECESSARY row-level filters or limits STRICTLY REQUIRED to answer the question.  
    - Consider `WHERE`, `ORDER BY`, `LIMIT/FETCH FIRST`, `OFFSET`, `NULLS FIRST`, `NULLS LAST`.
    - For sub-query predicates such as `EXISTS`, `NOT EXISTS` or `IN`, include the entire predicate.
    - Example: ["ORDER BY orders.order_date DESC", "LIMIT 1", "WHERE orders.total_amount > 100"]

7. List each NECESSARY `GROUP BY` clause STRICTLY REQUIRED to answer the question.
    - Example: ["GROUP BY customer_id"]

8. List NECESSARY group-level filters in `HAVING` clause STRICTLY REQUIRED to answer the question.
    - Example: ["HAVING SUM(assignments.hours_worked) > 500"]

9. List columns the user REQUIRES to have unique values.
    - **IMPORTANT** ONLY focus on keywords like "unique" or "distinct" in the question.
    - Answer in natural language.
    - Example: ["user requires orders.email to be unique"]
    
10. List EXPLICITLY or IMPLICITLY REQUIRED output format details.
    - **IMPORTANT** ONLY focus on the clause between `SELECT` and `FROM`.
    - Consider clear formatting instructions, such as rounding to a specific decimal place.
    - Identify implied formatting, like representing ratios or percentages as floats.
    - Answer in concise natural language.
    - Example: ["ratio should be represented as float", "output should contain 2 decimal places"]

###### CHECKLIST END

###### EXAMPLE1:
### SCHEMA
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total_amount DECIMAL
);

### QUESTION
"Which customers made orders over $1000?"

### BACKGROUND
""

### GOLD_SQL
SELECT customers.first_name, customers.last_name 
FROM customers
INNER JOIN orders ON customers.customer_id = orders.customer_id
WHERE orders.total_amount > 1000;

### ANSWER (single JSON array):
```json
[
  {{
    "question_id": "1",
    "answer": "NA"
  }},
  {{
    "question_id": "2",
    "answer": ["customers", "orders"]
  }},
  {{
    "question_id": "3",
    "answer": ["customers INNER JOIN orders ON customers.customer_id = orders.customer_id"]
  }},
  {{
    "question_id": "4",
    "answer": ["customers.first_name", "customers.last_name", "orders.total_amount"]
  }},
  {{
    "question_id": "5",
    "answer": "NA"
  }},
  {{
    "question_id": "6",
    "answer": ["WHERE orders.total_amount > 1000"]
  }},
  {{
    "question_id": "7",
    "answer": "NA"
  }},
  {{
    "question_id": "8",
    "answer": "NA"
  }},
  {{
    "question_id": "9",
    "answer": "NA"
  }},
  {{
    "question_id": "10",
    "answer": "NA"
  }}
]
```

###### EXAMPLE2:
### SCHEMA
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT,
    department_id INTEGER,
    salary DECIMAL
);

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name TEXT,
    department_id INTEGER
);

CREATE TABLE assignments (
    assignment_id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    project_id INTEGER,
    hours_worked INTEGER
);

CREATE TABLE performance_reviews (
    review_id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    review_date DATE,
    performance_score DECIMAL
);

### QUESTION
"How many employees in the 'Engineering' department have worked on projects with a total of over 500 hours, have received performance reviews in at least 3 different months, and whose total salary exceeds $100,000?"

### BACKGROUND
"Total hours worked is SUM(assignments.hours_worked). Distinct review months are counted using strftime('%Y-%m', performance_reviews.review_date)"

### GOLD_SQL
SELECT COUNT(DISTINCT employees.employee_id) FROM employees INNER JOIN departments ON employees.department_id = departments.department_id INNER JOIN assignments ON employees.employee_id = assignments.employee_id INNER JOIN projects ON assignments.project_id = projects.project_id INNER JOIN performance_reviews ON employees.employee_id = performance_reviews.employee_id WHERE departments.department_name = 'Engineering' GROUP BY employees.employee_id HAVING SUM(assignments.hours_worked) > 500 AND COUNT(DISTINCT strftime('%Y-%m', performance_reviews.review_date)) >= 3 AND SUM(employees.salary) > 100000;

### ANSWER:
```json
[
  {{
    "question_id": "1",
    "answer": "NA"
  }},
  {{
    "question_id": "2",
    "answer": ["employees", "departments", "projects", "assignments", "performance_reviews"]
  }},
  {{
    "question_id": "3",
    "answer": [
      "employees INNER JOIN departments ON employees.department_id = departments.department_id",
      "employees INNER JOIN assignments ON employees.employee_id = assignments.employee_id",
      "assignments INNER JOIN projects ON assignments.project_id = projects.project_id",
      "employees INNER JOIN performance_reviews ON employees.employee_id = performance_reviews.employee_id"
    ]
  }},
  {{
    "question_id": "4",
    "answer": ["employees.employee_id", "departments.department_name", "assignments.hours_worked", "performance_reviews.review_date", "employees.salary"]
  }},
  {{
    "question_id": "5",
    "answer": ["COUNT(DISTINCT employees.employee_id)"]
  }},
  {{
    "question_id": "6",
    "answer": ["WHERE departments.department_name = 'Engineering'"]
  }},
  {{
    "question_id": "7",
    "answer": ["GROUP BY employees.employee_id"]
  }},
  {{
    "question_id": "8",
    "answer": ["HAVING SUM(assignments.hours_worked) > 500", "HAVING COUNT(DISTINCT strftime('%Y-%m', performance_reviews.review_date)) >= 3", "HAVING SUM(employees.salary) > 100000"]
  }},
  {{
    "question_id": "9",
    "answer": "NA"
  }},
  {{
    "question_id": "10",
    "answer": "NA"
  }}
]
```

###### For you to answer:
### SCHEMA
{schema}

### QUESTION
{question}

### BACKGROUND
{evidence}

### GOLD_SQL
{gold_sql}

### ANSWER:
""".strip()
