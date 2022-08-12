import base64
import os
import json
from threading import Lock
from _thread import *
import socket
import numpy as np
import traceback
import argparse
from pathlib import Path
import cv2
import yaml

from networking import *


m = Lock()

app_info = {                # seconds
    "yolov5s.pt": 0.03,
    "yolov5x.pt": 0.06
}


class Server:
    def __init__(self):
        self.confusion_matrix = None
        self.host = None
        self.port = None
        self.s = None
        self.ul_channel = []
        self.dl_channel = {}
        self.net = None
        self.pose = None
        self.processed = {}
        self.inx = 0
        self.requests = {}
        self.start = {}
        self.gpu_utilization = []
        self.monitor_on = False
        self.services = {}

        self.device = None
        self.iouv = None
        self.niou  = None
        self.half = None
        self.imgsz = 640

        self.dataset = None

        self.stats = {}
        self.number = {}

        self.segment_time = {}
        self.total_IDLE_time = 0

        self.initial_cfg = {
            # "9fd3b96565dbebe8": 0.2,
            # "204dfa87f106ca64": 0.8
        }
        self.inference = {}

    def connect_to_urb(self, host, port):
        try:
            print("connecting to urb {} ...".format(host))
            urb_channel = socket.socket()
            urb_channel.connect((host, port))
            start_new_thread(self.down_link_handler, (urb_channel, host))
            print("connected")
            while True:
                try:
                    data = recv_msg(urb_channel)
                    info = json.loads(str(data.decode('utf-8')))

                    task = str(self.inx).zfill(8) + "_" + info["user"]

                    self.inx += 1

                    if info["user"] not in self.requests:
                        self.requests[info["user"]] = []
                        self.segment_time[info["user"]] = 0

                    m.acquire()
                    if info["user"] not in self.inference:
                        self.inference[info["user"]] = []
                    m.release()

                    if "server" in info:
                        self.initial_cfg[info["user"]] = info["server"]

                    m.acquire()
                    self.requests[info["user"]].append(
                        {"img_file": task, "user": info["user"], "segment": info["segment"],
                              "imgsz": info["imgsz"], "model": info["model"], "total": info["total"]})

                    m.release()
                except error:
                    print(traceback.format_exc())
                    print("urb", host, "disconnected")
        except (RuntimeError, TypeError, NameError):
            urb_channel.close()
            print(traceback.format_exc())

    # 7b0f5c1dbf33e4b2  70
    # db846572170927ce  30

    def down_link_handler(self, urb_channel, urb_addr):

        while True:
            if len(self.initial_cfg.items()) == 1:
                break

        time_window = 0.25
        initialized = False
        while True:
            try:
                total_used = 0
                for user, alloc_time in self.initial_cfg.items():
                    total_used += alloc_time
                idle = 1 - total_used

                if idle > 0:
                    print("GPU IDLE {} = {}".format(user, round(idle * time_window, 4)))
                    time.sleep(idle * time_window)
                    for user1, alloc_time1 in self.initial_cfg.items():
                        if user1 in self.requests and len(self.requests[user1]) != 0:
                            self.segment_time[user1] += idle * time_window
                            print("+ {}:{}".format(user1, round(idle * time_window, 4)))
                for user, alloc_time in self.initial_cfg.items():
                    if user in self.requests and len(self.requests[user]) == 0 or user not in self.requests:
                        print("IDLE because of {} = {}".format(user, round(self.initial_cfg[user] * time_window, 4)))
                        time.sleep(self.initial_cfg[user] * time_window)
                        for user1, alloc_time1 in self.initial_cfg.items():
                            if user1 != user and user1 in self.requests and len(self.requests[user1]) != 0:
                                self.segment_time[user1] += self.initial_cfg[user] * time_window
                                print("+ {}:{}".format(user1, round(self.initial_cfg[user] * time_window, 4)))
                        continue

                    if not initialized:
                        last_busy_time = time.time()
                        initialized = True

                    processed = 0
                    i_time = 0
                    while len(self.requests[user]) > 0:
                        self.total_IDLE_time += time.time() - last_busy_time
                        # print("IDLE = {}".format(self.total_IDLE_time))

                        req = self.requests[user][0]
                        msg = {"data": "111111111111111111111111111111111"}
                        start = time.time()
                        time.sleep(app_info[req["model"]])
                        msg["inference"] = round(time.time() - start, 4)
                        self.inference[req["user"]].append(msg["inference"])
                        self.segment_time[req["user"]] += msg["inference"]
                        i_time += msg["inference"]

                        if req["user"] not in self.stats:
                            self.stats[req["user"]] = []
                            self.number[req["user"]] = 0

                        self.number[req["user"]] += 1

                        map50 = None
                        inference = None
                        segment = None
                        if self.number[req["user"]] >= req["total"]:
                            start_r = time.time()
                            self.stats[req["user"]] = []
                            self.number[req["user"]] = 0
                            inference = np.average(self.inference[req["user"]])
                            segment = self.segment_time[req["user"]]
                            self.inference[req["user"]] = []
                            self.segment_time[req["user"]] = 0
                            print("+ eva", round(time.time() - start_r, 4))

                        msg["seg_time"] = segment
                        msg["inference"] = inference
                        msg["mAP50"] = map50
                        msg["model"] = req["model"]
                        msg["imgsz"] = req["imgsz"]
                        msg["FPS"] = 0
                        msg["user"] = req["user"]
                        msg["total_IDLE_time"] = self.total_IDLE_time
                        msg["segment"] = req["segment"]
                        send_msg(urb_channel, json.dumps(msg).encode("utf-8"))
                        self.requests[user].remove(req)
                        processed += 1
                        last_busy_time = time.time()
                        if i_time >= self.initial_cfg[user] * time_window:
                            break
                    print("{}[{}%]: processed {}, remaining {}, latency {}"
                          .format(user, round(self.initial_cfg[user] * 100),
                                  processed,
                                  len(self.requests[user]),
                                  round(np.average(self.inference[req["user"]]), 4)))
            except:
                print(traceback.format_exc())
                print("urb", urb_addr, "disconnected")


if __name__ == '__main__':
    server = Server()
    server.connect_to_urb(host='192.168.0.18', port=8009)

