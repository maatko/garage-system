from flask import Flask, request, render_template, jsonify
import database
import detect
import uuid
import os

# create the flask app
app = Flask(__name__)

# if the upload directory does
# not exist, make sure to create it
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def check_licence_plate(request):
    if "image" in request.files:
        # get the file that was uploaded
        image = request.files["image"]

        # make sure that the file was provided
        if image.filename == "":
            return None

        # get the file extension (suffix) of the image
        file_extension = os.path.splitext(image.filename)[1]

        # generate a random uuid for the image
        file_name = os.path.join(UPLOAD_DIR, str(uuid.uuid4())) + file_extension

        # save the image
        image.save(file_name)

        # read the text from the licence plate
        plate_text = detect.read_licence_plate_text(file_name)

        # make sure that text was found on the licence plate
        if plate_text is None or len(plate_text) == 0:
            return None

        # check if the licence plate has access to the garage
        query_result = database.check_licence_plate(plate_text)

        # make sure that text was found on the licence plate
        if query_result is None or len(query_result) == 0:
            return None

        # get the first and last name of the user
        first_name, last_name = query_result[0]

        # return the variables
        return first_name, last_name, plate_text

    # if the image was not found make sure
    # to return None
    return None


@app.route("/check", methods=["POST"])
def check():
    # check the licence plate
    result = check_licence_plate(request)
    if result is None:
        return jsonify(error="You don't have access to this garage")

    # get the first name, last name and the licence plate text from the request
    first_name, last_name, plate_text = result

    # return the data in the json format
    return jsonify(
        first_name=first_name,
        last_name=last_name,
        plate_text=plate_text
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # check the licence plate
        result = check_licence_plate(request)
        if result is None:
            return render_template("responses/failure.html")

        # get the first name, last name and the licence plate text from the request
        first_name, last_name, plate_text = result

        # render the success page
        return render_template("responses/success.html", response=f"{first_name} {last_name} - {plate_text}")

    # if the request was not post, return the default index.html file
    return render_template("index.html")


@app.route("/admin", methods=["GET"])
def admin():
    return render_template("admin.html", results=database.get_users())


# on the main entry point
# start the flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
