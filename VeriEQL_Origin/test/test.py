# -*- coding:utf-8 -*-
from z3 import *
import itertools
import functools

sql1 = "SELECT S.CUSTOMERKEY FROM SALES AS S"
sql2 = "SELECT S.CUSTOMERKEY+1 FROM SALES AS S WHERE EXISTS (SELECT SALES.CUSTOMERKEY FROM CUSTOMER JOIN SALES ON CUSTOMER.CUSTOMERKEY = SALES.CUSTOMERKEY WHERE SALES.CUSTOMERKEY != S.CUSTOMERKEY)"

# define z3 Sorts
__TupleSort = DeclareSort("TupleSort")  # define `Tuple` sort
__Int = IntSort()  # define `Int` sort
__String = StringSort()  # define `String` sort
__Boolean = BoolSort()  # define `Boolean` sort

# Special functions
DELETED = Function("DELETED", __TupleSort, __Boolean)  # define `DELETE` function to represent a tuple does not exist; Not(DELETE) means the existence of a tuple
NULL = Function("NULL", __TupleSort, __String, __Boolean)  # define `NULL` function
COUNT = Function("COUNT", __TupleSort, __String, __Int)  # define `COUNT` function
MAX = Function("MAX", __TupleSort, __String, __Int)  # define `MAX` function
MIN = Function("MIN", __TupleSort, __String, __Int)  # define `MIN` function
AVG = Function("AVG", __TupleSort, __String, __Int)  # define `AVG` function
SUM = Function("SUM", __TupleSort, __String, __Int)  # define `SUM` function
ROUND = Function("ROUND", __Int, __Int, __Int, __Int)  # define `ROUND` (uninterpreted) function
CUSTOMER__CUSTOMERKEY = Function('CUSTOMER__CUSTOMERKEY', __TupleSort, __Int)  # define `CUSTOMER__CUSTOMERKEY` function to retrieve columns of tuples
SALES__CUSTOMERKEY = Function('SALES__CUSTOMERKEY', __TupleSort, __Int)  # define `SALES__CUSTOMERKEY` function to retrieve columns of tuples
SALES__ORDERDATEKEY = Function('SALES__ORDERDATEKEY', __TupleSort, __Int)  # define `SALES__ORDERDATEKEY` function to retrieve columns of tuples
SALES__SHIPDATE = Function('SALES__SHIPDATE', __TupleSort, __Int)  # define `SALES__SHIPDATE` function to retrieve columns of tuples
SALES__DUEDATE = Function('SALES__DUEDATE', __TupleSort, __Int)  # define `SALES__DUEDATE` function to retrieve columns of tuples
DATE__DATEKEY = Function('DATE__DATEKEY', __TupleSort, __Int)  # define `DATE__DATEKEY` function to retrieve columns of tuples
TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1 = Function('TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1', __TupleSort, __Int)  # define `TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1` function to retrieve columns of tuples

# Special Variables
NULL_VALUE = Const('NULL_VALUE', __Int)  # define NULL variable
POS_INF__Int = Const('POS_INF__Int', __Int)  # define +INF variable
NEG_INF__Int = Const('NEG_INF__Int', __Int)  # define -INF variable
COUNT_ALL__String = Const(f"COUNT_ALL__String", __String)  # define `COUNT(*)`
t1 = Const('t1', __TupleSort)  # define a tuple `t1`
CUSTOMER__CUSTOMERKEY__String = Const('CUSTOMER__CUSTOMERKEY__String', __String)  # define `CUSTOMER__CUSTOMERKEY__String` for NULL function
String_x1__Int = Const('String_x1__Int', __Int)  # define `String_x1__Int` for NULL function
t2 = Const('t2', __TupleSort)  # define a tuple `t2`
String_x2__Int = Const('String_x2__Int', __Int)  # define `String_x2__Int` for NULL function
t3 = Const('t3', __TupleSort)  # define a tuple `t3`
SALES__CUSTOMERKEY__String = Const('SALES__CUSTOMERKEY__String', __String)  # define `SALES__CUSTOMERKEY__String` for NULL function
String_x3__Int = Const('String_x3__Int', __Int)  # define `String_x3__Int` for NULL function
SALES__ORDERDATEKEY__String = Const('SALES__ORDERDATEKEY__String', __String)  # define `SALES__ORDERDATEKEY__String` for NULL function
String_x4__Int = Const('String_x4__Int', __Int)  # define `String_x4__Int` for NULL function
SALES__SHIPDATE__String = Const('SALES__SHIPDATE__String', __String)  # define `SALES__SHIPDATE__String` for NULL function
String_x5__Int = Const('String_x5__Int', __Int)  # define `String_x5__Int` for NULL function
SALES__DUEDATE__String = Const('SALES__DUEDATE__String', __String)  # define `SALES__DUEDATE__String` for NULL function
String_x6__Int = Const('String_x6__Int', __Int)  # define `String_x6__Int` for NULL function
t4 = Const('t4', __TupleSort)  # define a tuple `t4`
String_x7__Int = Const('String_x7__Int', __Int)  # define `String_x7__Int` for NULL function
String_x8__Int = Const('String_x8__Int', __Int)  # define `String_x8__Int` for NULL function
String_x9__Int = Const('String_x9__Int', __Int)  # define `String_x9__Int` for NULL function
String_x10__Int = Const('String_x10__Int', __Int)  # define `String_x10__Int` for NULL function
t5 = Const('t5', __TupleSort)  # define a tuple `t5`
DATE__DATEKEY__String = Const('DATE__DATEKEY__String', __String)  # define `DATE__DATEKEY__String` for NULL function
String_x11__Int = Const('String_x11__Int', __Int)  # define `String_x11__Int` for NULL function
t6 = Const('t6', __TupleSort)  # define a tuple `t6`
String_x12__Int = Const('String_x12__Int', __Int)  # define `String_x12__Int` for NULL function
t9 = Const('t9', __TupleSort)  # define a tuple `t9`
t10 = Const('t10', __TupleSort)  # define a tuple `t10`
t11 = Const('t11', __TupleSort)  # define a tuple `t11`
t12 = Const('t12', __TupleSort)  # define a tuple `t12`
t13 = Const('t13', __TupleSort)  # define a tuple `t13`
t14 = Const('t14', __TupleSort)  # define a tuple `t14`
t15 = Const('t15', __TupleSort)  # define a tuple `t15`
t16 = Const('t16', __TupleSort)  # define a tuple `t16`
t17 = Const('t17', __TupleSort)  # define a tuple `t17`
t18 = Const('t18', __TupleSort)  # define a tuple `t18`
t19 = Const('t19', __TupleSort)  # define a tuple `t19`
t20 = Const('t20', __TupleSort)  # define a tuple `t20`
t25 = Const('t25', __TupleSort)  # define a tuple `t25`
t26 = Const('t26', __TupleSort)  # define a tuple `t26`
TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String = Const('TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String', __String)  # define `TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String` for NULL function
t27 = Const('t27', __TupleSort)  # define a tuple `t27`
t28 = Const('t28', __TupleSort)  # define a tuple `t28`
t25_0 = Const('t25_0', __TupleSort)  # define a tuple `t25_0`
t26_0 = Const('t26_0', __TupleSort)  # define a tuple `t26_0`
t17_0 = Const('t17_0', __TupleSort)  # define a tuple `t17_0`
t18_0 = Const('t18_0', __TupleSort)  # define a tuple `t18_0`
t19_0 = Const('t19_0', __TupleSort)  # define a tuple `t19_0`
t20_0 = Const('t20_0', __TupleSort)  # define a tuple `t20_0`
t21_0 = Const('t21_0', __TupleSort)  # define a tuple `t21_0`
t22_0 = Const('t22_0', __TupleSort)  # define a tuple `t22_0`
t23_0 = Const('t23_0', __TupleSort)  # define a tuple `t23_0`
t24_0 = Const('t24_0', __TupleSort)  # define a tuple `t24_0`
t17_1 = Const('t17_1', __TupleSort)  # define a tuple `t17_1`
t18_1 = Const('t18_1', __TupleSort)  # define a tuple `t18_1`
t19_1 = Const('t19_1', __TupleSort)  # define a tuple `t19_1`
t20_1 = Const('t20_1', __TupleSort)  # define a tuple `t20_1`
t21_1 = Const('t21_1', __TupleSort)  # define a tuple `t21_1`
t22_1 = Const('t22_1', __TupleSort)  # define a tuple `t22_1`
t23_1 = Const('t23_1', __TupleSort)  # define a tuple `t23_1`
t24_1 = Const('t24_1', __TupleSort)  # define a tuple `t24_1`

def _MAX(*args):
    return functools.reduce(lambda x, y: If(x >= y, x, y), args)


def _MIN(*args):
    return functools.reduce(lambda x, y: If(x < y, x, y), args)

DBMS_facts = And(
# Database tuples
Not(DELETED(t1)),
CUSTOMER__CUSTOMERKEY(t1) == String_x1__Int,
Not(DELETED(t2)),
CUSTOMER__CUSTOMERKEY(t2) == String_x2__Int,
-2147483648 <= CUSTOMER__CUSTOMERKEY(t1),
2147483647 >= CUSTOMER__CUSTOMERKEY(t1),
-2147483648 <= CUSTOMER__CUSTOMERKEY(t2),
2147483647 >= CUSTOMER__CUSTOMERKEY(t2),
Not(DELETED(t3)),
SALES__CUSTOMERKEY(t3) == String_x3__Int,
SALES__ORDERDATEKEY(t3) == String_x4__Int,
SALES__SHIPDATE(t3) == String_x5__Int,
SALES__DUEDATE(t3) == String_x6__Int,
Not(DELETED(t4)),
SALES__CUSTOMERKEY(t4) == String_x7__Int,
SALES__ORDERDATEKEY(t4) == String_x8__Int,
SALES__SHIPDATE(t4) == String_x9__Int,
SALES__DUEDATE(t4) == String_x10__Int,
-2147483648 <= SALES__CUSTOMERKEY(t3),
2147483647 >= SALES__CUSTOMERKEY(t3),
-2147483648 <= SALES__ORDERDATEKEY(t3),
2147483647 >= SALES__ORDERDATEKEY(t3),
1 <= SALES__SHIPDATE(t3),
2932897 >= SALES__SHIPDATE(t3),
1 <= SALES__DUEDATE(t3),
2932897 >= SALES__DUEDATE(t3),
-2147483648 <= SALES__CUSTOMERKEY(t4),
2147483647 >= SALES__CUSTOMERKEY(t4),
-2147483648 <= SALES__ORDERDATEKEY(t4),
2147483647 >= SALES__ORDERDATEKEY(t4),
1 <= SALES__SHIPDATE(t4),
2932897 >= SALES__SHIPDATE(t4),
1 <= SALES__DUEDATE(t4),
2932897 >= SALES__DUEDATE(t4),
Not(DELETED(t5)),
DATE__DATEKEY(t5) == String_x11__Int,
Not(DELETED(t6)),
DATE__DATEKEY(t6) == String_x12__Int,
-2147483648 <= DATE__DATEKEY(t5),
2147483647 >= DATE__DATEKEY(t5),
-2147483648 <= DATE__DATEKEY(t6),
2147483647 >= DATE__DATEKEY(t6),
And(Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
    Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
    CUSTOMER__CUSTOMERKEY(t1) != CUSTOMER__CUSTOMERKEY(t2)),
And(Not(NULL(t3, SALES__CUSTOMERKEY__String)),
    Not(NULL(t4, SALES__CUSTOMERKEY__String)),
    Not(NULL(t3, SALES__ORDERDATEKEY__String)),
    Not(NULL(t4, SALES__ORDERDATEKEY__String)),
    Not(And(SALES__CUSTOMERKEY(t3) == SALES__CUSTOMERKEY(t4),
            SALES__ORDERDATEKEY(t3) ==
            SALES__ORDERDATEKEY(t4)))),
And(Not(NULL(t5, DATE__DATEKEY__String)),
    Not(NULL(t6, DATE__DATEKEY__String)),
    DATE__DATEKEY(t5) != DATE__DATEKEY(t6)),
And(Or(And(Not(NULL(t3, SALES__CUSTOMERKEY__String)),
           Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
           SALES__CUSTOMERKEY(t3) ==
           CUSTOMER__CUSTOMERKEY(t1)),
       And(Not(NULL(t3, SALES__CUSTOMERKEY__String)),
           Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
           SALES__CUSTOMERKEY(t3) ==
           CUSTOMER__CUSTOMERKEY(t2))),
    Or(And(Not(NULL(t4, SALES__CUSTOMERKEY__String)),
           Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
           SALES__CUSTOMERKEY(t4) ==
           CUSTOMER__CUSTOMERKEY(t1)),
       And(Not(NULL(t4, SALES__CUSTOMERKEY__String)),
           Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
           SALES__CUSTOMERKEY(t4) ==
           CUSTOMER__CUSTOMERKEY(t2)))),
And(Or(And(Not(NULL(t3, SALES__ORDERDATEKEY__String)),
           Not(NULL(t5, DATE__DATEKEY__String)),
           SALES__ORDERDATEKEY(t3) == DATE__DATEKEY(t5)),
       And(Not(NULL(t3, SALES__ORDERDATEKEY__String)),
           Not(NULL(t6, DATE__DATEKEY__String)),
           SALES__ORDERDATEKEY(t3) == DATE__DATEKEY(t6))),
    Or(And(Not(NULL(t4, SALES__ORDERDATEKEY__String)),
           Not(NULL(t5, DATE__DATEKEY__String)),
           SALES__ORDERDATEKEY(t4) == DATE__DATEKEY(t5)),
       And(Not(NULL(t4, SALES__ORDERDATEKEY__String)),
           Not(NULL(t6, DATE__DATEKEY__String)),
           SALES__ORDERDATEKEY(t4) == DATE__DATEKEY(t6))))
)

premise1 = And(
# 1st SQL query formulas
True
)

premise2 = And(
# 2nd SQL query formulas
# t9 := InnerJoin(t1, t3, None)
And(
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t3))),
        And(
            Not(DELETED(t9)),
            And(NULL(t9, CUSTOMER__CUSTOMERKEY__String) ==
    NULL(t1, CUSTOMER__CUSTOMERKEY__String),
    CUSTOMER__CUSTOMERKEY(t9) == CUSTOMER__CUSTOMERKEY(t1)),
And(NULL(t9, SALES__CUSTOMERKEY__String) ==
    NULL(t3, SALES__CUSTOMERKEY__String),
    SALES__CUSTOMERKEY(t9) == SALES__CUSTOMERKEY(t3)),
And(NULL(t9, SALES__ORDERDATEKEY__String) ==
    NULL(t3, SALES__ORDERDATEKEY__String),
    SALES__ORDERDATEKEY(t9) == SALES__ORDERDATEKEY(t3)),
And(NULL(t9, SALES__SHIPDATE__String) ==
    NULL(t3, SALES__SHIPDATE__String),
    SALES__SHIPDATE(t9) == SALES__SHIPDATE(t3)),
And(NULL(t9, SALES__DUEDATE__String) ==
    NULL(t3, SALES__DUEDATE__String),
    SALES__DUEDATE(t9) == SALES__DUEDATE(t3)),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t3)))),
        DELETED(t9),
    ),
),

# t10 := InnerJoin(t2, t3, None)
And(
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t3))),
        And(
            Not(DELETED(t10)),
            And(NULL(t10, CUSTOMER__CUSTOMERKEY__String) ==
    NULL(t2, CUSTOMER__CUSTOMERKEY__String),
    CUSTOMER__CUSTOMERKEY(t10) == CUSTOMER__CUSTOMERKEY(t2)),
And(NULL(t10, SALES__CUSTOMERKEY__String) ==
    NULL(t3, SALES__CUSTOMERKEY__String),
    SALES__CUSTOMERKEY(t10) == SALES__CUSTOMERKEY(t3)),
And(NULL(t10, SALES__ORDERDATEKEY__String) ==
    NULL(t3, SALES__ORDERDATEKEY__String),
    SALES__ORDERDATEKEY(t10) == SALES__ORDERDATEKEY(t3)),
And(NULL(t10, SALES__SHIPDATE__String) ==
    NULL(t3, SALES__SHIPDATE__String),
    SALES__SHIPDATE(t10) == SALES__SHIPDATE(t3)),
And(NULL(t10, SALES__DUEDATE__String) ==
    NULL(t3, SALES__DUEDATE__String),
    SALES__DUEDATE(t10) == SALES__DUEDATE(t3)),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t3)))),
        DELETED(t10),
    ),
),

# t11 := InnerJoin(t1, t4, None)
And(
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t4))),
        And(
            Not(DELETED(t11)),
            And(NULL(t11, CUSTOMER__CUSTOMERKEY__String) ==
    NULL(t1, CUSTOMER__CUSTOMERKEY__String),
    CUSTOMER__CUSTOMERKEY(t11) == CUSTOMER__CUSTOMERKEY(t1)),
And(NULL(t11, SALES__CUSTOMERKEY__String) ==
    NULL(t4, SALES__CUSTOMERKEY__String),
    SALES__CUSTOMERKEY(t11) == SALES__CUSTOMERKEY(t4)),
And(NULL(t11, SALES__ORDERDATEKEY__String) ==
    NULL(t4, SALES__ORDERDATEKEY__String),
    SALES__ORDERDATEKEY(t11) == SALES__ORDERDATEKEY(t4)),
And(NULL(t11, SALES__SHIPDATE__String) ==
    NULL(t4, SALES__SHIPDATE__String),
    SALES__SHIPDATE(t11) == SALES__SHIPDATE(t4)),
And(NULL(t11, SALES__DUEDATE__String) ==
    NULL(t4, SALES__DUEDATE__String),
    SALES__DUEDATE(t11) == SALES__DUEDATE(t4)),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t4)))),
        DELETED(t11),
    ),
),

# t12 := InnerJoin(t2, t4, None)
And(
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t4))),
        And(
            Not(DELETED(t12)),
            And(NULL(t12, CUSTOMER__CUSTOMERKEY__String) ==
    NULL(t2, CUSTOMER__CUSTOMERKEY__String),
    CUSTOMER__CUSTOMERKEY(t12) == CUSTOMER__CUSTOMERKEY(t2)),
And(NULL(t12, SALES__CUSTOMERKEY__String) ==
    NULL(t4, SALES__CUSTOMERKEY__String),
    SALES__CUSTOMERKEY(t12) == SALES__CUSTOMERKEY(t4)),
And(NULL(t12, SALES__ORDERDATEKEY__String) ==
    NULL(t4, SALES__ORDERDATEKEY__String),
    SALES__ORDERDATEKEY(t12) == SALES__ORDERDATEKEY(t4)),
And(NULL(t12, SALES__SHIPDATE__String) ==
    NULL(t4, SALES__SHIPDATE__String),
    SALES__SHIPDATE(t12) == SALES__SHIPDATE(t4)),
And(NULL(t12, SALES__DUEDATE__String) ==
    NULL(t4, SALES__DUEDATE__String),
    SALES__DUEDATE(t12) == SALES__DUEDATE(t4)),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t4)))),
        DELETED(t12),
    ),
),

# t13 := Filter(['t9'], Cond=(eq_FExpressionTuple(NULL=NULL(t1, CUSTOMER__CUSTOMERKEY__String), VALUE=CUSTOMER__CUSTOMERKEY(t1))_FExpressionTuple(NULL=NULL(t3, SALES__CUSTOMERKEY__String), VALUE=SALES__CUSTOMERKEY(t3))))
And(
    Implies(
        And(*[Not(DELETED(t9)), If(Or(NULL(t1, CUSTOMER__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t1) == SALES__CUSTOMERKEY(t3)))]),
        And(Not(DELETED(t13)), t13 == t9),
    ),
    Implies(Not(And(*[Not(DELETED(t9)), If(Or(NULL(t1, CUSTOMER__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t1) == SALES__CUSTOMERKEY(t3)))])), DELETED(t13)),
),

# t14 := Filter(['t10'], Cond=(eq_FExpressionTuple(NULL=NULL(t2, CUSTOMER__CUSTOMERKEY__String), VALUE=CUSTOMER__CUSTOMERKEY(t2))_FExpressionTuple(NULL=NULL(t3, SALES__CUSTOMERKEY__String), VALUE=SALES__CUSTOMERKEY(t3))))
And(
    Implies(
        And(*[Not(DELETED(t10)), If(Or(NULL(t2, CUSTOMER__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t2) == SALES__CUSTOMERKEY(t3)))]),
        And(Not(DELETED(t14)), t14 == t10),
    ),
    Implies(Not(And(*[Not(DELETED(t10)), If(Or(NULL(t2, CUSTOMER__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t2) == SALES__CUSTOMERKEY(t3)))])), DELETED(t14)),
),

# t15 := Filter(['t11'], Cond=(eq_FExpressionTuple(NULL=NULL(t1, CUSTOMER__CUSTOMERKEY__String), VALUE=CUSTOMER__CUSTOMERKEY(t1))_FExpressionTuple(NULL=NULL(t4, SALES__CUSTOMERKEY__String), VALUE=SALES__CUSTOMERKEY(t4))))
And(
    Implies(
        And(*[Not(DELETED(t11)), If(Or(NULL(t1, CUSTOMER__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t1) == SALES__CUSTOMERKEY(t4)))]),
        And(Not(DELETED(t15)), t15 == t11),
    ),
    Implies(Not(And(*[Not(DELETED(t11)), If(Or(NULL(t1, CUSTOMER__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t1, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t1) == SALES__CUSTOMERKEY(t4)))])), DELETED(t15)),
),

# t16 := Filter(['t12'], Cond=(eq_FExpressionTuple(NULL=NULL(t2, CUSTOMER__CUSTOMERKEY__String), VALUE=CUSTOMER__CUSTOMERKEY(t2))_FExpressionTuple(NULL=NULL(t4, SALES__CUSTOMERKEY__String), VALUE=SALES__CUSTOMERKEY(t4))))
And(
    Implies(
        And(*[Not(DELETED(t12)), If(Or(NULL(t2, CUSTOMER__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t2) == SALES__CUSTOMERKEY(t4)))]),
        And(Not(DELETED(t16)), t16 == t12),
    ),
    Implies(Not(And(*[Not(DELETED(t12)), If(Or(NULL(t2, CUSTOMER__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t2, CUSTOMER__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       CUSTOMER__CUSTOMERKEY(t2) == SALES__CUSTOMERKEY(t4)))])), DELETED(t16)),
),

# t17_0 := Filter(['t13'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t13)), If(Or(NULL(t13, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t13, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t13) != SALES__CUSTOMERKEY(t3)))]),
        And(Not(DELETED(t17_0)), t17_0 == t13),
    ),
    Implies(Not(And(*[Not(DELETED(t13)), If(Or(NULL(t13, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t13, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t13) != SALES__CUSTOMERKEY(t3)))])), DELETED(t17_0)),
),

# t18_0 := Filter(['t14'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t14)), If(Or(NULL(t14, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t14, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t14) != SALES__CUSTOMERKEY(t3)))]),
        And(Not(DELETED(t18_0)), t18_0 == t14),
    ),
    Implies(Not(And(*[Not(DELETED(t14)), If(Or(NULL(t14, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t14, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t14) != SALES__CUSTOMERKEY(t3)))])), DELETED(t18_0)),
),

# t19_0 := Filter(['t15'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t15)), If(Or(NULL(t15, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t15, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t15) != SALES__CUSTOMERKEY(t3)))]),
        And(Not(DELETED(t19_0)), t19_0 == t15),
    ),
    Implies(Not(And(*[Not(DELETED(t15)), If(Or(NULL(t15, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t15, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t15) != SALES__CUSTOMERKEY(t3)))])), DELETED(t19_0)),
),

# t20_0 := Filter(['t16'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t16)), If(Or(NULL(t16, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t16, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t16) != SALES__CUSTOMERKEY(t3)))]),
        And(Not(DELETED(t20_0)), t20_0 == t16),
    ),
    Implies(Not(And(*[Not(DELETED(t16)), If(Or(NULL(t16, SALES__CUSTOMERKEY__String),
      NULL(t3, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t16, SALES__CUSTOMERKEY__String)),
       Not(NULL(t3, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t16) != SALES__CUSTOMERKEY(t3)))])), DELETED(t20_0)),
),

# t25_0 := Filter(['t3'], Cond=(EXISTS FFakeProjectionTable(Table10): [	t21 := FakeProjection(['t17'], Cond=[SALES__CUSTOMERKEY])	t22 := FakeProjection(['t18'], Cond=[SALES__CUSTOMERKEY])	t23 := FakeProjection(['t19'], Cond=[SALES__CUSTOMERKEY])	t24 := FakeProjection(['t20'], Cond=[SALES__CUSTOMERKEY])]))
And(
    Implies(
        And(*[Not(DELETED(t3)), Or(Not(DELETED(t17_0)),
   Not(DELETED(t18_0)),
   Not(DELETED(t19_0)),
   Not(DELETED(t20_0)))]),
        And(Not(DELETED(t25_0)), t25_0 == t3),
    ),
    Implies(Not(And(*[Not(DELETED(t3)), Or(Not(DELETED(t17_0)),
   Not(DELETED(t18_0)),
   Not(DELETED(t19_0)),
   Not(DELETED(t20_0)))])), DELETED(t25_0)),
),

# t17_1 := Filter(['t13'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t13)), If(Or(NULL(t13, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t13, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t13) != SALES__CUSTOMERKEY(t4)))]),
        And(Not(DELETED(t17_1)), t17_1 == t13),
    ),
    Implies(Not(And(*[Not(DELETED(t13)), If(Or(NULL(t13, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t13, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t13) != SALES__CUSTOMERKEY(t4)))])), DELETED(t17_1)),
),

# t18_1 := Filter(['t14'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t14)), If(Or(NULL(t14, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t14, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t14) != SALES__CUSTOMERKEY(t4)))]),
        And(Not(DELETED(t18_1)), t18_1 == t14),
    ),
    Implies(Not(And(*[Not(DELETED(t14)), If(Or(NULL(t14, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t14, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t14) != SALES__CUSTOMERKEY(t4)))])), DELETED(t18_1)),
),

# t19_1 := Filter(['t15'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t15)), If(Or(NULL(t15, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t15, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t15) != SALES__CUSTOMERKEY(t4)))]),
        And(Not(DELETED(t19_1)), t19_1 == t15),
    ),
    Implies(Not(And(*[Not(DELETED(t15)), If(Or(NULL(t15, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t15, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t15) != SALES__CUSTOMERKEY(t4)))])), DELETED(t19_1)),
),

# t20_1 := Filter(['t16'], Cond=(neq_SALES__CUSTOMERKEY_S__CUSTOMERKEY))
And(
    Implies(
        And(*[Not(DELETED(t16)), If(Or(NULL(t16, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t16, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t16) != SALES__CUSTOMERKEY(t4)))]),
        And(Not(DELETED(t20_1)), t20_1 == t16),
    ),
    Implies(Not(And(*[Not(DELETED(t16)), If(Or(NULL(t16, SALES__CUSTOMERKEY__String),
      NULL(t4, SALES__CUSTOMERKEY__String)),
   False,
   And(Not(NULL(t16, SALES__CUSTOMERKEY__String)),
       Not(NULL(t4, SALES__CUSTOMERKEY__String)),
       SALES__CUSTOMERKEY(t16) != SALES__CUSTOMERKEY(t4)))])), DELETED(t20_1)),
),

# t26_0 := Filter(['t4'], Cond=(EXISTS FFakeProjectionTable(Table10): [	t21 := FakeProjection(['t17'], Cond=[SALES__CUSTOMERKEY])	t22 := FakeProjection(['t18'], Cond=[SALES__CUSTOMERKEY])	t23 := FakeProjection(['t19'], Cond=[SALES__CUSTOMERKEY])	t24 := FakeProjection(['t20'], Cond=[SALES__CUSTOMERKEY])]))
And(
    Implies(
        And(*[Not(DELETED(t4)), Or(Not(DELETED(t17_1)),
   Not(DELETED(t18_1)),
   Not(DELETED(t19_1)),
   Not(DELETED(t20_1)))]),
        And(Not(DELETED(t26_0)), t26_0 == t4),
    ),
    Implies(Not(And(*[Not(DELETED(t4)), Or(Not(DELETED(t17_1)),
   Not(DELETED(t18_1)),
   Not(DELETED(t19_1)),
   Not(DELETED(t20_1)))])), DELETED(t26_0)),
),

# t27 := Projection(['t25'], Cond=[TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1])
And(*[
    Implies(
        Not(DELETED(t25_0)),
        And(
Not(DELETED(t27)),
And(NULL(t27, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String) ==
    Or(NULL(t25_0, SALES__CUSTOMERKEY__String), False),
    TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(t27) ==
    SALES__CUSTOMERKEY(t25_0) + 1),
        ),
    ),
    Implies(DELETED(t25_0), DELETED(t27)),
]),

# t28 := Projection(['t26'], Cond=[TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1])
And(*[
    Implies(
        Not(DELETED(t26_0)),
        And(
Not(DELETED(t28)),
And(NULL(t28, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String) ==
    Or(NULL(t26_0, SALES__CUSTOMERKEY__String), False),
    TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(t28) ==
    SALES__CUSTOMERKEY(t26_0) + 1),
        ),
    ),
    Implies(DELETED(t26_0), DELETED(t28)),
])
)

premise = And(DBMS_facts, premise1, premise2)

def equals(ltuples, rtuples):
    left_left_function = lambda tuple1, tuple2: Or(
    And(DELETED(tuple1), DELETED(tuple2)),
    And(
        Not(DELETED(tuple1)),
        Not(DELETED(tuple2)),
        Or(And(NULL(tuple1, SALES__CUSTOMERKEY__String), NULL(tuple2, SALES__CUSTOMERKEY__String)), And(Not(NULL(tuple1, SALES__CUSTOMERKEY__String)), Not(NULL(tuple2, SALES__CUSTOMERKEY__String)), SALES__CUSTOMERKEY(tuple1) == SALES__CUSTOMERKEY(tuple2))),
    )
)
    left_right_function = lambda tuple1, tuple2: Or(
    And(DELETED(tuple1), DELETED(tuple2)),
    And(
        Not(DELETED(tuple1)),
        Not(DELETED(tuple2)),
        Or(And(NULL(tuple1, SALES__CUSTOMERKEY__String), NULL(tuple2, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String)), And(Not(NULL(tuple1, SALES__CUSTOMERKEY__String)), Not(NULL(tuple2, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String)), SALES__CUSTOMERKEY(tuple1) == TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(tuple2))),
    )
)
    right_left_function = lambda tuple1, tuple2: Or(
    And(DELETED(tuple1), DELETED(tuple2)),
    And(
        Not(DELETED(tuple1)),
        Not(DELETED(tuple2)),
        Or(And(NULL(tuple1, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String), NULL(tuple2, SALES__CUSTOMERKEY__String)), And(Not(NULL(tuple1, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String)), Not(NULL(tuple2, SALES__CUSTOMERKEY__String)), TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(tuple1) == SALES__CUSTOMERKEY(tuple2))),
    )
)
    right_right_function = lambda tuple1, tuple2: Or(
    And(DELETED(tuple1), DELETED(tuple2)),
    And(
        Not(DELETED(tuple1)),
        Not(DELETED(tuple2)),
        Or(And(NULL(tuple1, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String), NULL(tuple2, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String)), And(Not(NULL(tuple1, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String)), Not(NULL(tuple2, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String)), TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(tuple1) == TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(tuple2))),
    )
)

    formulas = [
        Sum([If(DELETED(tuple_sort), 0, 1) for tuple_sort in ltuples]) ==         Sum([If(DELETED(tuple_sort), 0, 1) for tuple_sort in rtuples])
    ]
    for tuple_sort in ltuples:
        count_in_ltuples = Sum([If(left_left_function(tuple_sort, t), 1, 0) for t in ltuples])
        count_in_rtuples = Sum([If(left_right_function(tuple_sort, t), 1, 0) for t in rtuples])
        formulas.append(
            Implies(
                Not(DELETED(tuple_sort)),
                count_in_ltuples == count_in_rtuples,
            )
        )
    for tuple_sort in rtuples:
        count_in_ltuples = Sum([If(right_left_function(tuple_sort, t), 1, 0) for t in ltuples])
        count_in_rtuples = Sum([If(right_right_function(tuple_sort, t), 1, 0) for t in rtuples])
        formulas.append(
            Implies(
                Not(DELETED(tuple_sort)),
                count_in_ltuples == count_in_rtuples,
            )
        )

    formulas = And(formulas)
    return formulas

conclusion = equals(ltuples=[t3, t4], rtuples=[t27, t28])

solver = Solver()

solver.add(Not(Implies(premise, conclusion)))
print(f'Symbolic Reasoning Output: ==> {solver.check()} <==')
model = solver.model()
#print(model)
for t in [t9, t10, t11, t12, t13, t14, t15, t16, t17, t18, t19, t20, t25, t26, t27, t28]:
	print(str(t), model.eval(DELETED(t)))
def _f(null, value, out_str=False, data_preix=None, type=None):
    if not isinstance(null, bool):
        null = eval(str(model.eval(null, model_completion=True)))
    if null:
        value = 99999
    else:
        if not isinstance(value, int | float):
            value = eval(str(model.eval(value, model_completion=False)))
    
    if value == 99999:
        return 'NULL'
    else:
        if out_str:
            return f"'{value}'"
        else:
            value = value if data_preix is None else f"'{data_preix + str(value)}'"
            if type == 'boolean':
                return value != 0
            else:
                return value

print(
	_f(NULL(t1, CUSTOMER__CUSTOMERKEY__String), CUSTOMER__CUSTOMERKEY(t1)),
)
print(
	_f(NULL(t2, CUSTOMER__CUSTOMERKEY__String), CUSTOMER__CUSTOMERKEY(t2)),
)
print(
	_f(NULL(t3, SALES__CUSTOMERKEY__String), SALES__CUSTOMERKEY(t3)),
',',
	_f(NULL(t3, SALES__ORDERDATEKEY__String), SALES__ORDERDATEKEY(t3)),
',',
	_f(NULL(t3, SALES__SHIPDATE__String), SALES__SHIPDATE(t3)),
',',
	_f(NULL(t3, SALES__DUEDATE__String), SALES__DUEDATE(t3)),
)
print(
	_f(NULL(t4, SALES__CUSTOMERKEY__String), SALES__CUSTOMERKEY(t4)),
',',
	_f(NULL(t4, SALES__ORDERDATEKEY__String), SALES__ORDERDATEKEY(t4)),
',',
	_f(NULL(t4, SALES__SHIPDATE__String), SALES__SHIPDATE(t4)),
',',
	_f(NULL(t4, SALES__DUEDATE__String), SALES__DUEDATE(t4)),
)
print(
	_f(NULL(t5, DATE__DATEKEY__String), DATE__DATEKEY(t5)),
)
print(
	_f(NULL(t6, DATE__DATEKEY__String), DATE__DATEKEY(t6)),
)

print('--------sql1--------')
if model.eval(Not(DELETED(t3))):
	print(
	_f(NULL(t3, SALES__CUSTOMERKEY__String), SALES__CUSTOMERKEY(t3)),
	)
if model.eval(Not(DELETED(t4))):
	print(
	_f(NULL(t4, SALES__CUSTOMERKEY__String), SALES__CUSTOMERKEY(t4)),
	)
print('--------sql2--------')
if model.eval(Not(DELETED(t27))):
	print(
	_f(NULL(t27, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String), TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(t27)),
	)
if model.eval(Not(DELETED(t28))):
	print(
	_f(NULL(t28, TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1__String), TABLE11__ADD_S__CUSTOMERKEY_DIGITS_1(t28)),
	)

