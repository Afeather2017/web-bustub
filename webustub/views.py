from django.shortcuts import render
from django.http import HttpResponse
import socket, time, threading
import os

class SqlExecutor(object):
    def __init__(self, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("localhost", port))
        self.__ReadResult()

    def __ReadResult(self):
        self.data = ""
        while True:
            data = self.client_socket.recv(512)
            if len(data) == 0:
                self.client_socket.close()
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

    def __del__(self):
        self.client_socket.close()

def DefaultKey(value, key):
    if value == "" or value == None:
        return key
    return value

global_terminal_id = 0;
id_to_socket = {}
timeout = {}
lock = threading.Lock()

def Cleanup():
    if len(timeout) == 0:
        return
    deleted = []
    for tid, tm in timeout.items():
        if time.time() - tm >= 60 * 6:
            print(tid, "closed cuz timeout")
            deleted += [tid]
    for tid in deleted:
        del timeout[tid]
        del id_to_socket[tid]
    if len(timeout) == 0:
        os.system("killall bustub-nc-shell")

def Bustub(request):
    global lock
    with lock:
        Cleanup()
        global global_terminal_id
        terminal_id = DefaultKey(request.GET.get("id"), "None")
        if terminal_id == "None":
            terminal_id = 'tid_' + str(global_terminal_id)
            global_terminal_id += 1
            id_to_socket[terminal_id] = SqlExecutor(23333)
            timeout[terminal_id] = time.time()
        sql = DefaultKey(request.GET.get("sql"), "")
        sql = sql.strip()
        print("sql:", sql)
        print("tid:", terminal_id)
        if len(sql) == 0:
            return render(request, "bustub.html",
                          {"id": terminal_id, "results": ["There is no sql!"]})


        if sql.startswith("\\"):
            sql = " ".join(sql.split())
        elif not sql.endswith(";"):
            return render(request, "bustub.html",
                         {"id": terminal_id,
                         "results": ["Your sql must be ends with ';'!"]})
        if '"' in sql:
            return render(request, "bustub.html",
                         {"id": terminal_id,
                         "results": ["You cannot use \" in any sql",
                                     "use ' instead."]})
        data = ""
        try:
            executor = id_to_socket[terminal_id]
            timeout[terminal_id] = time.time()
            data = executor.Execute(sql)
            print("data:", data)
            results = data.split("\n")
        except Exception as e:
            results = ["transaction aborted, commited, or never exist"]
            if terminal_id in timeout:
                results += [id_to_socket[terminal_id].GetData()]
                timeout[terminal_id] = 0
        return render(request, "bustub.html", {"id": terminal_id, "results": results})

