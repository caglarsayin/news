from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
import time
import urlparse


class Quote(ndb.Model):
    """Storage for a single quote and its metadata

    Properties
    quote:          The quote as a string
    uri:            An optional URI that is the source of the quotation
    rank:           A calculated ranking based on the number of votes and when the quote was added.
    created:        When the quote was created, recorded in the number of days since the beginning of our local epoch.
    creation_order: Totally unique index on all quotes in order of their creation.
    creator:        The user that added this quote.
    """
    quote = ndb.StringProperty(required=True)
    uri = ndb.StringProperty()
    short_uri = ndb.ComputedProperty(lambda self: self.shortener(self.uri))
    rate = ndb.IntegerProperty(default=0, indexed=True)
    date_time = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    click_count = ndb.IntegerProperty(default=0)
    votesum = ndb.IntegerProperty(default=0)
    creator = ndb.StringProperty()
    category = ndb.StringProperty(indexed=True)
    chosen = ndb.BooleanProperty(default=False, indexed=True)
    created = ndb.ComputedProperty(lambda self: self.date_time.strftime("%x"))

    def shortener(self,url):
        short_uri = urlparse.urlsplit(url)[1]
        if short_uri.split('.')[0] == 'www':
            short_uri = short_uri[4:]
        return short_uri



class User(webapp2_extras.appengine.auth.models.User):
  def set_password(self, raw_password):
    """Sets the password for the current user

    :param raw_password:
        The raw password which will be hashed and stored
    """
    self.password = security.generate_password_hash(raw_password, length=12)

  @classmethod
  def get_by_auth_token(cls, user_id, token, subject='auth'):
    """Returns a user object based on a user ID and token.

    :param user_id:
        The user_id of the requesting user.
    :param token:
        The token string to be verified.
    :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
    """
    token_key = cls.token_model.get_key(user_id, subject, token)
    user_key = ndb.Key(cls, user_id)
    # Use get_multi() to save a RPC call.
    valid_token, user = ndb.get_multi([token_key, user_key])
    if valid_token and user:
        timestamp = int(time.mktime(valid_token.created.timetuple()))
        return user, timestamp

    return None, None