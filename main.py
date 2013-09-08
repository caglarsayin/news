import webapp2
import os
import jinja2
import mymodal
import datetime
import urlparse
from webapp2_extras import auth
from webapp2_extras import sessions
from google.appengine.datastore.datastore_query import Cursor
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
from webapp2_extras import json


################################################
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

config = {
  'webapp2_extras.auth': {
    'user_model': 'mymodal.User',
    'user_attributes': ['name']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'qwertasdfgzxcvb'
  }
}
#####################################################

class BaseHandler(webapp2.RequestHandler):
  @webapp2.cached_property
  def auth(self):
    """Shortcut to access the auth instance as a property."""
    return auth.get_auth()

  @webapp2.cached_property
  def user_info(self):
    """Shortcut to access a subset of the user attributes that are stored
    in the session.

    The list of attributes to store in the session is specified in
      config['webapp2_extras.auth']['user_attributes'].
    :returns
      A dictionary with most user information
    """
    return self.auth.get_user_by_session()

  @webapp2.cached_property
  def user(self):
    """Shortcut to access the current logged in user.

    Unlike user_info, it fetches information from the persistence layer and
    returns an instance of the underlying model.

    :returns
      The instance of the user model associated to the logged in user.
    """
    u = self.user_info
    return self.user_model.get_by_id(u['user_id']) if u else None

  @webapp2.cached_property
  def user_model(self):
    """Returns the implementation of the user model.

    It is consistent with config['webapp2_extras.auth']['user_model'], if set.
    """
    return self.auth.store.user_model

  @webapp2.cached_property
  def session(self):
      """Shortcut to access the current session."""
      return self.session_store.get_session(backend="datastore")

  def render_template(self, view_filename, params={}):
    user = self.user_info
    params['user'] = user
    template = JINJA_ENVIRONMENT.get_template(view_filename)
    self.response.write(template.render(params))

  def display_message(self, params):
    """Utility function to display a template with a simple message."""
    quotes = mymodal.Quote.query()
    packed_quotes = quotes.iter(offset=0, limit=25)
    params['quotes']=packed_quotes
    self.render_template('templates/news.html', params)

  # this is needed for webapp2 sessions to work
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
          # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
          # Save all sessions.
            self.session_store.save_sessions(self.response)


#####################################################
class FetchJsonHandler(BaseHandler):
    def get(self):
        page=self.request.get('page')
        curs = Cursor(urlsafe=self.request.get('cursor'))
        quotes = mymodal.Quote.query()
        packed_quotes, next_curs, more = quotes.fetch_page(25, start_cursor=curs)
        template_values = {'curs': next_curs.urlsafe(),
                           'more': more,
                           'page':page,
                           'elements':self.ndb_to_dict(packed_quotes)}
        template_values=json.encode(template_values)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(template_values)

    def ndb_to_dict(self, packed_quotes):
        return [i.to_dict(exclude=['date_time']) for i in packed_quotes]


class FetchHandler(BaseHandler):
    def get(self):
        page = self.request.get('page')
        curs = Cursor(urlsafe=self.request.get('cursor'))
        quotes = mymodal.Quote.query()
        packed_quotes, next_curs, more = quotes.fetch_page(25, start_cursor=curs)
        template_values = {'curs': next_curs.urlsafe(),
                           'more': more,
                           'page':page,
                           'quotes':packed_quotes}
        template = JINJA_ENVIRONMENT.get_template(template_values)
        template_values=json.encode(template_values)
        self.render_template('/templates/fetch.html', template_values)



class MainHandler(BaseHandler):
    def get(self):
        template_values = {'title': 'CiftSarmalNews'}
        self.render_template('/templates/news.html', template_values)


class AdditionHandler(BaseHandler):
    def post(self):
        title = self.request.get('title')
        url = self.request.get('url')
        category = self.request.get('category')
        username = self.user.auth_ids[0]
        new = mymodal.Quote(quote=title,uri=url,creator=username)
        new.created = new.date_time.strftime("%x %H:%M")
        if not u"http" == urlparse.urlsplit(url)[0]:
            self.display_message({'warning':'URL adresi yanlis'})
        short_uri = urlparse.urlsplit(url)[1]
        if short_uri.split('.')[0]=='www':
            short_uri=short_uri[4:]
        new.short_uri=short_uri
        new.put()
        self.display_message({'success':'Yaziniz Eklendi! :)'})


class Doldur(BaseHandler):
    def get(self):
        new = mymodal.Quote(quote="Test",uri="http://www.example.com",creator="caglar")
        short_uri = urlparse.urlsplit("http://www.example.com")[1]
        if short_uri.split('.')[0]=='www':
            short_uri = short_uri[4:]
        new.short_uri = short_uri
        new.put()


class SignupHandler(BaseHandler):
    def get(self):
        self.render_template('templates/signup.html')

    def post(self):
        user_name = self.request.get('username')
        email = self.request.get('email')
        name = self.request.get('name')
        last_name = self.request.get('lastname')
        password = self.request.get('password')
        sex = self.request.get('sex')
        education = self.request.get('education')

        unique_properties = ['email_address']
        user_data = self.user_model.create_user(user_name,
                                                unique_properties,
                                                email_address=email,
                                                name=name,
                                                password_raw=password,
                                                last_name=last_name,
                                                verified=True)
        if not user_data[0]: #user_data is a tuple
            self.display_message('Unable to create user for email %s because of \
            duplicate keys %s' % (user_name, user_data[1]))
            return

        user = user_data[1]
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        self.redirect(self.uri_for('home'))


class LogoutHandler(BaseHandler):
      def get(self):
        self.auth.unset_session()
        self.redirect(self.uri_for('home'))


class LoginHandler(BaseHandler):
    def get(self):
        self._serve_page()

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        try:
            u = self.auth.get_user_by_password(username, password, remember=True)
            self.display_message({'success': u['name']})
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self._serve_page(True)

    def _serve_page(self, failed=False):
        username = self.request.get('username')
        params = {
        'username': username,
        'failed': failed}
        self.response.write(params)

app = webapp2.WSGIApplication([webapp2.Route('/', MainHandler, name='home'),
                               webapp2.Route('/addit', AdditionHandler, name='addit'),
                               webapp2.Route('/signup', SignupHandler, name='signup'),
                               webapp2.Route('/logout', LogoutHandler, name='logout'),
                               webapp2.Route('/login', LoginHandler, name='login'),
                               webapp2.Route('/fetch', FetchHandler, name='datafetch'),
                               webapp2.Route('/jfetch', FetchJsonHandler, name='jsonfetch'),
                               ('/doldur', Doldur),
                               ], debug=True, config=config)
