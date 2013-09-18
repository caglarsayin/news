import webapp2

class Trending(webapp2.RequestHandler):
    def get(self):
        pass


app = webapp2.WSGIApplication([webapp2.Route('/tasks/trending', Trending, name='trending'), ],
                                  debug=True)
