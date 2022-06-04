#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form, CsrfProtect
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CsrfProtect(app)
csrf.init_app(app) # Fixing the bug of csrf token not found

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship("Show", backref="Venue", lazy=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Venue id={self.id} name={self.name} city={self.city} state={self.city}>\n"

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship("Show", backref="Artist", lazy=False, cascade="all, delete-orphan")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
    __tablename__ = "Show"
    
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  data = []

  results = Venue.query.distinct(Venue.city, Venue.state).all()

  for result in results:
    city_state_unit = {
      "city": result.city,
      "state": result.state
    }

    venues = Venue.query.filter_by(city=result.city, state=result.state).all()

    #format each venue
    formatted_venues = []
    for venue in venues:
      formatted_venues.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
      })

    city_state_unit["venues"] = formatted_venues
    data.append(city_state_unit)
  
  return render_template('pages/venues.html', areas=data);
  
  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  #return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term  = request.form.get('search_term', '')

  venues = list(Venue.query.filter(
    Venue.name.ilike(f'%{search_term}%') |
    Venue.city.ilike(f'%{search_term}%') |
    Venue.state.ilike(f'%{search_term}%')
  )).all()

  response["count"] = len(venues)
  response["data"] = []

  for venue in venues:
    venue_unit = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
    }
    response["data"].append(venue_unit)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  

  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  setattr(venue, "genres", venue.genres.split(",")) # converts genres to list

  #get past shows
  past_shows = list(filter(lambda x: x.start_time < datetime.now(), venue.shows))
  temp_shows = []

  for show in past_shows:
    temp = {}
    temp["artist_id"] = show.artist_id
    temp["artist_name"] = show.artist.name
    temp["artist_image_link"] = show.artist.image_link
    temp["start_time"] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    temp_shows.append(temp)

  setattr(venue, "past_shows", temp_shows)
  setattr(venue, "past_shows_count", len(temp_shows))

  #get upcoming shows
  upcoming_shows = list(filter(lambda x: x.start_time > datetime.now(), venue.shows))
  temp_shows = []

  for show in upcoming_shows:
    temp ={}
    temp["artist_id"] = show.artist_id
    temp["artist_name"] = show.artist.name
    temp["artist_image_link"] = show.artist.image_link
    temp["start_time"] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    temp_shows.append(temp)
  
  setattr(venue, "upcoming_shows", temp_shows)
  setattr(venue, "upcoming_shows_count", len(temp_shows))

  return render_template('pages/show_venue.html', venue=venue)

  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  
  if form.validate():
    try:
        new_venue = Venue(
          name = form.name.data,
          city = form.city.data,
          state = form.state.data,
          address = form.address.data,
          phone = form.phone.data,
          genres = ",".join(form.genres.data),#This coverts array to string with commas
          facebook_link = form.facebook_link.data,
          image_link = form.image_link.data,
          seeking_talent = form.seeking_talent.data,
          seeking_description = form.seeking_description.data,
          website = form.website.data
        )

        db.session.add(new_venue) # Managing database transactions 
        db.session.commit()
        flash('Venue ' + request.form['name'] + 'was successfully created and stored!')
    except Exception:
     db.session.rollback()
     print(sys.exc_info())
     flash('An error occured. Your Venue' + 'Could not be added to our database')

    finally:
      db.session.close() 

  else:
    print("\n\n", form.errors)
    flash('An error accurred while trying to create your venue! ')

  return render_template('pages/home.html')

  
  #return redirect(url_for("index")) # This redirects the user back to the home page
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  #return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')

  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occured. Venue ' + venue.name + ' could not be deleted.')

  finally:
    db.session.close()

  return redirect(url_for("index"))


  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  #return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist = db.session.query(Artist.id, Artist.name).all()
  # TODO: replace with real data returned from querying the database
  return render_template('pages/artists.html', artists=artist)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term  = request.form.get('search_term', '')
  artists = Artist.query.filter(
    Artist.name.ilike(f"%{search_term}%") |
    Artist.city.ilike(f"%{search_term}%") |
    Artist.state.ilike(f"%{search_term}%")
  ).all()

  response = {
    "count": len(artists),
    "data": []
  }

  for artist in artists:
    temp = {}
    temp['id'] = artist.id
    temp['name'] = artist.name

    upcoming_shows = 0
    for show in artist.shows:
      if show.start_time > datetime.now():
        upcoming_shows += 1
    temp['upcoming_shows'] = upcoming_shows

    response['data'].append(temp)


  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  setattr(artist, "genres", artist.genres.split(",")) #This coverts string to array

  #past shows
  past_shows = list(filter(lambda show: show.start_time < datetime.now(), artist.shows))
  temp_shows = []

  for show in past_shows:
    temp = {}
    temp["venue_id"] = show.venue_id
    temp["venue_name"] = show.venue.name
    temp["venue_image_link"] = show.venue.image_link
    temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

    temp_shows.append(temp)

    setattr(artist, "past_shows", temp_shows)
    setattr(artist, "past_shows_count", len(temp_shows))

  #upcoming shows
  upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), artist.shows))
  temp_shows = []
  for show in upcoming_shows:
    temp = {}
    temp["venue_id"] = show.venue_id
    temp["venue_name"] = show.venue.name
    temp["venue_image_link"] = show.venue.image_link
    temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

    temp_shows.append(temp)

    setattr(artist, "upcoming_shows", temp_shows)
    setattr(artist, "upcoming_shows_count", len(temp_shows))

    return render_template('pages/show_artist.html', artist=artist)
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

    
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  #return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.genres.data = artist.genres.split(',')

  return render_template('forms/edit_artist.html', form=form, artist=artist)


  # TODO: populate form with fields from artist with ID <artist_id>
 # return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)

  if form.validate():
    try:
      artist = Artist.query.get(artist_id)

      artist.name = form.name.data
      artist.city =  form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = ",".join(form.genres.data) # Converts array to string
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website = form.website.data
      artist.seeking_description = form.seeking_description.data
      artist.seeking_venue = form.seeking_venue.data

      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')

    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')

    finally:
      db.session.close()
  else:
    print("\n\n", form.errors)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')

  return redirect(url_for('show_artist', artist_id=artist_id))
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  #return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.genres.data = venue.genres.split(',') # convert string to list

  return render_template('forms/edit_venue.html', form=form, venue=venue)
  

  # TODO: populate form with values from venue with ID <venue_id>
  #return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

   form = VenueForm()

   if form.validate():
    try:
      venue = Venue.query.get(venue_id)

      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = ",".join(form.genres.data)
      venue.facebook_link = form.facebook_link.data
      venue.image_link = form.image_link.data
      venue.website = form.website.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      
      db.session.add(venue)
      db.session.commit()

      flash('Venue ' + request.form['name'] + ' was successfully updated!')

    except Exception:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')

    finally:
      db.session.close()

   else:
    print("\n\n", form.errors)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')

   return redirect(url_for('show_venue', venue_id=venue_id))

  #return render_template('forms/edit_venue.html', form=form)
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()

  if form.validate():
    try:
      new_artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        genres=",".join(form.genres.data), #converts array to string with comma
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        website=form.website.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data
      )

      db.session.add(new_artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

    except Exception:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        print(sys.exc_info())

    finally:
        db.session.close()

  else:
    print(form.errors)
    flash("Artist was not successfully created!")

  return render_template('pages/home.html')




  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  #return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []

  shows = Show.query.all()
  for show in shows:
    temp = {}
    temp['venue_id'] = show.venue_id
    temp['venue_name'] = show.venue.name
    temp['artist_id'] = show.artist_id
    temp['artist_name'] = show.artist.name
    temp['artist_image_link'] = show.artist.image_link
    temp['start_time'] = show.start_time

    data.append(temp)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)

  if form.validate():
    try:
      new_show = Show(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data
      )
      db.session.add(new_show)
      db.session.commit()
      flash('Show was successfully listed!')
    except Exception:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
  else:
    print(form.errors)
    flash('Show could not be listed. Please check form errors.')
  
  return render_template('pages/home.html')

  
  #return redirect(url_for('index'))
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
