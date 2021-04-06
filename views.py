
import textwrap
import urllib.parse
from datetime import datetime
from pprint import pformat
from typing import Optional, Tuple

from henango.http.request import HTTPRequest
from henango.http.response import HTTPResponse
from templates.renderer import render

"""
切り出す先のモジュールの名前は、viewsとします。
コネクションがどうとか、ヘッダーのパースがこうとか、そういったHTTPの事情は関知せず、見た目(view)の部分（= リクエストボディ）を生成することだけを責務として持つモジュールだからです。
"""
def now(
  request:HTTPRequest
) -> HTTPResponse:
  """
  現在時刻を表示するHTMLを生成する
  """
  context = {"now":datetime.now()}
  body = render("now.html", context)

  return HTTPResponse(body=body)

def show_request(
  request:HTTPRequest
) -> HTTPResponse:
  """
  HTTPリクエストの内容を表示するHTMLを生成する
  """
  context = {"request":request,"headers":pformat(request.headers),"body":request.body.decode("utf-8", "ignore")}
  body = render("show_request.html", context)

  return HTTPResponse(body=body)

def parameters(
  request:HTTPRequest
) -> HTTPResponse:
  """
  POSTパラメータを表示するHTMLを表示する
  """
  if request.method == "GET":
    body = b"<html><body><h1>405 Method Not Allowed</h1></body></html>"

    return HTTPResponse(body=body,status_code=405)
  elif request.method == "POST":
    post_params = urllib.parse.parse_qs(request.body.decode())
    context = {"post_params": post_params}
    body = render("params.html", context)

    return HTTPResponse(body=body)

def user_profile(request: HTTPRequest) -> HTTPResponse:
  user_id = request.params["user_id"]
  context = {"user_id": user_id}
  body = render("user_profile.html", context)

  return HTTPResponse(body=body)

def set_cookie(request: HTTPRequest) -> HTTPResponse:
  return HTTPResponse(headers={"Set-Cookie": "username=TARO"})

def login(request: HTTPRequest) -> HTTPResponse:
  if request.method == "GET":
    body = render("login.html", {})
    return HTTPResponse(body=body)

  elif request.method == "POST":
    post_params = urllib.parse.parse_qs(request.body.decode())
    username = post_params["username"][0]

    headers = {"Location": "/welcome", "Set-Cookie": f"username={username}"}
    return HTTPResponse(status_code=302,headers=headers)

def welcome(request: HTTPRequest) -> HTTPResponse:
  cookie_header = request.headers.get("Cookie", None)

  # Cookieが送信されてきていなければ、ログインしていないとみなして/loginへリダイレクト
  if not cookie_header:
    return HTTPResponse(status_code=302, headers={"Location": "/login"})

  # str から list へ変換
  # ex) "name1=value1; name2=value2" => ["name1=value1", "name2=value2"]
  cookie_strings = cookie_header.split("; ")

  # list から dict へ変換
  # ex) ["name1=value1","name2=value2"] => {"name1": "value1", "name2": "value2"}
  cookies = {}
  for cookie_string in cookie_strings:
    name, value = cookie_string.split("=", maxsplit=1)
    cookies[name] = value

  # Cookieにusernameが含まれていなければ、ログインしていないとみなして/loginへリダイレクト
  if "username" not in cookies:
    return HTTPResponse(status_code=302, headers={"Location": "/login"})

  # Welcome画面を表示
  body = render("welcome.html", context={"username": cookies["username"]})

  return HTTPResponse(body=body)
