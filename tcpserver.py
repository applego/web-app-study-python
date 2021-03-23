#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket

class TCPSserver:
  """
  TCP通史位を行うサーバを表すクラス
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

      # クライアントへ送信するレスポンスデータをファイルから取得する
      with open("server_send.txt", "rb") as f:
        response = f.read()

      # クライアントへレスポンスを送信する
      client_socket.send(response)

      # 返事は特に返さず、通信を終了させる
      client_socket.close()

    finally:
      print("=== サーバを停止します ===")

if __name__ == '__main__':
  server = TCPSserver()
  server.serve()
