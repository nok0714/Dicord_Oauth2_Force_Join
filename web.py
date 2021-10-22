# 설정 파일
import config
# 필요 모듈 불러오기
import os, requests
from flask import Flask, session, redirect, request, url_for
from requests_oauthlib import OAuth2Session

# 디코 API
AUTHORIZATION_BASE_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = config.CLIENT_SECRET

if "http://" in config.REDIRECT_URI:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

# 함수들
def token_updater(token):
    session["oauth2_token"] = token

def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=config.CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=config.REDIRECT_URI,
        auto_refresh_kwargs={
            "client_id": config.CLIENT_ID,
            "client_secret": config.CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)

# ----- 라우터어어 ----- #
@app.route("/")
def index():
    scope = request.args.get(
        "scope",
        "identify guilds.join")
    discord = make_session(scope=scope.split(" "))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session["oauth2_state"] = state
    return redirect(authorization_url)

# ----- 컬백 ----- #
@app.route("/callback")
def callback():
    if request.values.get("error"):
        return request.values["error"]
    discord = make_session(state=session.get("oauth2_state"))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=config.CLIENT_SECRET,
        authorization_response=request.url)
    session["oauth2_token"] = token
    user = discord.get("https://discord.com/api" + "/users/@me").json()
    FORCE_JOIN_URL = f"https://discord.com/api/guilds/{config.SERVER_ID}/members/{user['id']}"
    headers = {
            "Authorization" : f"Bot {config.BOT_TOKEN}",
            'Content-Type': 'application/json'
        }
    data = {
            "access_token" : token["access_token"]
        }
    response = requests.put(url=FORCE_JOIN_URL, json=data, headers=headers)
    return redirect("https://discord.com/oauth2/authorized")

if __name__ == "__main__":
    app.run(host=config.WEB_HOST, port=config.WEB_PORT)