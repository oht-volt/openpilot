
import json
import time
import socket
from threading import Thread

current_milli_time = lambda: int(round(time.time() * 1000))

class RoadSpeedLimiter:
  def __init__(self):
    self.json = None
    self.last_updated = 0
    self.slowing_down = False
    self.last_exception = None

    thread = Thread(target=self.udp_recv, args=[])
    thread.setDaemon(True)
    thread.start()

  def udp_recv(self):

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:

      try:
        sock.bind(('127.0.0.1', 843))

        while True:

          try:
            data, addr = sock.recvfrom(2048)
            self.json = json.loads(data.decode())
            self.last_updated = current_milli_time()

          except:
            self.json = None

      except Exception as e:
        self.last_exception = e

  def get_val(self, key):

    if self.json is None:
      return None

    if key in self.json:
      return self.json[key]
    return None

  def get_max_speed(self, CS, v_cruise_kph):

    if current_milli_time() - self.last_updated > 1000 * 20:

      if self.last_exception is not None:
        log = str(self.last_exception)
      else:
        log = "expired: {:d}, {:d}".format(current_milli_time(), self.last_updated)

      self.slowing_down = False
      return 0, 0, 0, log

    try:

      road_limit_speed = self.get_val('road_limit_speed')
      is_highway = self.get_val('is_highway')

      cam_limit_speed_left_dist = self.get_val('cam_limit_speed_left_dist')
      cam_limit_speed = self.get_val('cam_limit_speed')

      section_limit_speed = self.get_val('section_limit_speed')
      # section_avg_speed = self.get_val('section_avg_speed')
      section_left_dist = self.get_val('section_left_dist')
      # section_left_time = self.get_val('section_left_time')

      if is_highway is not None:
        if is_highway:
          MIN_LIMIT = 60
          MAX_LIMIT = 120
        else:
          MIN_LIMIT = 30
          MAX_LIMIT = 100
      else:
        MIN_LIMIT = 30
        MAX_LIMIT = 120

      log = "RECV: " + str(is_highway)
      log += ", " + str(cam_limit_speed)
      log += ", " + str(cam_limit_speed_left_dist)
      log += ", " + str(section_limit_speed)
      log += ", " + str(section_left_dist)

      if cam_limit_speed_left_dist is not None and cam_limit_speed is not None and cam_limit_speed_left_dist > 0:
        if MIN_LIMIT <= cam_limit_speed <= MAX_LIMIT and (self.slowing_down or cam_limit_speed_left_dist < CS.vEgo * 10):

          self.slowing_down = True
          return cam_limit_speed, cam_limit_speed, cam_limit_speed_left_dist, log

        self.slowing_down = False
        return 0, cam_limit_speed, cam_limit_speed_left_dist, log

      elif section_left_dist is not None and section_limit_speed is not None and section_left_dist > 0:
        if MIN_LIMIT <= section_limit_speed <= MAX_LIMIT:
          self.slowing_down = True
          return section_limit_speed, section_limit_speed, section_left_dist, log

        self.slowing_down = False
        return 0, section_limit_speed, section_left_dist, log

    except Exception as e:
      log = "Ex: " + str(e)
      pass

    self.slowing_down = False
    return 0, 0, 0, log


road_speed_limiter = None


def road_speed_limiter_get_max_speed(CS, v_cruise_kph):
  global road_speed_limiter
  if road_speed_limiter is None:
    road_speed_limiter = RoadSpeedLimiter()

  return road_speed_limiter.get_max_speed(CS, v_cruise_kph)
