from flask import Flask, jsonify, request
import requests
import config
from models import db, User, UserInteraction, Property
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config.from_object(config)
db.init_app(app)

@app.route('/')
def home():
    return "Flask backend is running!"

# ------------------ User 接口 ------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(user_name=username).first()
    if not user:
        new_user = User(user_name=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "message": "ok",
            "user_id": new_user.user_id
        })
    elif user and user.password == password:
        return jsonify({
            "message": "ok",
            "user_id": user.user_id
        })
    else:
        return jsonify({
            "message": "Invalid username or password,",
            "user_id": 0
        })
    
@app.route('/search', methods=['POST'])
def search():
    pid = int(request.json.get('pid', "0"))
    property_obj = Property.query.filter_by(property_id=pid).first()
    if not property_obj:
        return jsonify({"error": "Property not found"}), 404
    
    result = [{
        "property_id": property_obj.property_id,
        "property_name": property_obj.property_name,
        "image_url": property_obj.picture_url,
        "region": property_obj.neighbourhood_group_cleansed,
        "room_type": property_obj.room_type,
        "accommodates": property_obj.accommodates,
        'price': property_obj.price,
        'rating': property_obj.review_scores_rating,
        'latitude': property_obj.latitude,
        'longitude': property_obj.longitude
    }]
    return jsonify(result)

# ------------------ Property 接口 ------------------
@app.route('/properties', methods=['GET'])
def get_properties():
    regions = request.args.get('regions')      # 例如: "Central,East"
    types = request.args.get('types')          # 例如: "Entire home,Private room"
    accommodates = request.args.get('accommodates')  # 例如: "1-2,3-4"

    page = int(request.args.get('page', 1))     # 默认第一页
    limit = 12  # 默认每页20条

    query = Property.query

    # ---- Regions 映射 ----
    region_map = {
        "Central": "Central Region",
        "East": "East Region",
        "North": "North Region",
        "North-East": "North-East Region",
        "West": "West Region"
    }

    if regions:
        region_list = regions.split(',')
        db_regions = [region_map.get(r) for r in region_list if region_map.get(r)]
        query = query.filter(Property.neighbourhood_group_cleansed.in_(db_regions))

    # ---- Room Type ----
    if types:
        type_list = types.split(',')
        query = query.filter(Property.room_type.in_(type_list))

    # ---- Accommodates ----
    if accommodates:
        acc_list = accommodates.split(',')
        acc_filters = []
        for acc in acc_list:
            if acc == "1-2":
                acc_filters.append(Property.accommodates <= 2)
            elif acc == "3-4":
                acc_filters.append(Property.accommodates.between(3, 4))
            elif acc == "5-6":
                acc_filters.append(Property.accommodates.between(5, 6))
            elif acc == "7 +":
                acc_filters.append(Property.accommodates >= 7)
        if acc_filters:
            query = query.filter(db.or_(*acc_filters))

    # ---- 分页查询 ----
    total = query.count()
    properties = query.offset((page - 1) * limit).limit(limit).all()

    # ---- 数据封装 ----
    result = []
    for p in properties:
        result.append({
            'property_id': p.property_id,
            'property_name': p.property_name,
            'image_url': p.picture_url,
            'region': p.neighbourhood_group_cleansed,
            'room_type': p.room_type,
            'accommodates': p.accommodates,
            'price': p.price,
            'rating': p.review_scores_rating
        })

    return jsonify({
        "total": total,
        "data": result
    })


# ------------------ PropertyDetails 接口 ------------------
@app.route('/properties/<int:property_id>/details', methods=['POST'])
def property_details(property_id):
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # 查询 property
    property_obj = Property.query.filter_by(property_id=property_id).first()
    if not property_obj:
        return jsonify({"error": "Property not found"}), 404

    # 查询用户互动
    if int(user_id) > 0:
        interaction = UserInteraction.query.filter_by(
            user_id=user_id,
            property_id=property_id
        ).first()

        if interaction:
            interaction.num_of_views = interaction.num_of_views + 1 if interaction.num_of_views else 1
        else:
            interaction = UserInteraction(
                user_id=user_id,
                property_id=property_id,
                user_like=False,
                num_of_views=1
            )
            db.session.add(interaction)

        db.session.commit()

    # 返回 property 信息和用户 like 状态
    response = {
        "property_id": property_obj.property_id,
        "property_name": property_obj.property_name,
        "description": property_obj.description,
        "neighborhood_overview": property_obj.neighborhood_overview,
        "picture_url": property_obj.picture_url,
        "neighbourhood_cleansed": property_obj.neighbourhood_cleansed,
        "neighbourhood_group_cleansed": property_obj.neighbourhood_group_cleansed,
        "latitude": property_obj.latitude,
        "longitude": property_obj.longitude,
        "property_type": property_obj.property_type,
        "room_type": property_obj.room_type,
        "accommodates": property_obj.accommodates,
        "bathrooms": property_obj.bathrooms,
        "bedrooms": property_obj.bedrooms,
        "beds": property_obj.beds,
        "amenities": property_obj.amenities,
        "price": property_obj.price,
        "review_scores_rating": property_obj.review_scores_rating,
        "review_scores_accuracy": property_obj.review_scores_accuracy,
        "review_scores_cleanliness": property_obj.review_scores_cleanliness,
        "review_scores_checkin": property_obj.review_scores_checkin,
        "review_scores_communication": property_obj.review_scores_communication,
        "review_scores_location": property_obj.review_scores_location,
        "review_scores_value": property_obj.review_scores_value,
    }

    return jsonify(response)


# ------------------ UserInteraction 接口 ------------------
@app.route('/properties/<int:property_id>/like', methods=['POST'])
def toggle_like(property_id):
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # 查找该用户对该房源的交互记录
    interaction = UserInteraction.query.filter_by(
        user_id=user_id,
        property_id=property_id
    ).first()

    if interaction:
        # 反转当前点赞状态
        interaction.user_like = not interaction.user_like
        action = "like" if interaction.user_like else "unlike"
    else:
        # 如果没有记录，创建一个 LIKE=True 的记录
        interaction = UserInteraction(
            user_id=user_id,
            property_id=property_id,
            user_like=True,
            num_of_views=0
        )
        db.session.add(interaction)
        action = "like"

    db.session.commit()

    return jsonify({
        "message": "Success",
        "action": action,
        "user_like": interaction.user_like
    })


# ------------------ FavouriteProperty 接口 ------------------
@app.route('/liked-properties', methods=['POST'])
def get_liked_properties():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    

    # 查询该用户所有点赞记录
    liked_records = UserInteraction.query.filter_by(
        user_id=user_id,
        user_like=True
    ).all()

    # 如果没有点赞记录
    if not liked_records:
        return jsonify([])

    # 获取所有 property_id
    property_ids = [record.property_id for record in liked_records]

    # 查询对应的房源信息
    properties = Property.query.filter(Property.property_id.in_(property_ids)).all()

    result = []
    for p in properties:
        result.append({
            "property_id": p.property_id,
            "property_name": p.property_name,
            "image_url": p.picture_url,
            "region": p.neighbourhood_group_cleansed,
            "room_type": p.room_type,
            "accommodates": p.accommodates,
            'price': p.price,
            'rating': p.review_scores_rating,
            'latitude': p.latitude,
            'longitude': p.longitude
        })
    return jsonify(result)


# ------------------ Recommendation 接口 ------------------
# {
#   "user_id": "1",
#   "location": {
#     "longitude": <float>,
#     "latitude": <float>,
#     "distance": <float> # km
#   } # Optional, get recommendation based on location
# }
@app.post("/recommend")
def call_external_recommend():
    
    data = request.get_json(force=True)
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    queries = []
    location = data.get("location", {})
    if location:
        try:
            longitude = location["longitude"]
            latitude = location["latitude"]
            distance = location["distance"]
            queries = Property.find_within_radius(latitude,longitude,distance)
            if not queries:
                return jsonify({"message": "No interactions found for this user", "recommendations": []}), 401
        except:
            return jsonify({"error": "location is invalid"}), 400

    interactions = UserInteraction.query.filter_by(user_id=user_id).all()
    if not interactions:
        return jsonify({"message": "No interactions found for this user", "recommendations": []}), 402

    inter_list = []
    for i in interactions:
        inter_list.append({
            "listing_id": str(i.property_id),
            "like": int(i.user_like),   # True->1, False->0
            "views": int(i.num_of_views or 0)
        })

    external_url = "http://recommendation:7860/recommend"  # 替换为实际 URL
    payload = {
        "user_id": str(user_id),
        "interactions": inter_list,
        "top_k": 18,
        # if not [], get based on the list
        "listing_id_queries": queries,
        "alpha": 2.0,
        "include_seen": False
    }

    try:
        resp = requests.post(external_url, json=payload,  headers={'Content-Type': 'application/json'})
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
    recommend_ids = []
    for item in result.get("recommendations", []):
        try:
            recommend_ids.append(int(item["listing_id"]))
        except:
            continue   # 避免无效 ID

    if not recommend_ids:
        return jsonify({"error": "No valid recommendations"}), 404

    properties = Property.query.filter(Property.property_id.in_(recommend_ids)).all()

    properties_sorted = sorted(properties, key=lambda x: recommend_ids.index(x.property_id))

    response_list = []
    for p in properties_sorted:
        response_list.append({
            "property_id": p.property_id,
            "property_name": p.property_name,
            "image_url": p.picture_url,
            "region": p.neighbourhood_group_cleansed,
            "room_type": p.room_type,
            "accommodates": p.accommodates,
            'price': p.price,
            'rating': p.review_scores_rating,
            'latitude': p.latitude,
            'longitude': p.longitude
        })
    return jsonify(response_list)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 初始化数据库表
    app.run(host='0.0.0.0', debug=True, port=8000)