from django.shortcuts import render
from django.http import HttpResponse
import socket

class SqlExecutor(object):
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("localhost", 23333))
        self.__ReadResult()

    def __ReadResult(self):
        self.data = ""
        while True:
            data = self.client_socket.recv(512)
            data = data.decode()
            self.data += data
            if self.data.endswith("bustub> "):
                self.data = self.data[:-len("bustub> ")]
                break

    def GetData(self):
        return self.data

    def Execute(self, sql):
        self.client_socket.send(sql.encode())
        self.__ReadResult()
        return self.data

executor = SqlExecutor()

def DefaultKey(value, key):
    if value == "" or value == None:
        return key
    return value

def Bustub(request):
    sql = DefaultKey(request.GET.get("sql"), "")
    print("try execute sql", sql)
    sql = sql.strip()
    if len(sql) == 0:
        return render(request, "bustub.html", {"results": ["There is no sql!"]})

    if sql.startswith("\\"):
        sql = " ".join(sql.split())
    elif not sql.endswith(";"):
        return render(request, "bustub.html",
                      {"results": ["Your sql must be ends with ';'!"]})
    data = executor.Execute(sql)
    print(data)
    results = data.split("\n")
    return render(request, "bustub.html", {"results": results})
