#!/usr/bin/env python3
# test_rule_checker_hr.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SQLGlotEval import SQLGlotEval
from rich import print

if __name__ == "__main__":
    # 新 schema：人力资源（HR）-相关 5 张表
    schema = {
        "employees":  ["emp_id", "first_name", "last_name", "dept_id", "hire_date", "salary"],
        "departments": ["dept_id", "dept_name", "location"],
        "projects":   ["proj_id", "proj_name", "dept_id", "budget"],
        "assignments": ["emp_id", "proj_id", "role", "hours_per_week"],
        "locations":  ["location", "country"],
    }

    # 测试用例
    test_cases = [
        # 1. 单表：SELECT 列顺序交换
        ("SELECT first_name, last_name FROM employees",
         "SELECT last_name, first_name FROM employees",
         True),

        # 2. 单表：COUNT(*) 等价
        ("SELECT COUNT(*) FROM projects",
         "SELECT COUNT(1) FROM projects",
         True),

        # 3. DISTINCT vs GROUP BY
        ("SELECT DISTINCT dept_id FROM employees",
         "SELECT dept_id FROM employees GROUP BY dept_id",
         True),

        # 4. 别名 & 前缀差异
        ("SELECT e.salary FROM employees AS e",
         "SELECT employees.salary FROM employees",
         True),

        # 5. ORDER BY 影响结果
        ("SELECT salary FROM employees ORDER BY hire_date",
         "SELECT salary FROM employees",
         False),

        # 6. GROUP BY + 列别名引用
        ("SELECT dept_id AS d, AVG(salary) FROM employees GROUP BY d",
         "SELECT dept_id, AVG(salary) FROM employees GROUP BY dept_id",
         True),

        # 7. WHERE 边界差  (= / <>)
        ("SELECT * FROM departments WHERE location = 'NYC'",
         "SELECT * FROM departments WHERE location <> 'NYC'",
         False),

        # 8. 多列顺序 + 交换
        ("SELECT proj_id, dept_id, budget FROM projects",
         "SELECT budget, proj_id, dept_id FROM projects",
         True),

        # 9. 内连接顺序交换 & 列顺序交换
        ("""
         SELECT d.dept_name, e.first_name
         FROM departments d
         JOIN employees e ON d.dept_id = e.dept_id
         """,
         """
         SELECT e.first_name, d.dept_name
         FROM employees e
         JOIN departments d ON e.dept_id = d.dept_id
         """,
         True),

        # 10. CTE 展开
        ("""
         WITH high_budget AS (SELECT proj_id, budget FROM projects WHERE budget > 100000)
         SELECT proj_id FROM high_budget
         """,
         "SELECT proj_id FROM projects WHERE budget > 100000",
         True),

        # 11. 子查询展开
        ("SELECT * FROM (SELECT * FROM locations) l", "SELECT * FROM locations", True),

        # 12. AND 交换 + 别名混用
        ("SELECT first_name FROM employees WHERE salary > 50000 AND dept_id = 10",
         "SELECT first_name FROM employees WHERE dept_id = 10 AND salary > 50000",
         True),
    ]

    # 追加到 test_cases 列表即可
    more_false_positive_cases = [ 
        # 14. 不同表同名列：employees.dept_id vs departments.dept_id
        ("""
        SELECT dept_id FROM employees
        """,
        """
        SELECT dept_id FROM departments
        """,
        False),  

        # 15. LEFT JOIN 替换成 INNER JOIN
        ("""
        SELECT d.dept_name, e.first_name
        FROM departments d
        LEFT JOIN employees e ON d.dept_id = e.dept_id
        """,
        """
        SELECT d.dept_name, e.first_name
        FROM departments d
        JOIN employees e ON d.dept_id = e.dept_id
        """,
        False),  

        # 16. COUNT(*) vs COUNT(DISTINCT dept_id)
        ("SELECT COUNT(*) FROM employees",
        "SELECT COUNT(DISTINCT dept_id) FROM employees",
        False),

        # 17. SELECT DISTINCT 与非 DISTINCT
        ("SELECT DISTINCT role FROM assignments",
        "SELECT role FROM assignments",
        False),  

        # 18. GROUP BY 列误删
        ("SELECT dept_id, AVG(salary) FROM employees GROUP BY dept_id",
        "SELECT AVG(salary) FROM employees",
        False),  

        # 19. 边界条件 > 与 >=
        ("SELECT * FROM projects WHERE budget > 100000",
        "SELECT * FROM projects WHERE budget >= 100000",
        False),

        # 20. LIMIT 子句
        ("SELECT first_name FROM employees ORDER BY hire_date LIMIT 5",
        "SELECT first_name FROM employees ORDER BY hire_date",
        False), 

        # 21. NULL 与 0 混淆
        ("SELECT * FROM employees WHERE salary IS NULL",
        "SELECT * FROM employees WHERE salary = 0",
        False),

        # 22. 两步 JOIN 顺序 + JOIN 类型变化
        ("""
        SELECT p.proj_name, e.first_name
        FROM projects p
        JOIN assignments a  ON p.proj_id = a.proj_id
        LEFT JOIN employees  e ON a.emp_id = e.emp_id
        """,
        """
        SELECT p.proj_name, e.first_name
        FROM employees  e
        JOIN assignments a  ON e.emp_id = a.emp_id
        JOIN projects    p  ON a.proj_id = p.proj_id
        """,
        False),  
    ]
    test_cases.extend(more_false_positive_cases)


    passed = 0
    for i, (gt_sql, pred_sql, expected) in enumerate(test_cases, 1):
        result = SQLGlotEval(schema, gt_sql, pred_sql)
        status = "[green]PASS[/green]" if result == expected else "[red]FAIL[/red]"
        print(f"[{status}] Test case {i}: expected={expected}, got={result}")
        if result == expected:
            passed += 1

    print(f"\n[bold]Passed {passed}/{len(test_cases)} test cases.[/bold]")


