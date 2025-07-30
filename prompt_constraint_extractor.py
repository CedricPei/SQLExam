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
- When extracting predicates from GOLD_SQL, use the exact original text. Do not combine, modify or use your own words.
- One object per atomic requirement; no missing question_ids.  
- Keep answers concise; use arrays when multiple values apply.  
- Never add extra keys or change key names.
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

**CRITICAL FOR COMPLEX QUERIES**: If the SQL query contains multiple independent SELECT structures, analyze EACH independent SELECT structure separately and combine all requirements. Do not focus only on the main SELECT structure. For example:
- If there's a subquery in WHERE clause, analyze both the main query AND the subquery
- If there are CTEs (WITH clauses), analyze each CTE separately
- If there are UNION or EXCEPT clauses, analyze each SELECT in the UNION/EXCEPT separately
- Combine all tables, joins, columns, etc. from ALL independent SELECT structures

After completing all items, aggregate the objects into a **single JSON array** and enclose it in a markdown code block that begins with ```json.  

######  CHECKLIST BEGIN
1. List NECESSARY tables the answer MUST reference and that MUST appear in the provided schema.

2. List each NECESSARY and special join that is STRICTLY REQUIRED to answer the question.
    - Only include joins other than INNER JOIN / JOIN (e.g., LEFT, RIGHT, FULL, CROSS, NATURAL, SELF, OUTER).
    - Provide the pair and join type in the form "A LEFT JOIN B".
    - Do NOT include ON-clause details.

3. List all NECESSARY columns that appear in the provided schema.
    - **IMPORTANT** DO NOT output derived columns like `COUNT(order_id)` or bare column names.
    - Express each column in fully-qualified `table.column` form.
    - Exclude columns for table connections; include only columns meaningful to answer the question.
    - If all columns of one table are required, use `table.*`.

4. List NECESSARY functions that the query MUST call in the SELECT clause.
    - **IMPORTANT** IGNORE any functions that appear in WHERE, ORDER BY, GROUP BY, or HAVING clauses.
    - Include aggregate, window, and string functions.
    - COUNT, SUM, AVG, MAX, MIN, RANK(), DENSE_RANK(), SUBSTR
    - If a function is embedded in an arithmetic or concatenation expression, record the entire expression.
    - Example: ["COUNT(customer_id)", "SUM(amount)/COUNT(order_id)", "RANK() OVER (ORDER BY sales DESC)"]

5. List each NECESSARY `GROUP BY` clause STRICTLY REQUIRED to answer the question.
    - **ONLY** include GROUP BY clauses here, not in point 6 or 7.
    - If GROUP BY contains multiple fields, list them all.
    - Example: ["GROUP BY customer_id, order_year"]

6. List NECESSARY group-level filters in `HAVING` clause STRICTLY REQUIRED to answer the question.
    - **ONLY** include HAVING clauses here, not in point 5 or 7.
    - Use the exact HAVING clause text from GOLD_SQL. Do not combine or split predicates.
    - **CRITICAL**: If you see `HAVING A AND B AND C`, output it as one item: `["HAVING A AND B AND C"]`, NOT as separate items.
    - Example: ["HAVING SUM(assignments.hours_worked) > 500"]

7. List NECESSARY row-level filters or limits STRICTLY REQUIRED to answer the question.
    - **ONLY** Consider `ON`, `WHERE`, `ORDER BY`, `LIMIT/FETCH FIRST`, `OFFSET`, `NULLS FIRST`, `NULLS LAST` clauses.
    - **CRITICAL** NEVER include `HAVING` or `GROUP BY` clauses here - they belong to points 5 and 6 respectively.
    - **IMPORTANT** Ignore conditions for table connections and predicates like `ORDER BY` inside window functions like `RANK()`.
    - **CRITICAL** Treat a compound predicate as one item, do not split it. Keep the entire predicate together.  
    - For sub-query predicates such as `EXISTS`, `NOT EXISTS` or `IN`, include the entire predicate.
    - Example: ["WHERE orders.total_amount > 100 AND orders.status = 'paid'", "ORDER BY orders.order_date DESC", "LIMIT 1"]

8. List columns the user REQUIRES to have unique values.
    - **IMPORTANT** ONLY focus on keywords like "unique" or "distinct" in the question.
    - Answer in natural language.
    - Example: ["user requires email to be unique"]
    
9. List EXPLICITLY or IMPLICITLY REQUIRED output format details.
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
SELECT
    customers.first_name,
    customers.last_name
FROM customers
INNER JOIN orders
    ON customers.customer_id = orders.customer_id
WHERE orders.total_amount > 1000;

### ANSWER (single JSON array):
```json
[
  {{
    "question_id": "1",
    "answer": ["customers", "orders"]
  }},
  {{
    "question_id": "2",
    "answer": "NA"
  }},
  {{
    "question_id": "3",
    "answer": ["customers.first_name", "customers.last_name", "orders.total_amount"]
  }},
  {{
    "question_id": "4",
    "answer": "NA"
  }},
  {{
    "question_id": "5",
    "answer": "NA"
  }},
  {{
    "question_id": "6",
    "answer": "NA"
  }},
  {{
    "question_id": "7",
    "answer": ["WHERE orders.total_amount > 1000"]
  }},
  {{
    "question_id": "8",
    "answer": "NA"
  }},
  {{
    "question_id": "9",
    "answer": "NA"
  }}
]
```

###### EXAMPLE2:
### SCHEMA
CREATE TABLE actors (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title TEXT,
    director TEXT,
    release_year INTEGER
);

CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    actor_id INTEGER,
    movie_id INTEGER
);

### QUESTION
List the top 3 actors who have appeared in the most movies directed by 'Christopher Nolan' and have acted in at least 4 of those movies. Show each actor's name and the number of such movies.

### BACKGROUND
Count appearances across roles where movies.director = 'Christopher Nolan'.

### GOLD_SQL
SELECT a.name,
       COUNT(*) AS movie_count
FROM actors AS a
JOIN roles AS r ON r.actor_id = a.id
JOIN movies AS m ON m.id = r.movie_id
WHERE m.director = 'Christopher Nolan'
GROUP BY a.id
HAVING COUNT(*) >= 4
ORDER BY movie_count DESC
LIMIT 3;

### ANSWER:
```json
[
  {{
    "question_id": "1",
    "answer": ["actors", "roles", "movies"]
  }},
  {{
    "question_id": "2",
    "answer": "NA"
  }},
  {{
    "question_id": "3",
    "answer": ["actors.name", "movies.director"]
  }},
  {{
    "question_id": "4",
    "answer": ["COUNT(*)"]
  }},
  {{
    "question_id": "5",
    "answer": ["GROUP BY actors.id"]
  }},
  {{
    "question_id": "6",
    "answer": ["HAVING COUNT(*) >= 4"]
  }},
  {{
    "question_id": "7",
    "answer": [
      "WHERE movies.director = 'Christopher Nolan'",
      "ORDER BY movie_count DESC",
      "LIMIT 3"
    ]
  }},
  {{
    "question_id": "8",
    "answer": "NA"
  }},
  {{
    "question_id": "9",
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
