#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
from datetime import datetime

class WebSserver:
  """
  Webサーバを表すクラス
  """
  def serve(self):
    """
    サーバを起動する
    """

    print("=== サーバを起動します ===")

    try:
      # socketを生成
      server_socket = socket.socket()
      server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

      # socketをlocalhostのポート8080版に割り当てる
      server_socket.bind(("localhost", 8080))
      server_socket.listen(10)

      # 外部からの接続を待ち、接続があったらコネクションを確立する
      print("=== クライアントからの接続を待ちます ===")
      (client_socket, address) = server_socket.accept()
      print("=== クライアントとの接続が完了しました reote_address: {} ===".format(address))

      # クライアントから送られてきたデータを取得する
      request = client_socket.recv(4096)

      # クライアントから送られてきたデータをファイルに書き出す
      with open("server_recv.txt", "wb") as f:
        f.write(request)

      # レスポンスボディを生成
      response_body = "<html><body><h1>It works!</h1></body></html>"

      # レスポンスラインを生成
      response_line = "HTTP/1.1 200 OK\r\n"

      # レスポンスヘッダーを生成
      response_header = ""
      response_header += "Date: {}\r\n".format(datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'))
      response_header += "Host: HenaServer//0.1\r\n"
      response_header += "Content-Length: {}\r\n".format(len(response_body.encode()))
      response_header += "Connection: Close\r\n"
      response_header += "Content-Type: text/html\r\n"

      # ヘッダーとボディを空行でくっつけた上でbytesに変換し、レスポンス全体を生成する
      response = (response_line + response_header + "\r\n" + response_body).encode()

      # クライアントへレスポンスを送信する
      client_socket.send(response)

      # 返事は特に返さず、通信を終了させる
      client_socket.close()

    finally:
      print("=== サーバを停止します ===")

if __name__ == '__main__':
  server = WebSserver()
  server.serve()
