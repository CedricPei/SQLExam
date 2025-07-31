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
- When extracting predicates from GOLD_SQL, use the exact original text. Do not combine or use your own words.
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
**IMPORTANT** Treat GOLD_SQL AS REFERENCE ONLY, ignore any operation it contains that the user did not request (e.g., extra aliases or formatting).

**CRITICAL FOR COMPLEX QUERIES** 
If the SQL query contains multiple independent SELECT structures, analyze EACH independent SELECT structure separately and combine all requirements. 
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
    - If GROUP BY contains multiple fields, list them all.
    - Example: ["GROUP BY customer_id, order_year"]

6. List NECESSARY group-level filters in `HAVING` clause STRICTLY REQUIRED to answer the question.
    - Use the exact HAVING clause text from GOLD_SQL. Do not combine or split predicates.
    - **CRITICAL**: If multiple predicates are joined by `AND` or `OR`, output each predicate as a separate element while preserving the connector and order.
    - Example: ["HAVING SUM(bonuses.amount) > 20000", "AND COUNT(*) >= 3"]

7. List NECESSARY row-level filters or limits STRICTLY REQUIRED to answer the question.
    - **ONLY** Consider `ON`, `WHERE`, `ORDER BY`, `LIMIT/FETCH FIRST`, `OFFSET`, `NULLS FIRST`, `NULLS LAST` clauses.
    - NEVER include `HAVING` or `GROUP BY` clauses here - they belong to points 5 and 6 respectively.
    - **CRITICAL** Break composite predicates into individual field-level conditions; each element should reference exactly one column/field.
    - Ignore conditions for table connections and predicates like `ORDER BY` inside window functions like `RANK()`.
    - For sub-query predicates such as `EXISTS`, `NOT EXISTS` or `IN`, only include conditions inside.
    - Example: ["WHERE orders.total_amount > 100", "AND orders.status = 'paid'", "ORDER BY orders.order_date DESC", "LIMIT 1"]

8. List columns the user REQUIRES to have unique values.
    - **IMPORTANT** ONLY focus on keywords like "unique" or "distinct" in the question.
    - Answer in concise natural language.
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
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    employment_type TEXT
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    status TEXT
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    project_id INTEGER,
    hours_worked INTEGER
);

### QUESTION
Which full-time Engineering employees have logged over 500 hours on active projects and worked on at least 3 such projects?
Show each employee's name and the ratio of total hours worked to the number of active projects they joined, sorted from highest ratio to lowest.

### BACKGROUND
Only projects with status 'Active' count.

### GOLD_SQL
SELECT
    e.name,
    SUM(a.hours_worked) / COUNT(DISTINCT a.project_id) AS hours_per_project
FROM employees AS e
JOIN assignments AS a ON a.employee_id = e.id
WHERE e.department = 'Engineering'
  AND e.employment_type = 'Full-Time'
  AND a.project_id IN (
        SELECT p.id
        FROM projects AS p
        WHERE p.status = 'Active'
    )
GROUP BY e.id
HAVING SUM(a.hours_worked) > 500
   AND COUNT(DISTINCT a.project_id) >= 3
ORDER BY hours_per_project DESC;

### ANSWER (single JSON array):
```json
[
  {{
    "question_id": "1",
    "answer": ["employees", "assignments", "projects"]
  }},
  {{
    "question_id": "2",
    "answer": "NA"
  }},
  {{
    "question_id": "3",
    "answer": [
      "employees.name",
      "employees.department",
      "employees.employment_type",
      "assignments.hours_worked",
      "assignments.project_id",
      "projects.id",
      "projects.status"
    ]
  }},
  {{
    "question_id": "4",
    "answer": ["SUM(assignments.hours_worked)/COUNT(DISTINCT assignments.project_id)"]
  }},
  {{
    "question_id": "5",
    "answer": ["GROUP BY employees.id"]
  }},
  {{
    "question_id": "6",
    "answer": [
      "HAVING SUM(assignments.hours_worked) > 500",
      "AND COUNT(DISTINCT assignments.project_id) >= 3",
    ]
  }},
  {{
    "question_id": "7",
    "answer": [
      "WHERE employees.department = 'Engineering'",
      "AND employees.employment_type = 'Full-Time'",
      "WHERE projects.status = 'Active'",
      "ORDER BY hours_per_project DESC"
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
List the top 3 actors who have appeared in the most movies directed by 'Christopher Nolan' and have acted in at least 4 of those movies.
Show each actor's name and the number of such movies.

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
