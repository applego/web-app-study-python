

from datetime import datetime
import os
import socket
import traceback
from threading import Thread
from typing import Optional, Tuple
import textwrap
from pprint import pformat
import re

class WorkerThread(Thread):
  # 実行ファイルのあるディレクトリ
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  # 静的配信するファイルを置くディレクトリ
  STATIC_ROOT = os.path.join(BASE_DIR, "static")

  # 拡張子とMIME Typeの対応
  MIME_TYPE = {
    "html": "text/html",
    "css": "text/css",
    "png": "image/png",
    "jpg": "image/jpg",
    "gif": "image/gif",
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
      request = self.client_socket.recv(4096)

      # クライアントから送られてきたデータをファイルに書き出す
      with open("server_recv.txt", "wb") as f:
        f.write(request)

      self.update_request_html(request)

      # HTTPリクエストをパースする
      method, path, http_version, request_header, request_body = self.parse_http_request(request)

      response_body: bytes
      content_type: Optional[str]
      response_line: str
      # pathが/nowのときは、現在時刻を表示するHTMLを生成する
      if path == "/now":
        html = f"""\
          <html>
          <body>
            <h1>Now: {datetime.now()}</h1>
          </body>
          </html>
          """
        response_body = textwrap.dedent(html).encode()

        # Content-Typeを指定
        content_type = "text/html"

        #　レスポンスラインを生成
        response_line = "HTTP/1.1 200 OK\r\n"

      # pathが/nowのときは、現在時刻を表示するHTMLを生成する
      elif path == "/show_request":
        html = f"""\
          <html>
          <body>
            <h1>Request Line:</h1>
            <p>
              {method} {path} {http_version}
            </p>
            <h1>Headers:</h1>
            <pre>
              {pformat(request_header)}
            </pre>
            <h1>Body:</h1>
            <pre>
              {request_body.decode("utf-8","ignore")}
            </pre>
          </body>
          </html>
          """
        response_body = textwrap.dedent(html).encode()

        # Content-Typeを指定
        content_type = "text/html"

        #　レスポンスラインを生成
        response_line = "HTTP/1.1 200 OK\r\n"

      else:
        try:
          # ファイルからレスポンスボディを生成
          response_body = self.get_static_file_content(path)

          # Content-Typeを指定
          content_type = None

          # レスポンスラインを生成
          response_line = "HTTP/1.1 200 OK\r\n"

        except OSError:
          # レスポンスを取得できなかった場合は、ログを出力して404を返す
          traceback.print_exc()

          response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
          content_type = "text/html"
          response_line = "HTTP/1.1 404 Not Found\r\n"

      # レスポンスヘッダーを生成
      response_header = self.build_response_header(path, response_body, content_type)

      # ヘッダーとボディを空行でくっつけた上でbytesに変換し、レスポンス全体を生成する
      response = (response_line + response_header + "\r\n").encode() + response_body

      # クライアントへレスポンスを送信する
      self.client_socket.send(response)

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
    request_html_path = os.path.join(self.STATIC_ROOT, "request.html")
    with open(request_html_path, "wt") as f:
      str_request = request.decode().replace('\r\n', '<br>');
      ## print(f"<html><body>{str_request}</body></html>")
      f.write(f"<html><body>{str_request}</body></html>")

  def parse_http_request(self, request: bytes) -> Tuple[str, str, str, dict, bytes]:
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

    return method, path, http_version, headers, request_body

  def get_static_file_content(self, path: str) -> bytes:
    """
    リクエストpathから、staticファイルの内容を取得する
    """
    # pathの先頭の/を削除し、相対パスにしておく
    relative_path = path.lstrip("/")
    # ファイルのpathを取得
    static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

    with open(static_file_path, "rb") as f:
      return f.read()

  def build_response_header(self,path:str,response_body:bytes,content_type:Optional[str]) -> str:
    """
    レスポンスヘッダーを構築する
    """

    # Content-Typeが指定されていない場合はpathから特定する
    if content_type is None:
      # pathから拡張子を取得
      if "." in path:
        ext = path.split(".", maxsplit=1)[-1]
      else:
        ext = ""
      # 拡張子からMIME Typeを取得
      # 知らない対応していない拡張子の場合はoctet-streamとする
      content_type = self.MIME_TYPE.get(ext,"application/octet-stream")

    # レスポンスヘッダーを生成
    response_header = ""
    response_header += f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
    response_header += "Host: HenaServer//0.1\r\n"
    response_header += f"Content-Length: {len(response_body)}\r\n"
    response_header += "Connection: Close\r\n"
    response_header += f"Content-Type: {content_type}\r\n"

    return response_header
