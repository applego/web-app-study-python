#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket

class TCPClient:
  """
  TCP通信を行うクライアントを表すクラス
  """
  def request(self):
    """
    サーバへリクエストを送信する
    """

    print("=== クライアントを起動します ===")

    try:
      # socketを生成
      client_socket = socket.socket()
      client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

      # サーバと接続する
      print("=== サーバと接続します ===")
      client_socket.connect(("127.0.0.1", 80))
      print("=== サーバとの接続が完了しました ===")

      # サーバに送信するリクエストを、ファイルから取得する
      with open("client_send.txt", "rb") as f:
        request = f.read()
        print(request)

      # サーバへリクエストを送信する
      client_socket.send(request)

      # サーバからレスポンスが送られてくるのを待ち、取得する
      response = client_socket.recv(4096)

      # レスポンスの内容を、ファイルに書き出す
      with open("client_recv.txt", "wb") as f:
        f.write(response)

      # 通信を終了させる
      client_socket.close()

    finally:
      print("=== クライアントを停止します。 ===")

if __name__ == '__main__':
  client = TCPClient()
  client.request()
