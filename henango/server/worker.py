import os
import re
import traceback
from datetime import datetime
from socket import socket
from threading import Thread
from typing import Optional, Tuple

import settings
from henango.http.request import HTTPRequest
from henango.http.response import HTTPResponse
from urls import url_patterns
from henango.urls.resolver import URLResolver


class Worker(Thread):
  # 拡張子とMIME Typeの対応
  MIME_TYPE = {
    "html": "text/html; charset=UTF-8",
    "css": "text/css",
    "png": "image/png",
    "jpg": "image/jpg",
    "gif": "image/gif",
  }

  # ステータスコードとステータスラインの対応
  STATUS_LINES = {
    200: "200 OK",
    404: "404 Not Found",
    405:"405 Method Not Allowed",
  }

  def __init__(self, client_socket: socket, address: Tuple[str, int]):
    super().__init__()

    self.client_socket = client_socket
    self.client_address = address

  def run(self) -> None:
    """
    クライアントと接続済のsocketを引数として受け取り、
    リクエストを処理してレスポンスを送信する
    """

    try:

      # クライアントから送られてきたデータを取得する
      request_bytes = self.client_socket.recv(4096)

      # クライアントから送られてきたデータをファイルに書き出す
      with open("server_recv.txt", "wb") as f:
        f.write(request_bytes)

      self.update_request_html(request_bytes)

      # HTTPリクエストをパースする
      request = self.parse_http_request(request_bytes)

      # URL解決を試みる
      view = URLResolver().resolve(request)

      # レスポンスを生成する
      response = view(request)

      # レスポンスラインを生成
      response_line = self.build_response_line(response)

      # レスポンスヘッダーを生成
      response_header = self.build_response_header(response, request)


      # ヘッダーとボディを空行でくっつけた上でbytesに変換し、レスポンス全体を生成する
      response_bytes = (response_line + response_header + "\r\n").encode() + response.body

      # クライアントへレスポンスを送信する
      self.client_socket.send(response_bytes)

    except Exception as e:
      # リクエストの処理中に雷害が発生した場合はコンソールにエラーログを出力し、
      # 処理を続行する
      print("=== リクエストの処理中にエラーが発生しました ===")
      traceback.print_exc()

    finally:
      # 例外が発生した場合も、発生しなかった場合も、TCP通信のcloseは行う
      print(f"=== Worker: クライアントとの通信を終了します remote_address: {self.client_address} ===")
      self.client_socket.close()

  def update_request_html(self, request: bytes) -> None:
    """
    リクエストの内容をrequest.htmlに書き込む
    """
    # +
    # requestをrequest.htmlに書き込む
    default_static_root = os.path.join(os.path.dirname(__file__), "../../static")
    static_root = getattr(settings, "STATIC_ROOT", default_static_root)

    request_html_path = os.path.join(static_root, "request.html")
    with open(request_html_path, "wt") as f:
      str_request = request.decode().replace('\r\n', '<br>');
      ## print(f"<html><body>{str_request}</body></html>")
      f.write(f"<html><body>{str_request}</body></html>")

  def parse_http_request(self, request: bytes) -> HTTPRequest:
    """
    HTTPリクエストを
    1. method: str
    2. path: str
    3. http_version: str
    4. request_header: dict
    5. request_body: bytes
    に分割/変換する
    """
    # リクエスト全体を
    # 1. リクエストライン（１行目）
    # 2. リクエストヘッダー（２行目〜空行）
    # 3. リクエストボディ（空行〜）
    # にパースする

    request_line, remain = request.split(b"\r\n", maxsplit=1)
    request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

    # リクエストラインを文字列に変換してパースする
    method, path, http_version = request_line.decode().split(" ")

    # リクエストヘッダーを辞書にパースする
    headers = {}
    for header_row in request_header.decode().split("\r\n"):
      key, value = re.split(r": *", header_row, maxsplit=1)
      headers[key] = value

    return HTTPRequest(path, method, http_version, headers, request_body)

  def build_response_line(self, response: HTTPResponse) -> str:
    """
    レスポンスラインを構築する
    """
    status_line = self.STATUS_LINES[response.status_code]
    return f"HTTP/1.1 {status_line}"


  def build_response_header(self,response:HTTPResponse,request:HTTPRequest) -> str:
    """
    レスポンスヘッダーを構築する
    """

    # Content-Typeが指定されていない場合はpathから特定する
    if response.content_type is None:
      # pathから拡張子を取得
      if "." in request.path:
        ext = request.path.split(".", maxsplit=1)[-1]
      else:
        ext = ""
      # 拡張子からMIME Typeを取得
      # 知らない対応していない拡張子の場合はoctet-streamとする
      response.content_type = self.MIME_TYPE.get(ext,"application/octet-stream")

    # レスポンスヘッダーを生成
    response_header = ""
    response_header += f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
    response_header += "Host: HenaServer//0.1\r\n"
    response_header += f"Content-Length: {len(response.body)}\r\n"
    response_header += "Connection: Close\r\n"
    response_header += f"Content-Type: {response.content_type}\r\n"

    return response_header
