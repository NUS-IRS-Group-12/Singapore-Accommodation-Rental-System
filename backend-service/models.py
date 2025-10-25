from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import math

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255))
    password = db.Column(db.String(255))

    interactions = db.relationship('UserInteraction', backref='user', lazy=True)


class Property(db.Model):
    __tablename__ = 'property'
    property_id = db.Column(db.Integer, primary_key=True)
    property_name = db.Column(db.Text)
    description = db.Column(db.Text)
    neighborhood_overview = db.Column(db.Text)
    picture_url = db.Column(db.Text)
    neighbourhood_cleansed = db.Column(db.Text)
    neighbourhood_group_cleansed = db.Column(db.Text)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    property_type = db.Column(db.Text)
    room_type = db.Column(db.Text)

    accommodates = db.Column(db.Float)
    bathrooms = db.Column(db.Float)
    bedrooms = db.Column(db.Float)
    beds = db.Column(db.Float)

    amenities = db.Column(db.Text)

    price = db.Column(db.Float)

    review_scores_rating = db.Column(db.Text)
    review_scores_accuracy = db.Column(db.Text)
    review_scores_cleanliness = db.Column(db.Text)
    review_scores_checkin = db.Column(db.Text)
    review_scores_communication = db.Column(db.Text)
    review_scores_location = db.Column(db.Text)
    review_scores_value = db.Column(db.Text)

    interactions = db.relationship('UserInteraction', backref='property', lazy=True)

    @classmethod
    def find_within_radius(cls, target_lat, target_lon, distance_km):
        """
        使用 Haversine 公式在 SQL 层筛选指定半径内的 Property 列表
        """
        R = 6371  # 地球半径 km

        # 将经纬度转换为弧度
        lat_rad = func.radians(cls.latitude)
        lon_rad = func.radians(cls.longitude)
        target_lat_rad = math.radians(target_lat)
        target_lon_rad = math.radians(target_lon)

        # Haversine
        dlat = lat_rad - target_lat_rad
        dlon = lon_rad - target_lon_rad

        a = func.sin(dlat / 2) * func.sin(dlat / 2) + \
            func.cos(target_lat_rad) * func.cos(lat_rad) * \
            func.sin(dlon / 2) * func.sin(dlon / 2)
        c = 2 * func.atan2(func.sqrt(a), func.sqrt(1 - a))
        distance_expr = R * c  # km

        results = cls.query.with_entities(cls.property_id)\
            .filter(distance_expr <= distance_km).all()
        return [int(r[0]) for r in results]

class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    user_interaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'))
    user_like = db.Column(db.Boolean)
    num_of_views = db.Column(db.Integer)
    