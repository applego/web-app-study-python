#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import socket
import traceback
from datetime import datetime
from typing import Tuple

class WebSserver:
  """
  Webサーバを表すクラス
  """

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

  def serve(self):
    """
    サーバを起動する
    """

    print("=== サーバを起動します ===")

    try:
      # socketを生成
      server_socket = self.create_server_socket()

      while True:
        # 外部からの接続を待ち、接続があったらコネクションを確立する
        print("=== クライアントからの接続を待ちます ===")
        (client_socket, address) = server_socket.accept()
        print(f"=== クライアントとの接続が完了しました reote_address: {address} ===")

        try:
          # クライアントと通信をして、リクエストを処理する
          self.handle_client(client_socket)

        except Exception as e:
          # リクエストの処理中に雷害が発生した場合はコンソールにエラーログを出力し、
          # 処理を続行する
          print("=== リクエストの処理中にエラーが発生しました ===")
          traceback.print_exc()

        finally:
          # 例外が発生した場合も、発生しなかった場合も、TCP通信のcloseは行う
          client_socket.close()

    finally:
      print("=== サーバを停止します ===")

  def create_server_socket(self) -> socket:
    """
    通信を待ち受けるためのserver_socketを生成する
    :return:
    """
    # socketを生成
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # socketをlocalhostのポート8080版に割り当てる
    server_socket.bind(("localhost", 8080))
    server_socket.listen(10)
    return server_socket

  def handle_client(self, client_socket: socket) -> None:
    """
    クライアントと接続済みのsocketを引数として受け取り、
    リクエストを処理してレスポンスを送信する
    """

    # クライアントから送られてきたデータを取得する
    request = client_socket.recv(4096)

    # クライアントから送られてきたデータをファイルに書き出す
    with open("server_recv.txt", "wb") as f:
      f.write(request)

    self.update_request_html(request)

    # HTTPリクエストをパースする
    method, path, http_version, request_header, request_body = self.parse_http_request(request)

    try:
      # ファイルからレスポンスボディを生成
      response_body = self.get_static_file_content(path)

      # レスポンスラインを生成
      response_line = "HTTP/1.1 200 OK\r\n"

    except OSError:
      # ファイルが見つからない場合は4040を返す
      response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
      response_line = "HTTP/1.1 404 Not Found\r\n"

    # レスポンスヘッダーを生成
    response_header = self.build_response_header(path, response_body)

    # ヘッダーとボディを空行でくっつけた上でbytesに変換し、レスポンス全体を生成する
    response = (response_line + response_header + "\r\n").encode() + response_body

    # クライアントへレスポンスを送信する
    client_socket.send(response)

  def update_request_html(self, request: bytes) -> None:
    """
    リクエストの内容をrequest.htmlに書き込む
    """
    # +
    # requestをrequest.htmlに書き込む
    request_html_path = os.path.join(self.STATIC_ROOT, "request.html")
    with open(request_html_path, "wt") as f:
      str_request = request.decode().replace('\r\n', '<br>');
      print(f"<html><body>{str_request}</body></html>")
      f.write(f"<html><body>{str_request}</body></html>")

  def parse_http_request(self, request: bytes) -> Tuple[str, str, str, bytes, bytes]:
    """
    HTTPリクエストを
    1. method: str
    2. path: str
    3. http_version: str
    4. request_header: bytes
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

    # リクエストラインをパースする
    method, path, http_version = request_line.decode().split(" ")

    return method, path, http_version, request_header, request_body

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

  def build_response_header(self,path:str,response_body:bytes) -> str:
    """
    レスポンスヘッダーを構築する
    """
      # ヘッダー生成のためにContent-Typeを取得しておく
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


if __name__ == '__main__':
  server = WebSserver()
  server.serve()
