import tornado.web
import tornado.options
import tornado.ioloop
from tornado.escape import json_encode
import logic, api, newapi, apiv12
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from threading import Thread
import os
import string
import random
import json

chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')
secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(100)])
secret_key = 'PEO+{+RlTK[3~}TS-F%[9J/sIp>W7!r*]YV75GZV)e;Q9lAdNE{m@oWX.+u-&z*-p>~Xa!Z8j~{z,BVv.e0GChY{(1.KVForO#rQ'

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    xsrf_cookies=False,
    cookie_secret= secret_key,
    login_url= "/login",
)

class TemplateRendering:
    def render_template(self, template_name, variables = {}):
        env = Environment(loader = FileSystemLoader(settings['template_path']))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)

        content = template.render(variables)
        return content

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, mainT):
        self.mainT = mainT

    def get_current_user(self):
        return self.get_secure_cookie("userid")

class Application(tornado.web.Application):
    def __init__(self, mainT):
        handlers = [
            (r"/", MainHandler, {'mainT':mainT}),
            (r"/logout", LogoutHandler, {'mainT': mainT}),
            (r"/login", LoginHandler, {'mainT':mainT}),
            (r"/Alerts", AlertsHandler, {'mainT':mainT}),
            #(r"/message", MessageHandler, {'mainT':mainT}),
            (r"/alertinfo", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/alertinfo/([0-9]*)", CreateEditAlertsHandler, {'mainT':mainT}),
            (r"/Feed/(.*)", FeedHandler, {'mainT':mainT}),
            (r"/Feed", FeedHandler, {'mainT':mainT}),
            (r"/Conversations/(.*)", ConversationPageHandler, {'mainT':mainT}),
            (r"/Conversations", ConversationPageHandler, {'mainT':mainT}),
            (r"/Comments/(.*)", ConversationHandler, {'mainT':mainT}),
            (r"/Comments", ConversationHandler, {'mainT':mainT}),
            (r"/News/(.*)", NewsHandler, {'mainT':mainT}),
            (r"/News", NewsHandler, {'mainT':mainT}),
            (r"/Search", SearchHandler, {'mainT':mainT}),
            (r"/get_news", SearchNewsHandler, {'mainT':mainT}),
            (r"/get_news/(.*)", SearchNewsHandler, {'mainT':mainT}),
            (r"/Audience", AudienceHandler, {'mainT':mainT}),
            (r"/preview", PreviewHandler, {'mainT':mainT}),
            (r"/sentiment", SentimentHandler, {'mainT':mainT}),
            (r"/bookmark", BookmarkHandler, {'mainT':mainT}),
            (r"/domain", DomainHandler, {'mainT':mainT}),
            (r"/newTweets", NewTweetsHandler, {'mainT':mainT}),
            (r"/newTweets/(.*)", NewTweetsHandler, {'mainT':mainT}),
            (r"/api", DocumentationHandler, {'mainT':mainT}),
            (r"/api/v1\.1", Documentationv11Handler, {'mainT':mainT}),
            (r"/api/v1\.2", Documentationv12Handler, {'mainT':mainT}),
            (r"/api/get_themes", ThemesHandler, {'mainT':mainT}),
            (r"/api/get_influencers/(.*)/(.*)", InfluencersHandler, {'mainT':mainT}),
            (r"/api/get_feeds/(.*)/(.*)", FeedsHandler, {'mainT':mainT}),
            (r"/api/get_influencers/(.*)", InfluencersHandler, {'mainT':mainT}),
            (r"/api/get_feeds/(.*)", FeedsHandler, {'mainT':mainT}),
            (r"/getPages", PagesHandler, {'mainT':mainT}),
            (r"/api/v1.1/get_themes", ThemesV11Handler, {'mainT':mainT}),
            (r"/api/v1.1/get_feeds", FeedsV11Handler, {'mainT':mainT}),
            (r"/api/v1.1/get_influencers", InfluencersV11Handler, {'mainT':mainT}),
            (r"/api/v1.2/get_themes", ThemesV12Handler, {'mainT':mainT}),
            (r"/api/v1.2/get_feeds", FeedsV12Handler, {'mainT':mainT}),
            (r"/api/v1.2/get_influencers", InfluencersV12Handler, {'mainT':mainT}),
            (r"/api/v1.2/get_news", NewsV12Handler, {'mainT':mainT}),
            (r"/api/v1.2/get_conversation", ConversationHandler, {'mainT':mainT}),
            (r"/api/v1.2/get_hashtags", HashtagsV12Handler, {'mainT':mainT}),
            (r"/(.*)", tornado.web.StaticFileHandler, {'path': settings['static_path']}),
        ]
        super(Application, self).__init__(handlers, **settings)

class ConversationPageHandler(BaseHandler, TemplateRendering):
    def get(self):
        self.mainT.checkThread()
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title' : "Conversations",
            'alerts': logic.getAlertList(userid),
            'type' : "conversation"
        }
        content = self.render_template(template, variables)
        self.write(content)

class ConversationHandler(BaseHandler, TemplateRendering):
    def get(self):
        topic_id = self.get_argument("topic_id")
        timeFilter = self.get_argument("timeFilter")
        paging = self.get_argument("paging")
        docs = apiv12.getConversations(topic_id,timeFilter,paging)
        if docs == None:
            docs = []
        self.write(self.render_template("submission.html", {"docs":docs}))

class ThemesV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        themes = apiv12.getThemes(4)
        self.set_header('Content-Type', 'application/json')
        self.write(themes)

class FeedsV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        themename = self.get_argument("themename", None)
        themeid = self.get_argument("themeid", None)
        forbidden_domain = self.get_argument("forbidden_domains", "").split(",")
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass
        date = str(self.get_argument("date", "month"))
        feeds = apiv12.getFeeds(themename, themeid, date, cursor, forbidden_domain)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)

class InfluencersV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        themename = self.get_argument("themename", None)
        themeid = self.get_argument("themeid", None)
        influencers = apiv12.getInfluencers(themename, themeid)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)

class HashtagsV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        themename = self.get_argument("themename", None)
        themeid = self.get_argument("themeid", None)
        hashtags = apiv12.getHastags(themename, themeid)
        self.set_header('Content-Type', 'application/json')
        self.write(hashtags)

class NewsV12Handler(BaseHandler, TemplateRendering):
    def get(self):
        """themename = self.get_argument("themename", None)
        themeid = self.get_argument("themeid", None)"""
        news_ids = self.get_argument('news_ids', "").split(",")
        keywords = self.get_argument('keywords', "").split(",")
        languages = self.get_argument('languages', "").split(",")
        countries = self.get_argument('countries', "").split(",")
        cities = self.get_argument('cities', "").split(",")
        user_location = self.get_argument('mention_location', "").split(",")
        user_language = self.get_argument('mention_language', "").split(",")
        since = self.get_argument('since', "")
        until = self.get_argument('until', "")
        print(countries)
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass
        news = apiv12.getNews(news_ids, keywords, languages, cities, countries, user_location, user_language, cursor, since, until, [""])
        self.set_header('Content-Type', 'application/json')
        self.write(news)

class Documentationv12Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv12.html'
        variables = {
            'title' : "Watchtower Api v1.2"
        }
        content = self.render_template(template, variables)
        self.write(content)

class ThemesV11Handler(BaseHandler, TemplateRendering):
    def get(self):
        themes = newapi.getThemes(4)
        self.set_header('Content-Type', 'application/json')
        self.write(themes)

class FeedsV11Handler(BaseHandler, TemplateRendering):
    def get(self):
        themename = str(self.get_argument("themename", None))
        themeid = str(self.get_argument("themeid", None))
        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass
        date = str(self.get_argument("date", "month"))
        feeds = newapi.getFeeds(themename, themeid , 4, date, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)

class InfluencersV11Handler(BaseHandler, TemplateRendering):
    def get(self):
        themename = str(self.get_argument("themename", None))
        themeid = str(self.get_argument("themeid", None))
        influencers = newapi.getInfluencers(themename, themeid)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)

class Documentationv11Handler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'apiv11.html'
        variables = {
            'title' : "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)

class ThemesHandler(BaseHandler, TemplateRendering):
    def get(self):
        themes = logic.getThemes()
        self.set_header('Content-Type', 'application/json')
        self.write(themes)

class InfluencersHandler(BaseHandler, TemplateRendering):
    def get(self, themename, cursor=None):
        influencers = logic.getInfluencers(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(influencers)

class FeedsHandler(BaseHandler, TemplateRendering):
    def get(self, themename, cursor=None):
        feeds = logic.getFeeds(themename, cursor)
        self.set_header('Content-Type', 'application/json')
        self.write(feeds)

class DocumentationHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'api.html'
        variables = {
            'title' : "Watchtower Api"
        }
        content = self.render_template(template, variables)
        self.write(content)

class MainHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'index.html'
        variables = {
            'title' : "Watchtower"
        }
        content = self.render_template(template, variables)
        self.write(content)

class LoginHandler(BaseHandler, TemplateRendering):
    def get(self):
        template = 'login.html'
        variables = {
            'title' : "Login Page"
        }
        content = self.render_template(template, variables)
        self.write(content)

    def post(self):
        login_info = logic.login(str(self.get_argument("username")), str(self.get_argument("password")))
        if login_info['response']:
            self.set_secure_cookie("userid", str(login_info['userid']))
            self.write({'response': True, 'redirectUrl': self.get_argument('next', '/Alerts')})
        else:
            self.write(json.dumps(login_info))

class LogoutHandler(BaseHandler, TemplateRendering):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")

class AlertsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        self.mainT.checkThread()
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(userid),
            'type' : "alertlist",
            'alertlimit' : logic.getAlertLimit(userid),
            'threadstatus': logic.getThreadStatus(self.mainT),
            'threadconnection': logic.getThreadConnection(self.mainT)
        }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid = None):
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        userid = tornado.escape.xhtml_escape(self.current_user)
        if posttype == u'remove':
            info = logic.deleteAlert(alertid, self.mainT,userid)
        elif posttype == u'stop':
            info = logic.stopAlert(alertid, self.mainT)
        elif posttype == u'start':
            info = logic.startAlert(alertid, self.mainT)
        elif posttype == u'publish':
            info = logic.publishAlert(alertid)
        elif posttype == u'unpublish':
            info = logic.unpublishAlert(alertid)
        template = "alerts.html"
        variables = {
            'title' : "Alerts",
            'alerts' : logic.getAlertList(userid),
            'type' : "alertlist",
            'alertlimit' : logic.getAlertLimit(userid)
        }
        content = self.render_template(template, variables)
        self.write(content)

class MessageHandler(BaseHandler, TemplateRendering):
    def post(self):
        alertid = self.get_argument("alertid")
        info = logic.response(alertid)
        result = info['message'] + ";" + info['type']
        self.write(result)

class CreateEditAlertsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, alertid = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {}
        if alertid != None:
            if logic.alertExist(alertid):
                if logic.checkUserIdAlertId(userid, alertid):
                    variables['title'] = "Edit Alert"
                    variables['alert'] = logic.getAlert(alertid)
                    variables['type'] = "editAlert"
                else:
                    self.redirect("/Alerts")
            else:
                self.redirect("/Alerts")
        else:
            if logic.getAlertLimit(userid) == 0:
                self.redirect("/Alerts")
            variables['title'] = "Create Alert"
            variables['alert'] = logic.getAlert(alertid)
            variables['type'] = "createAlert"
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, alertid = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        alert = {}
        alert['keywords'] = ",".join(self.get_argument("keywords").split(","))
        try:
            alert['domains'] = ",".join(self.get_argument("domains").split(","))
        except:
            alert['domains'] = ""
        print(alert['domains'])
        alert['description'] = self.get_argument("description")
        keywordlimit = 10 - len(self.get_argument("keywords").split(","))
        alert['keywordlimit'] = keywordlimit
        #alert['excludedkeywords'] = ",".join(self.get_argument("excludedkeywords").split(","))
        if len(self.request.arguments.get("languages")) != 0:
            alert['lang'] = b','.join(self.request.arguments.get("languages")).decode("utf-8")
        else:
            alert['lang'] = ""
        facebookpages = self.request.arguments.get("facebookpages")
        if facebookpages != None and len(facebookpages) != 0:
            alert['pages'] = b','.join(facebookpages).decode("utf-8")
        else:
            alert['pages'] = ""
        subreddits = self.request.arguments.get("subreddits")
        if subreddits != None and len(subreddits) != 0:
            alert['subreddits'] = b','.join(subreddits).decode("utf-8")
        else:
            alert['subreddits'] = ""

        print(alert['subreddits'], alert['pages'])
        if alertid != None:
            alert['alertid'] = alertid
            logic.updateAlert(alert, self.mainT, userid)
        else:
            alert['name'] = self.get_argument('alertname')
            alertid = logic.getNextAlertId()
            logic.addAlert(alert, self.mainT, userid)
        self.redirect("/Alerts")

class PreviewHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        template = 'tweetsTemplate.html'
        keywords = self.get_argument("keywords")
        #exculdedkeywords = self.get_argument("excludedkeywords")
        languages = self.get_argument("languages")
        variables = {
            'tweets': logic.searchTweets(keywords, languages)
        }
        if len(variables['tweets']) == 0:
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)

class BookmarkHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        link_id = self.get_argument("link_id")
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        if posttype == "add":
            content = logic.addBookmark(alertid, link_id)
        else:
            content = logic.removeBookmark(alertid, link_id)
        self.write(content)

class SentimentHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        link_id = self.get_argument("link_id")
        alertid = self.get_argument("alertid")
        posttype = self.get_argument("posttype")
        if posttype == "positive":
            content = logic.sentimentPositive(alertid, link_id)
        elif posttype == "negative":
            content = logic.sentimentNegative(alertid, link_id)
        else:
            content = logic.sentimentNotr(alertid, link_id)
        self.write(content)

class DomainHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self):
        domain = self.get_argument("domain")
        alertid = self.get_argument("alertid")
        logic.banDomain(alertid, domain)
        self.write({})

class FeedHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument = None):
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        if argument is not None:
            try:
                alertid = int(argument)
                variables = {
                    'title': "Feed",
                    'tweets': logic.getTweets(alertid),
                    'alertid': alertid,
                    'alertname': logic.getAlertName(alertid),
                    'comesAlert': True,
                    'type': "feed"
                }
                if len(variables['tweets']) == 0:
                    self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
            except ValueError:
                variables = {
                    'title': "Feed",
                    'alerts': logic.getAlertList(userid),
                    'comesAlert': False,
                    'type': "feed"
                }
                pass
        else:
            variables = {
                'title': "Feed",
                'alerts': logic.getAlertList(userid),
                'comesAlert': False,
                'type': "feed"
            }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        if argument is not None:
            template = 'tweetsTemplate.html'
            alertid = self.get_argument('alertid')
            lastTweetId = self.get_argument('lastTweetId')
            variables = {
                'tweets': logic.getSkipTweets(alertid, lastTweetId)
            }
        else:
            template = 'alertFeed.html'
            alertid = self.get_argument('alertid')
            variables = {
                'tweets': logic.getTweets(alertid),
                'alertid': alertid
            }
            if len(variables['tweets']) == 0:
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no tweet now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)

class NewTweetsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def post(self, get = None):
        if get is not None:
            template = 'tweetsTemplate.html'
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            variables = {
                'tweets': logic.getNewTweets(alertid, newestId)
            }
            content = self.render_template(template, variables)
        else:
            alertid = self.get_argument('alertid')
            newestId = self.get_argument('tweetid')
            content = str(logic.checkTweets(alertid, newestId))
        self.write(content)

class NewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument = None):
        variables = {}
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        if argument is not None:
            try:
                alertid = int(argument)
                try:
                    date =  self.get_argument('date')
                except:
                    date = 'yesterday'
                    pass
                try:
                    feeds = logic.getNews(alertid, date, 0)
                    variables = {
                        'title': "News",
                        'feeds': feeds['feeds'],
                        'cursor': feeds['next_cursor'],
                        'alertid': alertid,
                        'alertname': logic.getAlertName(alertid),
                        'comesAlert': True,
                        'type': "news"
                    }
                except:
                    self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
            except ValueError:
                variables = {
                    'title': "News",
                    'alerts': logic.getAlertList(userid),
                    'comesAlert': False,
                    'type': "news"
                }
                pass
        else:
            variables = {
                'title': "News",
                'alerts': logic.getAlertList(userid),
                'comesAlert': False,
                'type': "news"
            }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self, argument=None):
        variables = {}
        if argument is not None:
            template = 'newsTemplate.html'
            alertid = self.get_argument('alertid')
            next_cursor = self.get_argument('next_cursor')
            try:
                date =  self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            try:
                feeds = logic.getNews(alertid, date, int(next_cursor))
                variables = {
                    'feeds': feeds['feeds'],
                    'cursor': feeds['next_cursor'],
                }
            except Exception as e:
                print(e)
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        else:
            template = 'alertNews.html'
            alertid = self.get_argument('alertid')
            try:
                date =  self.get_argument('date')
            except:
                date = 'yesterday'
                pass
            try:
                feeds = logic.getNews(alertid, date, 0)
                variables = {
                    'feeds': feeds['feeds'],
                    'cursor': feeds['next_cursor'],
                    'alertid': alertid
                }
            except Exception as e:
                print(e)
                self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)

class SearchHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        variables = {}
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        variables = {
            'title': "Search",
            'type': "search"
        }

        content = self.render_template(template, variables)
        self.write(content)

class SearchNewsHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        keywords = self.get_argument('keywords').split(",")
        domains = self.get_argument('domains').split(",")
        languages = self.get_argument('languages').split(",")
        countries = self.get_argument('countries').split(",")
        cities = self.get_argument('cities').split(",")
        user_location = self.get_argument("mention_location").split(",")
        user_language = self.get_argument('mention_language').split(",")
        cursor = self.get_argument("cursor")
        since = ""
        until = ""

        try:
            cursor = int(self.get_argument("cursor"))
            if cursor == -1:
                cursor = 0
        except:
            cursor = 0
            pass

        if argument is not None:
            template = 'newsTemplate.html'
        else:
            template = "alertNews.html"

        news = apiv12.getNews([""], keywords, languages, cities, countries, user_location, user_language, cursor, since, until, domains)
        news = json.loads(news)
        if news['news'] == []:
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
        variables = {
            'feeds': news['news'],
            'cursor': news['next_cursor_str']
        }

        content = self.render_template(template, variables)
        self.write(content)

class AudienceHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self, argument=None):
        variables = {}
        userid = tornado.escape.xhtml_escape(self.current_user)
        template = 'afterlogintemplate.html'
        if argument is not None:
            try:
                alertid = int(argument)
                try:
                    audiences = logic.getAudiences(alertid)
                    variables = {
                        'title': "Audience",
                        'alertname': logic.getAlertName(alertid),
                        'audiences': audiences,
                        'comesAlert': True,
                        'type': "audiences"
                    }
                except:
                    self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no news now.</b></p>")
            except ValueError:
                variables = {
                    'title': "Audience",
                    'alerts': logic.getAlertList(userid),
                    'comesAlert': False,
                    'type': "audience"
                }
                pass
        else:
            variables = {
                'title': "Audience",
                'alerts': logic.getAlertList(userid),
                'comesAlert': False,
                'type': "audience"
            }
        content = self.render_template(template, variables)
        self.write(content)

    @tornado.web.authenticated
    def post(self):
        variables = {}
        template = 'alertAudience.html'
        alertid = self.get_argument('alertid')
        try:
            audiences = logic.getAudiences(alertid)
            variables = {
                'audiences': audiences,
                'alertid': alertid
            }
        except Exception as e:
            print(e)
            self.write("<p style='color: red; font-size: 15px'><b>Ops! There is no audience now.</b></p>")
        content = self.render_template(template, variables)
        self.write(content)

class PagesHandler(BaseHandler, TemplateRendering):
    @tornado.web.authenticated
    def get(self):
        template = 'pages.html'
        keywordsList = self.get_argument("keywords").split(",")

        if keywordsList != ['']:
            sourceSelection = logic.sourceSelection(keywordsList)
        else:
            sourceSelection = {'pages': [], 'subreddits': []}

        variables = {
            'facebookpages': sourceSelection['pages'],
            'redditsubreddits': sourceSelection['subreddits']
        }

        print(variables)

        content = self.render_template(template, variables)
        self.write(content)

def main(mainT):
    tornado.options.parse_command_line()
    app = Application(mainT)
    app.listen(8484)
    tornado.ioloop.IOLoop.current().start()

def webserverInit(mainT):
    thr = Thread(target= main, args= [mainT] )
    thr.daemon = True
    thr.start()
    thr.join()

if __name__ == "__main__":
    main()
