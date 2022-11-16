from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from random import choice


app = Flask(__name__)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/random")
def get_random_cafe():
    cafes = db.session.query(Cafe).all()
    random_cafe = choice(cafes)
    return jsonify(cafe=random_cafe.to_dict())


@app.route("/all")
def get_all_cafes():
    cafes = db.session.query(Cafe).all()
    cafe_list = []
    for cafe in cafes:
        new_cafe = cafe.to_dict()
        cafe_list.append(new_cafe)
    return jsonify(cafe_list)


@app.route("/search")
def search_location():
    # loc as parameter e.g. url+/search?loc=Peckham
    query_location = request.args.get("loc")
    cafes_by_location = db.session.query(Cafe).filter_by(location=query_location).all()
    if cafes_by_location:
        return jsonify(cafes=[cafe.to_dict() for cafe in cafes_by_location])
    else:
        return jsonify(error={"Not Found": "No cafes at this location"})


@app.route("/add", methods=["POST"])
def add_cafe():
    def check_bool(value):
        return 1 if value == '1' or value.lower() == 'true' else 0

    # Get field values from request body and create a new Cafe object
    # request.form returns an immutable dictionary (ImmutableMultiDict)
    # the boolean values must be blank, 0 or 1
    data = request.form
    new_cafe = Cafe(
        name=data['name'],
        map_url=data['map_url'],
        img_url=data['img_url'],
        location=data['location'],
        seats=data['seats'],
        has_toilet=check_bool(data['has_toilet']),
        has_wifi=check_bool(data['has_wifi']),
        has_sockets=check_bool(data['has_sockets']),
        can_take_calls=check_bool(data['can_take_calls']),
        coffee_price=data['coffee_price'],
    )
    # Check if cafe is already in the database
    # Select all results from the search <class 'flask_sqlalchemy.BaseQuery'>
    search_cafe = db.session.query(Cafe).filter_by(
        name=new_cafe.name,
        location=new_cafe.location
    ).all()
    if search_cafe:
        # 400  Bad Request
        # Request had bad syntax or was impossible to fulfill
        return jsonify(error={"exists": "Cafe already exists."}), 400
    else:
        # Add cafe to database
        db.session.add(new_cafe)
        db.session.commit()
        # 200  OK     Action completed successfully
        return jsonify(response={"success": "Successfully added the new cafe."}), 200


# HTTP PUT/PATCH - Update Record
# Put = full replacement
# Patch = piece of data to be updated

@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def update_price(cafe_id):
    new_price = request.args.get("new_price")
    cafe = db.session.query(Cafe).get(cafe_id)
    if cafe:
        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully added the new coffee price."}), 200
    else:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404


# HTTP DELETE - Delete Record

@app.route("/report-closed/<cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    api_key = request.args.get("api_key")
    cafe = db.session.query(Cafe).get(cafe_id)
    if api_key == "TopSecretAPIKey":
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted cafe object"}), 200
        else:
            return jsonify(error={"Not Found": "No cafe with this id"}), 404
    else:
        return jsonify(error={"No access to this method, wrong api_key"}), 403



if __name__ == '__main__':
    app.run(debug=True)
