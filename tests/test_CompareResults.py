import pandas as pd
import numpy as np
from helper import compare_results

# ---------- 生成大型随机 DataFrame 的工具 ----------
def make_large_df(rows=1_000, cols=10, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = rng.integers(0, 10_000, size=(rows, cols))
    return pd.DataFrame(data, columns=[f"col_{i}" for i in range(cols)])

if __name__ == "__main__":
    df1_a = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    df2_a = df1_a.copy()

    df1_b = df1_a.copy()
    df2_b = pd.DataFrame({"val": ["a", "b", "c"], "id": [1, 2, 3]})

    df1_c = pd.DataFrame({"x": [1, 2, 1], "y": [3, 4, 3]})
    df2_c = df1_c.sample(frac=1, random_state=42)  # 行顺序打乱

    df1_d = df1_a.copy()
    df2_d = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "X", "c"]})  # 第二行不同

    df1_e = df1_a.copy()
    df2_e = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"], "extra": [0, 0, 0]})

    df1_f = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    df2_f = pd.DataFrame({"a": [1, 2, 2], "b": [3, 4, 4]})  # 重复分布不同

    df1_g = pd.DataFrame({"n": [1, 2, 3]})
    df2_g = pd.DataFrame({"n": [1.0, 2.0, 3.0]})  # int vs float

    df1_h = pd.DataFrame({"k": [np.nan, None, 5]})
    df2_h = pd.DataFrame({"k": [np.nan, None, 5]})

    df1_i = make_large_df()
    df2_i = df1_i.sample(frac=1, random_state=1).sample(frac=1, axis=1, random_state=2)

    df1_j = pd.DataFrame({"u": ["alpha", "beta", "gamma"]}, index=[10, 11, 12])
    df2_j = pd.DataFrame({"u": ["alpha", "beta", "gamma"]}, index=[99, 98, 97])

    # === 列名完全不同 & 大型用例 ===
    rng = np.random.default_rng(123)

    arr_k = rng.integers(0, 1_000_000, size=(5_000, 5))
    df1_k = pd.DataFrame(arr_k, columns=[f"A{i}" for i in range(5)])
    df2_k = pd.DataFrame(arr_k, columns=[f"Z{i}" for i in range(5)])

    data_l = {
        "text_1": rng.choice(list("ABCDEFGH"), 2_000),
        "num_1":  rng.uniform(0, 1000, 2_000),
        "text_2": rng.choice(list("WXYZ"), 2_000),
        "num_2":  rng.integers(0, 10_000, 2_000),
        "flag":   rng.choice([True, False], 2_000),
        "num_3":  rng.normal(0, 1, 2_000),
        "cat":    rng.choice(["x", "y", "z"], 2_000),
        "id":     np.arange(2_000),
    }
    df1_l = pd.DataFrame(data_l)
    df2_l = df1_l.sample(frac=1, axis=1, random_state=7).copy()
    df2_l.columns = [f"col_{i}" for i in range(df2_l.shape[1])]

    df1_m = df1_l.copy()
    df2_m = df1_l.drop(columns=["flag"]).copy()
    df2_m.columns = [f"m_{c}" for c in df2_m.columns]

    arr_n = rng.integers(0, 2**31 - 1, size=(10_000, 20))
    df1_n = pd.DataFrame(arr_n, columns=[f"orig_{i}" for i in range(20)])
    df2_n = (
        pd.DataFrame(arr_n, columns=[f"new_{i}" for i in range(20)])
          .sample(frac=1, axis=1, random_state=11)
          .sample(frac=1, random_state=22)
    )

    # === 测试列表 ===
    tests = [
        ("完全一致",                    df1_a, df2_a, True),
        ("列顺序不同",                  df1_b, df2_b, True),
        ("行顺序不同",                  df1_c, df2_c, True),
        ("值不同",                      df1_d, df2_d, False),
        ("列数不同",                    df1_e, df2_e, False),
        ("重复行分布不同",              df1_f, df2_f, False),
        ("int 与 float 表示差异",       df1_g, df2_g, False),
        ("包含 NaN/None",              df1_h, df2_h, True),
        ("大型表行列乱序",              df1_i, df2_i, True),
        ("索引不同",                    df1_j, df2_j, True),
        ("5000×5 列名完全不同",         df1_k, df2_k, True),
        ("2000×8 列乱序并重命名",       df1_l, df2_l, True),
        ("缺失一列",                    df1_m, df2_m, False),
        ("10000×20 行列乱序改名",       df1_n, df2_n, True),
    ]

    # === 执行测试 ===
    for name, left, right, expected in tests:
        got = compare_results(left, right)
        status = "✅" if got == expected else "❌"
        print(f"{status} {name:<25} -> 结果: {got}  (期望: {expected})")
