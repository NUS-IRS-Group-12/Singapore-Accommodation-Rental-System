from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
import pandas as pd
import numpy as np

# -----------------------------
# 0) App init
# -----------------------------
app = Flask(__name__)

# -----------------------------
# 1) 载入数据（与原版一致）
# -----------------------------
# 相似度矩阵（索引=候选listing，列=候选listing）
similarity_df = pd.read_csv("./data/cosine_similarity.csv", index_col=0)

# 交互（若有 excel 优先）
try:
    interactions = pd.read_excel("interactions.xlsx")
except Exception:
    try:
        interactions = pd.read_csv("interactions.csv", sep=None, engine="python", encoding="utf-8")
    except Exception:
        interactions = pd.DataFrame(columns=["user_id", "listing_id", "like", "views"])

# 房源表
listings = pd.read_csv("./data/listings.csv", encoding="latin1")

# -----------------------------
# 2) 工具函数
# -----------------------------
def _str2bool(v, default=False):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "t", "yes", "y"):
        return True
    if s in ("0", "false", "f", "no", "n"):
        return False
    return default

# -----------------------------
# 3) 推荐函数（与原文件一致）
# -----------------------------
def recommend_for_user(user_id, top_k=10, alpha=2.0, include_seen=False, queries=[]):
    """
    根据用户交互记录计算房源推荐结果。
    include_seen: 是否包含用户已看过或已点赞的房源
    """
    global interactions, similarity_df

    user_data = interactions[interactions["user_id"] == user_id]
    if user_data.empty:
        return {
            "user_id": user_id,
            "count": 0,
            "recommendations": [],
            "invalid_ids": [],
            "message": "No interactions found for this user."
        }

    # 确保索引/列都是字符串
    similarity_df.index = similarity_df.index.astype(str)
    similarity_df.columns = similarity_df.columns.astype(str)

    # 兴趣分数 = α * like + views
    user_data = user_data.copy()
    user_data["score"] = alpha * user_data["like"] + user_data["views"]
    liked_ids = [str(i) for i in user_data["listing_id"].values]
    weights = user_data["score"].values

    # 有效/无效ID划分
    valid_ids = [lid for lid in liked_ids if lid in similarity_df.index]
    invalid_ids = [lid for lid in liked_ids if lid not in similarity_df.index]

    # 无有效ID -> 直接返回
    if len(valid_ids) == 0:
        return {
            "user_id": user_id,
            "count": 0,
            "recommendations": [],
            "invalid_ids": invalid_ids,
            "message": "All listing_id are invalid — cannot generate recommendation."
        }

    # 取相似度子矩阵并加权
    sim_subset = similarity_df.loc[valid_ids]
    weights = weights[:len(valid_ids)]
    weighted_scores = np.dot(weights, sim_subset.values) / weights.sum()

    rec_df = pd.DataFrame({
        "listing_id": similarity_df.columns,
        "recommend_score": weighted_scores
    })

    # 标记是否已看过
    rec_df["seen"] = rec_df["listing_id"].isin(liked_ids)

    # 是否排除已看过
    if not include_seen:
        rec_df = rec_df[~rec_df["seen"]]

    # 排序与Top-K
    rec_df = rec_df.sort_values("recommend_score", ascending=False)

    # 如果queries不为空(就是查询这些房源的偏好顺序, 而不是全局的)
    # 把queries的内容按照rec_df进行排序, 并返回
    if queries:
        queries = [str(q) for q in queries]
        rec_df = rec_df[rec_df["listing_id"].isin(queries)]

    rec_df = rec_df.head(int(top_k))

    return {
        "user_id": user_id,
        "count": len(rec_df),
        "recommendations": rec_df.to_dict(orient="records"),
        "invalid_ids": invalid_ids,
        "message": "Recommendation generated successfully."
    }

# -----------------------------
# 4) GET /recommend
# -----------------------------
@app.route('/')
def home():
    return "Flask backend is running!"

@app.get("/recommend")
def recommend_get():
    """
    输入用户ID，返回推荐结果（JSON）
    查询参数：
      - user_id: str（必填）
      - top_k: int = 10
      - include_seen: bool = false
      - alpha: float = 2.0
    """
    try:
        user_id = request.args.get("user_id", type=str)
        if not user_id:
            raise BadRequest("Missing query parameter: user_id")

        top_k = request.args.get("top_k", default=10, type=int)
        include_seen = _str2bool(request.args.get("include_seen"), default=False)
        alpha = request.args.get("alpha", default=2.0, type=float)

        result = recommend_for_user(user_id=user_id, top_k=top_k, alpha=alpha, include_seen=include_seen)
        return jsonify(result)
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# -----------------------------
# 5) POST /recommend  （固定 replace 行为）
# -----------------------------
@app.post("/recommend")
def recommend_post():
    """
    前端 POST 用户交互 JSON 数据，生成推荐结果。
    固定为 replace —— 用本次交互覆盖该 user_id 的历史记录。

    请求体示例：
    {
      "user_id": "U001",
      "interactions": [
        {"listing_id": "71609", "like": 1, "views": 3},
        {"listing_id": "71896", "like": 0, "views": 2}
      ],
      "listing_id_queries": [
        71604,
        71602,
        71423
      ], # 可选, 当存在时则查询这些房源的偏好顺序, 不存在则全局
      "top_k": 5,            # 可选（默认10）
      "alpha": 2.0,          # 可选（默认2.0）
      "include_seen": false  # 可选（默认false）
    }
    """
    global interactions
    app.logger.info('Test API received')
    try:
        data = request.get_json(force=True, silent=False)
        if not isinstance(data, dict):
            raise BadRequest("Invalid JSON body")

        user_id = data.get("user_id")
        inter_list = data.get("interactions")
        # 如果不存在则返回空列表, recommend_for_user查全局
        listing_id_queries = data.get("listing_id_queries", [])
        if not user_id or not isinstance(inter_list, list) or len(inter_list) == 0:
            raise BadRequest("Body must contain 'user_id' and non-empty 'interactions' list")

        # 校验并转 DataFrame
        df = pd.DataFrame(inter_list)
        required_cols = {"listing_id", "like", "views"}
        if df.empty or not required_cols.issubset(df.columns):
            raise BadRequest(f"Each interaction must contain {required_cols}")

        # 去重（同一 listing_id 取最后一条）
        df = df.drop_duplicates(subset=["listing_id"], keep="last").copy()

        # 组装统一格式（全部转为字符串/整数）
        df["user_id"] = str(user_id)
        df["listing_id"] = df["listing_id"].astype(str)
        df["like"] = pd.to_numeric(df["like"], errors="coerce").fillna(0).astype(int)
        df["views"] = pd.to_numeric(df["views"], errors="coerce").fillna(0).astype(int)
        df = df[["user_id", "listing_id", "like", "views"]]

        # —— replace：先删该 user_id 旧交互，再写新交互
        interactions = interactions[interactions["user_id"] != user_id].copy()
        interactions = pd.concat([interactions, df], ignore_index=True)

        # 读取可选参数
        top_k = int(data.get("top_k", 10))
        alpha = float(data.get("alpha", 2.0))
        include_seen = bool(data.get("include_seen", False))

        # 计算推荐
        result = recommend_for_user(user_id=user_id, top_k=top_k, alpha=alpha, include_seen=include_seen, queries=listing_id_queries)
        return jsonify(result)
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# -----------------------------
# 6) GET /recommend_map
# -----------------------------
@app.get("/recommend_map")
def recommend_map():
    """
    根据用户交互推荐房源，并返回可用于地图展示的数据。
    查询参数：
      - user_id: str（必填）
      - top_k: int = 5
      - include_seen: bool = false
      - alpha: float = 2.0
    """
    try:
        user_id = request.args.get("user_id", type=str)
        if not user_id:
            raise BadRequest("Missing query parameter: user_id")

        top_k = request.args.get("top_k", default=10, type=int)
        include_seen = _str2bool(request.args.get("include_seen"), default=False)
        alpha = request.args.get("alpha", default=2.0, type=float)

        rec = recommend_for_user(user_id=user_id, top_k=top_k, alpha=alpha, include_seen=include_seen)

        # 兼容返回：当没有有效交互/ID时
        if not rec or rec.get("count", 0) == 0:
            return jsonify({"user_id": user_id, "count": 0, "missing": [], "recommendations": []})

        recs = rec["recommendations"]
        rec_ids = [str(r["listing_id"]) for r in recs]

        # 匹配 listings
        listings_local = listings.copy()
        listings_local["id"] = listings_local["id"].astype(str)
        matched = listings_local[listings_local["id"].isin(rec_ids)]

        merged = matched.merge(pd.DataFrame(recs), left_on="id", right_on="listing_id", how="left")
        merged = merged.rename(columns={
            "neighbourhood_cleansed": "neighbourhood",
            "neighbourhood_group_cleansed": "region"
        })

        numeric_cols = ["latitude", "longitude", "price", "review_scores_rating"]
        for col in numeric_cols:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")

        # 去除空坐标 & 数值清洗
        merged = merged.replace([np.inf, -np.inf], np.nan)
        merged = merged.dropna(subset=["latitude", "longitude"])
        merged[numeric_cols] = merged[numeric_cols].apply(lambda x: np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0))

        results = merged[[
            "listing_id", "name", "latitude", "longitude", "price",
            "review_scores_rating", "neighbourhood", "region", "property_type",
            "recommend_score", "seen"
        ]].copy()

        missing = list(set(rec_ids) - set(results["listing_id"].astype(str)))

        payload = {
            "user_id": user_id,
            "count": int(len(results)),
            "missing": missing,
            "recommendations": results.to_dict(orient="records")
        }
        return jsonify(payload)
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# -----------------------------
# 7) main
# -----------------------------


if __name__ == "__main__":
    # 与原来一致的端口
    app.run(host="0.0.0.0", port=7860, debug=True)