import socket
import traceback
import random
from concurrent.futures.thread import ThreadPoolExecutor
import numpy as np
import json
from threading import Lock
from networking import *


m = Lock()

app_info = {
    "yolov5s.pt": 0.03,
    "yolov5x.pt": 0.06
}

pow_info = {
    "yolov5s.pt": 100,
    "yolov5x.pt": 150,
}


class RootWidget():
    def __init__(self):
        self.is_connect = False
        self.host = None
        self.port = 8009
        self.imgID = 0
        self.inx = 0
        self.start = None
        self.det = None
        self.model = "yolov5x.pt"
        self.user = "epi3prqhpi9s9wq5"
        print(self.user)

        self.fps = 30
        self.avg_pow = 0
        self.avg_pow_hist = []
        self.edge_fps = 15

        self.time_l = []
        self.time_r = []

        self.send_controller = None

        self.local = False
        self.remote = False

        self.pow_hist = []
        self.time_hist = []
        self.remote_hist = []

    def connect(self):
        self.host = "192.168.0.18"
        self.port = 8001
        if not self.is_connect:
            try:
                self.s = socket.socket()
                self.s.connect((self.host, self.port))
                self.is_connect = True
            except:
                print(traceback.format_exc())
                return

            send_msg(self.s, json.dumps({"content": "handoff", "user": self.user}).encode("utf-8"))

            data = recv_msg(self.s)
            info = json.loads(str(data.decode('utf-8')))
            print("msg:", info)
            if "service" in info and info["service"] == "ready":
                self.start = time.time()
                self.imgsz = info["imgsz"]
            t2 = threading.Thread(target=self.batter_monitor, args=())
            t2.start()

            self.run()

        else:
            self.s.close()
            self.is_connect = False

    def batter_monitor(self):
        start = time.time()
        while True:
            if time.time() - start > 0.5:
                pow = pow_info[self.model] * (self.fps - self.edge_fps)
                self.pow_hist.append(int(pow))
                print(self.pow_hist)
                start = time.time()
            else:
                pass

    def run(self):
        for i in range(2000):
            start_t = time.time()
            items = [
                ("local", self.fps - self.edge_fps),
                ("remote", self.edge_fps)
            ]

            with ThreadPoolExecutor(2) as executor:
                results = executor.map(self.process, items)

            time_1, time_2 = results
            self.time_l.append(time_1)
            self.time_r.append(time_2)

            while time.time() - start_t <= 8:
                pass

            print(
                f"\t video segment {i} (partition {self.fps - self.edge_fps}/{self.edge_fps} #{i}) finished in {round(time.time() - start_t, 4)}/{time_1, time_2},pow={round(np.average(self.pow_hist), 4)}")

            self.avg_pow = round(np.average(self.pow_hist), 4)
            self.avg_pow_hist.append(self.avg_pow)
            if i > 0 and i % 10 == 0:
                print("pow_hist=", self.avg_pow_hist)
            self.pow_hist = []

    def process(self, items):
        p_type, fps = items
        if p_type == "local":
            start_t = time.time()
            time.sleep(app_info[self.model] * fps)
            return round(time.time() - start_t, 4)
        else:
            start_t = time.time()
            if fps > 0:
                self.send_data(fps)
            return round(time.time() - start_t, 4)

    def send_data(self, fps):
        energy_info = {}
        try:
            """
                wait for start_to_send command
            """
            while True:
                data = recv_msg(self.s)
                info = json.loads(str(data.decode('utf-8')))
                if "start_to_send" in info and info["start_to_send"] is True:
                    print(info)
                    self.edge_fps = info["fps"]
                    self.imgsz = info["imgsz"]
                    self.alc_server = info["server"]
                    break
            """
                send image
            """

            data = "111111111111111111111111111111111"

            if len(self.time_r) > 0:
                msg = {"data": data, "avg_pow": self.avg_pow, "user": self.user, "remote_r": self.time_r[-1]}
            else:
                msg = {"data": data, "avg_pow": self.avg_pow, "user": self.user}
            encoding = json.dumps(msg).encode("utf-8")
            send_msg(self.s, encoding)

            while True:
                try:
                    data = recv_msg(self.s)
                    info = json.loads(str(data.decode('utf-8')))
                    print(info)
                    if "status" in info:
                        pass
                    elif "results" in info:
                        break
                except:
                    print(traceback.format_exc())
            start = time.time()
        except:
            print(traceback.format_exc())


if __name__ == '__main__':
    r = RootWidget()
    r.connect()
