from flask import Blueprint
from flask.ext.restful import Api

blueprint = Blueprint("api", __name__, url_prefix="/api")
api = Api(blueprint)

# bind resources to api object BEFORE we Initialize
# if not, routes will not exists on flask app object

# slack
# from resources.slack.ListChannels import ListChannels
# from resources.slack.GetChannels import GetChannel
# from resources.slack.officeHistories import GetOfficeHistories

# add resources

# slack
# api.add_resource(ListChannels, '/slack/channels')
# api.add_resource(GetChannel, '/slack/channel/<channel>')
# api.add_resource(GetOfficeHistories, '/slack/officeHistories')

api.init_app(blueprint)
