
import webapp2
import os
import jinja2

from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty()

class Story(ndb.Model):
    content = ndb.TextProperty()
    month = ndb.StringProperty()
    year = ndb.StringProperty()
    author = ndb.StructuredProperty(Author)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('JusHapMain.html')
        self.response.write(template.render(template_values))

class Page(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        story = Story()
        if self.request.get('store'):
            story.content = self.request.get("content")
            story.month = self.request.get("month")
            story.year = self.request.get("year")
            if user:
                story.author = Author(identity=users.get_current_user().user_id(), email=users.get_current_user().email())
            story.put()
        if self.request.get('nostore'):
            story.month = self.request.get("month")
            story.year = self.request.get("year")

        self.redirect('/story?month={0}&year={1}'.format(story.month, story.year))

    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        month = self.request.get('month')
        year = self.request.get('year')
        stories_query = Story.query(ndb.AND(Story.month==month, Story.year==year)).order(-Story.date)

        # cursor = ndb.Cursor(urlsafe=self.request.get('cursor'))
        # items, next_curs, more = stories_query.fetch_page(10, start_cursor=cursor)
        # if more:
        #     next_c = next_curs.urlsafe()
        # else:
        #     next_c = None
        # self.generate('JusHapPage.html', {'items': items, 'cursor': next_c })

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'stories': stories_query,
            'month': month,
            'year': year}

        template = JINJA_ENVIRONMENT.get_template('JusHapPage.html')
        self.response.write(template.render(template_values))

class ManagePage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            email = user.email()
            stories = Story.query(Story.author.email == email).order(-Story.date)
            stories.fetch(1000)
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'stories': stories,
        }

        template = JINJA_ENVIRONMENT.get_template('ManagePage.html')
        self.response.write(template.render(template_values))

class Delete(webapp2.RequestHandler):
    def post(self):
        story_keys = self.request.get_all('delete', allow_multiple=True)
        if len(story_keys) > 0:
           for story_key in story_keys:
               story_object = ndb.Key(urlsafe=story_key)
               story_object.delete()
           self.redirect('/manage')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/story', Page),
    ('/manage', ManagePage),
    ('/delete', Delete)
], debug=True)