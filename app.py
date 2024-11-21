# cpanel testing2
import os

from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for, send_from_directory, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from werkzeug.utils import secure_filename

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from helpers import apology, upload_to_excel, admin_login_required, embed_link

app = Flask(__name__)

# Get the secret key from an environment variable
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Load admin credentials from environment variables - stored in cpanel
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password')

# Define the upload folder path within the static folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_URL = os.getenv('DB_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/ekprayas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)   

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# Ensure the upload directory exists
if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'secured')):
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'secured'))


def upload_get_public(file):
    filename = secure_filename(file.filename)
    public_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(public_upload_path)
        file_url = url_for('static', filename=f'uploads/{filename}')
        return file_url
    except Exception as e:
        return apology("Error upoading file", 403)


def upload_get_secured(file):
    filename = secure_filename(file.filename)
    secured_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'secured', filename)
    
    try:
        file.save(secured_upload_path)
        file_url = url_for('static', filename=f'uploads/secured/{filename}', _external=True)
        return file_url
    except Exception as e:
        return apology("Error Uploading file", 403)


@app.route("/" , methods=["GET", "POST"])
def index():
   return render_template("index.html")


@app.route("/gallery", methods=["GET", "POST"])
def gallery():
   if request.method == "POST":
      action = request.form.get("formToggle")
      event_name = request.form.get("event_name")
      thumbnail = request.files.get("thumbnail")
      files = request.files.getlist('files')

      if not event_name:
         flash("Must provide event name", "danger")
         return redirect(url_for("gallery"))
      
      if not thumbnail:
         flash("Must provide thumbnail", "danger")
         return redirect(url_for("gallery"))
      
      if not files:
         flash("Must provide files", "danger")
         return redirect(url_for("gallery"))
         

      file_urls = []
      for file in files:
         file_url = upload_get_public(file)
         file_urls.append(file_url)

      thumbnail_url = upload_get_public(thumbnail)

      data = {
        "event_name": event_name,
        "thumbnail_url": thumbnail_url,
        "img1_url": file_urls[0] if len(file_urls) > 0 else None,
        "img2_url": file_urls[1] if len(file_urls) > 1 else None,
        "img3_url": file_urls[2] if len(file_urls) > 2 else None,
        "img4_url": file_urls[3] if len(file_urls) > 3 else None,
        "img5_url": file_urls[4] if len(file_urls) > 4 else None,
        "img6_url": file_urls[5] if len(file_urls) > 5 else None,
        "img7_url": file_urls[6] if len(file_urls) > 6 else None,
        "img8_url": file_urls[7] if len(file_urls) > 7 else None,
        "img9_url": file_urls[8] if len(file_urls) > 8 else None,
        "img10_url": file_urls[9] if len(file_urls) > 9 else None,
        # Add more as needed up to img50_url
      }

      # Prepare your SQL query
      column_names = ', '.join(data.keys())
      placeholders = ', '.join([f':{key}' for key in data.keys()])

      if action == "add":
         query = text(f"""
            INSERT INTO photo_gallery ({column_names})
            VALUES ({placeholders})
         """)

      if action == "edit":
         # Update operation
         event_id = request.form.get("event_id")
         if not event_id:
            flash("Must provide event id", "danger")
            return redirect(url_for("gallery"))
         data["event_id"] = event_id
         query = text(f"""
            UPDATE photo_gallery
            SET {', '.join([f"{key} = :{key}" for key in data.keys() if key != "event_id"])}
            WHERE id = :event_id
         """)

      try:
         db.session.execute(query, data)
         db.session.commit()
      except Exception as e:
         db.session.rollback()
         return apology("An error occured", 500)
         # return apology("An error occured", 500)
         # return f"an error occured {str(e)}"


      flash("Photo Gallery Updated!")
      return redirect("/gallery")

   else:
      rows = db.session.execute(text("SELECT * FROM photo_gallery ORDER BY id DESC")).fetchall()
      modified_rows = [list(row) for row in rows]
      # return jsonify(modified_rows)
      return render_template("gallery.html" , rows = modified_rows)
   


@app.route("/about", methods=["GET", "POST"])
def about():
   if request.method == "GET":
      rows = db.session.execute(text("SELECT * FROM founders")).fetchall()
      modified_rows = [dict(row._mapping) for row in rows]
      # return jsonify(modified_rows)

      rows_team = db.session.execute(text("SELECT * FROM team_info")).fetchall()
      modified_rows_team = [dict(row._mapping) for row in rows_team]

      # return jsonify(modified_rows_team)
      #TODO: update about.html for cards
      return render_template("about.html", rows=modified_rows, rows_team=modified_rows_team)


@app.route("/founders", methods=["POST"])
def founders():
   if request.method == "POST":
      action = request.form.get("actionType")
      name = request.form.get("name")
      photo = request.files.get("photo")
      short_desc = request.form.get("short_desc")
      long_desc = request.form.get("long_desc")
      instagram_url = request.form.get("instagram_url")
      linkedin_url = request.form.get("linkedin_url")
      email = request.form.get("email")
      twitter_url = request.form.get("twitter_url")

      if not name:
         return apology("Must provide Name", 403)
      if not photo:
         return apology("Must Provide profile photo", 403)
      if not short_desc:
         return ("Must provide short description", 403)
      
      photo_url = upload_get_public(photo)
      
      data = {
         "name": name,
         "short_desc": short_desc,
         "long_desc": long_desc,
         "photo_url": photo_url,
         "email": email,
         "linkedin_url": linkedin_url,
         "twitter_url": twitter_url,
         "instagram_url": instagram_url
      }

      column_names = ', '.join(data.keys())
      placeholders = ', '.join([f':{key}' for key in data.keys()])

      if action == "add":
         query = text(f"""
            INSERT INTO founders ({column_names})
            VALUES ({placeholders})
         """)

      if action == "edit":
         # Update operation
         founder_id = request.form.get("founder_id")
         if not founder_id:
            flash("Must provide event founder_id", "danger")
            return redirect(url_for("about"))
         data["founder_id"] = founder_id
         query = text(f"""
            UPDATE founders
            SET {', '.join([f"{key} = :{key}" for key in data.keys() if key != "founder_id"])}
            WHERE id = :founder_id
         """)

      try:
         db.session.execute(query, data)
         db.session.commit()
      except Exception as e:
         db.session.rollback()
         return apology("An error occured", 500)
         # return f"an error occured {str(e)}"


      flash("Founders Updated!")
      return redirect("/about")


@app.route("/team-info", methods=["POST"])
def team_info():
   if request.method == "POST":
      action = request.form.get("actionType")
      name = request.form.get("name")
      photo = request.files.get("photo")
      short_desc = request.form.get("short_desc")
      instagram_url = request.form.get("instagram_url")
      linkedin_url = request.form.get("linkedin_url")
      email = request.form.get("email")
      twitter_url = request.form.get("twitter_url")

      if not name:
         return apology("Must provide Name", 403)
      if not photo:
         return apology("Must Provide profile photo", 403)
      if not short_desc:
         return ("Must provide short description", 403)
      
      photo_url = upload_get_public(photo)
      
      data = {
         "name": name,
         "short_desc": short_desc,
         "photo_url": photo_url,
         "email": email,
         "linkedin_url": linkedin_url,
         "twitter_url": twitter_url,
         "instagram_url": instagram_url
      }

      column_names = ', '.join(data.keys())
      placeholders = ', '.join([f':{key}' for key in data.keys()])

      if action == "add":
         query = text(f"""
            INSERT INTO team_info ({column_names})
            VALUES ({placeholders})
         """)

      if action == "edit":
         # Update operation
         team_id = request.form.get("team_id")
         if not team_id:
            flash("Must provide event team_id", "danger")
            return redirect(url_for("about"))
         data["team_id"] = team_id
         query = text(f"""
            UPDATE team_info
            SET {', '.join([f"{key} = :{key}" for key in data.keys() if key != "team_id"])}
            WHERE id = :team_id
         """)

      try:
         db.session.execute(query, data)
         db.session.commit()
      except Exception as e:
         db.session.rollback()
         return apology("An error occured", 500)
         # return f"an error occured {str(e)}"


      flash("Team members Updated!")
      return redirect("/about")


@app.route("/blind" , methods=["GET", "POST"])
def blind():
   if request.method == "POST":
      first_name = request.form.get("first_name")
      last_name = request.form.get("last_name")
      gender = request.form.get("inlineRadioOptions")
      email = request.form.get("email")
      mobile_number = request.form.get("mobile_number")
      address = request.form.get("address")
      occupation = request.form.get("occupation")
      occupation_address = request.form.get("occupation_address")
      education = request.form.get("education")
      languages = request.form.getlist("languages")
      photo = request.files.get("photo")
      id_proof = request.files.get("id_proof")

      if not first_name:
         return apology("must provide you first_name", 403)
      
      if not last_name:
         return apology("must provide last_name", 403)
      
      if not gender:
         return apology("must provide your gender", 403)
      
      if not email:
         return apology("must provide email", 403)

      if not mobile_number:
         return apology("must provide mobile_number", 403)
      
      if not address:
         return apology("must provide address", 403)

      if not education:
         return apology("must provide education", 403)
      
      if not languages:
         return apology("must provide languages", 403)
      
      if not photo:
         return apology("must provide your photo", 403)
      
      if not id_proof:
         return apology("must provide your identity proof", 403)

      if len(mobile_number) != 10:
         return apology("Mobile number must be of 10 digits", 403)
      
      photo_url = upload_get_secured(photo)  
      id_proof_url = upload_get_secured(id_proof)
      
      try:
         languages_str = ','.join(languages)  # Convert list to comma-separated string

         db.session.execute(
            text(
                  """
                  INSERT INTO blind
                  (first_name, last_name, gender, email, mobile_number, address, occupation, occupation_address, education, languages, photo_url, id_proof_url)
                  VALUES 
                  (:first_name, :last_name, :gender, :email, :mobile_number, :address, :occupation, :occupation_address, :education, :languages, :photo_url, :id_proof_url)
                  """
            ), 
            {
                  "first_name": first_name, 
                  "last_name": last_name, 
                  "gender": gender, 
                  "email": email, 
                  "mobile_number": mobile_number, 
                  "address": address, 
                  "occupation": occupation, 
                  "occupation_address": occupation_address, 
                  "education": education, 
                  "languages": languages_str,  # Use the converted string
                  "photo_url": photo_url, 
                  "id_proof_url": id_proof_url
            }
         )
         db.session.commit()

      except Exception as e:
         db.session.rollback()
         return apology("An Error Occured", 500)
         # Displaying detailed errors is not safe so remove the below line when ready to deploy
         # return f"An error occurred: {str(e)}"

      #Add data to excel
      rows = db.session.execute(text("SELECT * FROM blind")).fetchall()
      modified_rows = [dict(row._mapping) for row in rows]
      upload_to_excel("static/uploads/secured/blind.xlsx", modified_rows,"blind")

      flash("Thank You for Submitting Form We Will Get Back to you Soon.")
      return redirect("/blind")

   else:
      return render_template("blind.html")

   
@app.route("/book", methods=["GET", "POST"])
def book():
   if request.method == "POST":
      first_name = request.form.get("first_name")
      last_name = request.form.get("last_name")
      gender = request.form.get("inlineRadioOptions")
      email = request.form.get("email")
      mobile_number = request.form.get("mobile_number")
      address = request.form.get("address")
      occupation = request.form.get("occupation")
      occupation_address = request.form.get("occupation_address")
      education = request.form.get("education")
      languages = request.form.getlist("languages")
      audio = request.files.get("audio")

      if not first_name:
         flash("Must provide first name", "danger")
         return redirect(url_for("book"))

      if not last_name:
         flash("Must provide last name", "danger")
         return redirect(url_for("book"))

      if not gender:
         flash("Must provide gender", "danger")
         return redirect(url_for("book"))

      if not email:
         flash("Must provide email", "danger")
         return redirect(url_for("book"))

      if not mobile_number:
         flash("Must provide mobile number", "danger")
         return redirect(url_for("book"))

      if not address:
         flash("Must provide address", "danger")
         return redirect(url_for("book"))

      if not education:
         flash("Must provide education", "danger")
         return redirect(url_for("book"))

      if not languages:
         flash("Must provide languages", "danger")
         return redirect(url_for("book"))

      if not audio:
         flash("Must provide your audio file", "danger")
         return redirect(url_for("book"))
      
      if len(mobile_number) != 10:
         return apology("Mobile number must be of 10 digits", 403)

      # Check if the file is an audio file
      allowed_audio_types = {
         'audio/mpeg',  # MP3
         'audio/wav',   # WAV
         'audio/ogg',   # OGG
         'audio/x-wav', # Another variant of WAV
         'audio/webm',  # WebM audio
         'audio/flac'   # FLAC audio
      }

      if audio.mimetype not in allowed_audio_types:
         flash("Invalid audio file type", "danger")
         return redirect(url_for("book"))

      audio_url = upload_get_secured(audio)  

      try:
         languages_str = ','.join(languages)  # Convert list to comma-separated string

         db.session.execute(
               text(
                  """
                  INSERT INTO book
                  (first_name, last_name, gender, email, mobile_number, address, occupation, occupation_address, education, languages, audio_url)
                  VALUES 
                  (:first_name, :last_name, :gender, :email, :mobile_number, :address, :occupation, :occupation_address, :education, :languages, :audio_url)
                  """
               ),
               {
                  "first_name": first_name,
                  "last_name": last_name,
                  "gender": gender,
                  "email": email,
                  "mobile_number": mobile_number,
                  "address": address,
                  "occupation": occupation,
                  "occupation_address": occupation_address,
                  "education": education,
                  "languages": languages_str,  # Use the converted string
                  "audio_url": audio_url
               }    
            )
         db.session.commit()

      except Exception as e:
         db.session.rollback()
         return apology("An Error Occured", 500)
         # Displaying detailed errors is not safe so remove the below line when ready to deploy
         # flash(f"An error occurred: {str(e)}", "danger")
         # Do not redirect to book page so that the user does not have to fill the form again
         # return redirect(url_for("book"))
         
      #Add data to excel
      rows = db.session.execute(text("SELECT * FROM book")).fetchall()
      modified_rows = [dict(row._mapping) for row in rows]
      upload_to_excel("static/uploads/secured/book.xlsx", modified_rows,"book")

      flash("Thank You for Submitting Form We Will Get Back to you Soon.")
      return redirect(url_for("book"))

   else:
      return render_template("book.html")


@app.route("/team", methods=["GET", "POST"])
def team():
   if request.method == "POST":
      first_name = request.form.get("first_name")
      last_name = request.form.get("last_name")
      gender = request.form.get("inlineRadioOptions")
      email = request.form.get("email")
      mobile_number = request.form.get("mobile_number")
      address = request.form.get("address")
      occupation = request.form.get("occupation")
      occupation_address = request.form.get("occupation_address")
      education = request.form.get("education")
      about = request.form.get("about")
      make_change = request.form.get("make_change")
      aadhar_number = request.form.get("aadhar_number")
      pan_number = request.form.get("pan_number")
      aadhar_card = request.files.get("aadhar_card")
      pan_card = request.files.get("pan_card")
      photo = request.files.get("photo") 


      if not first_name:
         return apology("must provide you first_name", 403)
      
      if not last_name:
         return apology("must provide last_name", 403)
      
      if not gender:
         return apology("must provide your gender", 403)
      
      if not email:
         return apology("must provide email", 403)

      if not mobile_number:
         return apology("must provide mobile_number", 403)
      
      if not address:
         return apology("must provide address", 403)

      if not occupation:
         return apology("must provide your occupation", 403)
      
      if not occupation_address:
         return apology("must provide your occupation address", 403)
      
      if not education:
         return apology("must provide education", 403)
      
      if not about:
         return apology("must provide about", 403)
      
      if not make_change:
         return apology("must provide make change", 403)
      
      if not aadhar_number:
         return apology("must provide aadhar number", 403)
      
      if not pan_number:
         return apology("must provide pan number", 403)
      
      if not aadhar_card:
         return apology("must provide aadhar_card", 403)
      
      if not pan_card:
         return apology("must provide pan_card", 403)
      
      if not photo:
         return apology("must provide your photo", 403)
      
      if len(mobile_number) != 10:
         return apology("Mobile number must be of 10 digits", 403)
      
      if len(aadhar_number) != 12:
         return apology("Aadhar number must be of 12 digits wthout any space and symbols", 403)
      
      if len(pan_number) != 10:
         return apology("Pan number must be of 10 characters", 403)

      aadhar_card_url = upload_get_secured(aadhar_card)  
      pan_card_url = upload_get_secured(pan_card)
      photo_url = upload_get_secured(photo)

      try:

         db.session.execute(
            text(
                  """
                  INSERT INTO team
                  (first_name, last_name, gender, email, mobile_number, address, occupation, occupation_address, education, about, make_change , aadhar_number ,  pan_number , aadhar_card , pan_card , photo_url)
                  VALUES 
                  (:first_name, :last_name, :gender, :email, :mobile_number, :address, :occupation, :occupation_address, :education, :about, :make_change , :aadhar_number , :pan_number , :aadhar_card , :pan_card , :photo_url)
                  """
            ), 
            {
                  "first_name": first_name,
                  "last_name": last_name,
                  "gender": gender,
                  "email": email,
                  "mobile_number": mobile_number,
                  "address": address,
                  "occupation": occupation,
                  "occupation_address": occupation_address,
                  "education": education,
                  "about": about, 
                  "make_change": make_change,  
                  "aadhar_number": aadhar_number,  
                  "pan_number": pan_number,  
                  "aadhar_card": aadhar_card_url,  
                  "pan_card": pan_card_url, 
                  "photo_url": photo_url  

            }
         )
         db.session.commit()

      except Exception as e:
         db.session.rollback()
         return apology("An Error Occured", 500)
         # Displaying detailed errors is not safe so remove the below line when ready to deploy
         # return f"An error occurred: {str(e)}"

      #Add data to excel
      rows = db.session.execute(text("SELECT * FROM team")).fetchall()
      modified_rows = [dict(row._mapping) for row in rows]
      upload_to_excel("static/uploads/secured/team.xlsx", modified_rows,"team")

      flash("Thank You for Submitting Form We Will Get Back to you Soon.")
      return redirect(url_for("team"))

   else:
      return render_template("team.html")

   
@app.route("/initiative")
def initiative():
   return render_template("initiative.html")


@app.route("/video-gallery", methods=["GET", "POST"])
def video_gallery():
   if request.method == "POST":
      action = request.form.get("action")
      video_title = request.form.get("video_title")
      video_url = request.form.get("video_url")

      if not video_title:
         return apology("Must provide Video Title", 403)
      if not video_url:
         return apology("Must provide Youtube URL", 403)

      if video_url:
         preview = embed_link(video_url)
         if preview and 'preview' in preview and 'html' in preview['preview']:
            iframe = preview['preview']['html']

      data = {
         "video_title": video_title,
         "iframe": iframe
      }

      column_names = ', '.join(data.keys())
      placeholders = ', '.join([f':{key}' for key in data.keys()])

      if action == "add":
         query = text(f"""
            INSERT INTO video ({column_names})
            VALUES ({placeholders})
         """)

      if action == "edit":
         # Update operation
         video_id = request.form.get("video_id")
         if not video_id:
            flash("Must provide video id", "danger")
            return redirect(url_for("gallery"))
         data["video_id"] = video_id
         query = text(f"""
            UPDATE video
            SET {', '.join([f"{key} = :{key}" for key in data.keys() if key != "video_id"])}
            WHERE id = :video_id
         """)

      try:
         db.session.execute(query, data)
         db.session.commit()
      except Exception as e:
         db.session.rollback()
         return apology("An error occured", 500)      
      
      flash("Video Gallery Updated")
      return redirect("/video-gallery")
   
   else:
      rows = db.session.execute(
         text(
            """SELECT * FROM video ORDER BY id DESC"""
         )
      )
      modified_rows = [dict(row._mapping) for row in rows]
      return render_template("video-gallery.html", videos=modified_rows)


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
   if request.method == "POST":
      username = request.form.get("username")
      password = request.form.get("password")

      if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
         session["admin"] = ADMIN_USERNAME  # Store admin username in session
         return redirect(url_for("admin_dashboard"))
      else:
         return apology("INVALID CREDENTIALS !", 403)
   else:
      return render_template("admin-login.html")
   

@app.route("/admin-dashboard", methods=["GET"])
@admin_login_required
def admin_dashboard():
   if request.method == "GET":
      return render_template("admin-dashboard.html")


@app.route("/logout")
def logout():
   """Log admin out"""
   session.clear()
   return redirect(url_for("admin_login"))


@app.errorhandler(404)
def page_not_found(e):
   return apology("Page Not Found", 404)


@app.errorhandler(500)
def server_error(e):
   return apology("Internal Server Error", 500)


# Secured images route
@app.route("/static/uploads/secured/<filename>")
@admin_login_required
def secured_file(filename):
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'secured', filename)

    if not os.path.isfile(file_path):
        abort(404)  # Not Found

    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'secured'), filename)


# @app.route("/testing")
# def testing():
#    rows = db.session.execute(
#       text(
#          "SELECT photo_url FROM blind WHERE id = 8"
#       ),
#    ).fetchall()
#    image = rows[0][0]
#    return f"{image}"


if __name__ == "__main__":
    app.run(debug=True)


# Change code like below when ready to deploy 

# import logging
# from logging.handlers import RotatingFileHandler

# Set up logging
# handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
# handler.setLevel(logging.ERROR)
# formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
# handler.setFormatter(formatter)
# app.logger.addHandler(handler)

# from flask import Flask, render_template, flash, redirect, url_for

# app = Flask(__name__)

# @app.route('/some_route')
# def some_route():
#     try:
#         # Your route logic here
#         pass
#     except Exception as e:
#         app.logger.error(f"An error occurred: {str(e)}")
#         flash("An unexpected error occurred. Please try again later.", "danger")
#         return redirect(url_for('error'))

# @app.errorhandler(500)
# def internal_error(error):
#     app.logger.error(f"Server Error: {str(error)}")
#     return render_template('500.html'), 500

# @app.errorhandler(Exception)
# def unhandled_exception(e):
#     app.logger.error(f"Unhandled Exception: {str(e)}")
#     return render_template('500.html'), 500

# if __name__ == "__main__":
#     app.run(debug=False)
