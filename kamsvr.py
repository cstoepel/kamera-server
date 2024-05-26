#!/usr/bin/python3
VERSION  = "1.0.18a"
# import {{{1
import os
import sys
import time
import errno
import signal
import threading
from subprocess import check_output
from argparse import ArgumentParser
import socket
import gpiozero
import picamera
import picamera.array
import numpy
import cv2
import asyncio
import websockets
import base64
import astral.sun
# from apscheduler.schedulers.background import BackgroundScheduler
#}}}1
# global var {{{1
HISTORY           = ""
VERBOSE           = False # show output to stdout
                          # command line option -v, default is no output
DEBUGLEVEL        = 9     # default debug level, wird im config file überschrieben
                          # higher means more verbose, 0 is off
                          # debug.out("text", level) level=1  high importance
                          #                          level=9  low  importance (default)
DEBUG_OPENCV      = False
HOME_DIR          = os.environ['HOME']
BASE_DIR          = HOME_DIR + "/data"
# LOGFILE           = HOME_DIR + "/debug.txt"
CONFIG_FILE       = HOME_DIR + "/.ks.conf"
MOTION_MASK       = HOME_DIR + "/motion_mask.png"
RASPI             = check_output(['cat', '/proc/device-tree/model']).decode()
# RASPI_LIST        = RASPI.decode().split()
# RASPI_TYPE        = RASPI_LIST[2]
HOSTNAME          = socket.gethostname()
HOSTADDRESS       = socket.gethostbyname(HOSTNAME)
MULTICASTADDR     = ""
START_MULTICAST   = False
TIMESTR_DEBUG     = "%Y-%m-%d %H%M %S"
TIMESTR_PIR       = "%Y-%m-%d %H%M %S"
TIMESTR_PHOTO     = "%Y-%m-%d_%H-%M-%S"
TIMESTR_PHOTO_DIR = "%Y-%m-%d"
TIMESTR_VIDEO     = "%Y-%m-%d_%H-%M-%S"
TIMESTR_VIDEO_DIR = "%Y-%m-%d"
TIMEOFFSET        = 1
LASTPHOTO         = None
COL_RED           = "\033[31m";
COL_GREEN         = "\033[32m";
COL_YELLOW        = "\033[33m";
COL_BLUE          = "\033[34m";
COL_MAGENTA       = "\033[35m";
COL_CYAN          = "\033[36m";
COL_WHITE         = "\033[37m";
COL_BRIGHT        = "\033[1m";
COL_RESET         = "\033[0m";
COL_DEFAULT       = "\033[39;49m";
COL_ok            = COL_GREEN
COL_warning       = COL_YELLOW
COL_error         = COL_RED
COL_init          = COL_BRIGHT + COL_WHITE
COL_del           = COL_BLUE
COL_run           = COL_CYAN
COL_start         = COL_CYAN
COL_stop          = COL_BLUE
#___Bewegungsmelder__________
# PIN_PIR1   = 14  # pin  8
# PIN_PIR2   = 15  # pin 10
PIN_PIR3   = 18  # pin 12
#___Kamera___________________
VIDEORES = ( 640, 480)
photores = (1296, 972)
jpgquality  = 10
kamera_lock = threading.Lock()
PIRCAM      = False
#___Konfiguration____________
configurations = {'base': []}
curr_config = 'base'
#___WebSockets_______________
ws_set = set()

WS_PORT = 4000
#___HELP_____________________{{{2
HELPSTR = f"""
                ___________GPIO__________PIN__________GPIO__________________
                           3.3         1     2        5.0
                SDA<------>[02]        3     4        5.0
                SCL<------>[03]        5     6        GND
                1W <------>[04]        7     8        [14]--->TX     SER
                           GND         9    10        [15]<---RX     SER
    A           I/O<------>[17]       11    12        [18]<---PIR1   AUX0
    A           I/O<------>[27]       13    14        GND
    A           I/O<------>[22]       15    16        [23]<---PIR2   AUX0
    A                      3.3        17    18        [24]<--->I/O   AUX1
    A           MOSI<----->[10]       19    20        GND
    A           MISO<----->[09]       21    22        [25]<--->I/O   AUX1
    A           SCKL<----->[11]       23    24        [08]<---right stop Motor
    A                      GND        25    26        [07]<---left  stop Motor
                           DNC        27    28        DNC
    B           CLOCK<-----[05]       29    30        GND
    B           LATCH<-----[06]       31    32        [12]--->A      M
    B           OE<--------[13]       33    34        GND            O
    B           DATA<------[19]       35    36        [16]--->B      T
    B           I/O<------>[26]       37    38        [20]--->C      O
                            GND       39    40        [21]--->D      R
Stecker A     8 Pins (GND, 3,3V)
Stecker B     6 Pins (GND      )
Stecker AU0X  4 Pins (GND, 5,0V)
Stecker AUX1  4 Pins (GND, 5,0V)
Stecker Motor 8 Pins (GND, 5,0V)

__Resolution__Aspect_________fps________Vid_Img_FoV__Binning__
V1
1  1920x1080    16:9    1 <  fps <= 30   x      Part  None
2  2592x1944    4:3     1 <  fps <= 15   x   x  Full  None
3  2592x1944    4:3   1/6 <= fps <= 1    x   x  Full  None
4  1296x972     4:3     1 <  fps <= 42   x      Full  2x2
5  1296x730    16:9     1 <  fps <= 49   x      Full  2x2
6  640x480      4:3    42 <  fps <= 60   x      Full  4x4
7  640x480      4:3    60 <  fps <= 90   x      Full  4x4
__Resolution__Aspect_________fps________Vid_Img_FoV__Binning__
V2
1 1920x1080   16:9    1/10 <= fps <= 30   x      Partial  None
2 3280x2464    4:3    1/10 <= fps <= 15   x  x   Full     None
3 3280x2464    4:3    1/10 <= fps <= 15   x  x   Full     None
4 1640x1232    4:3    1/10 <= fps <= 40   x      Full     2x2
5 1640x922    16:9    1/10 <= fps <= 40   x      Full     2x2
6 1280x720    16:9      40 < fps <= 90    x      Partial  2x2
7  640x480     4:3      40 < fps <= 90    x      Partial  2x2

__COMMANDS____________________________________________________
sh-get
sh-set <xxxx>     x=0|1
sh-sw  n x        x=0|1
quit
status1    Ausgabe für Terminal
status2    Ausgabe zum parsen
status3    Quick Status
help
photo
record
recstop
osd0       On Screen Display
osd1
config-load
config-set
turn-right <n>
turn-left  <n>
debug <n>     n = 0..9
startvid <client_port> <ip:port>   ... server socket is bound to spec address
startvid <client_port> 0           ... start videostream to calling client at port
mc-start                           ... start multicast
motion-photo-start
motion-photo-stop
photo
photo-last

ws-send {socket.gethostname()}:{WS_PORT} "command"
______________________________________________________________
"""
#}}}2

#}}}1
class Debug(object): #{{{1

	def __init__(self, debug_level, timestr):
		self.debug_level   = debug_level
		self.timestr       = timestr
		self.default_color = ""
		self.init_color    = ""
		self.del_color     = ""
		self.run_color     = ""
		self.start_color   = ""
		self.stop_color    = ""
		self.class_color   = ""
		self.func_color    = ""
		self.reset_color   = ""


	def __call__(self, level):
		def decorator(func):
			def function_wrapper(*args, **kwargs):
				self.do_before(level, func, *args)
				result = func(*args, **kwargs)
				self.do_after(level, func, *args)
				return result
			return function_wrapper
		return decorator

	def do_before(self, level, func, *args):
		if   func.__name__ == "__init__": color = self.init_color
		elif func.__name__ == "__del__" : color = self.del_color
		elif func.__name__ == "run"     : color = self.run_color
		elif func.__name__ == "start"   : color = self.start_color
		elif func.__name__ == "stop"    : color = self.stop_color
		else                            : color = self.default_color
		if len(args) > 0:
			name = args[0].__class__.__name__
		else:
			name = "function"
		func_name  = func.__name__
		self.out(f"{self.class_color}{name}:{self.reset_color}{self.func_color} {func_name}()", level, color)

	def do_after(self, func, *args):
		pass

	def out(self, text, level = 9, color = ""):
		if self.debug_level >= level:
			print(f"{time.strftime(self.timestr)} {COL_CYAN}{str(level)}{COL_RESET} : {color}{text}{COL_RESET}", flush=True)
#}}}1

debug = Debug(DEBUGLEVEL, TIMESTR_DEBUG)
debug.default_color = COL_DEFAULT
debug.init_color    = COL_BRIGHT + COL_WHITE
debug.del_color     = COL_BLUE
debug.run_color     = COL_CYAN
debug.start_color   = COL_BRIGHT + COL_CYAN
debug.stop_color    = COL_BLUE
debug.class_color   = COL_BRIGHT + COL_WHITE
debug.func_color    = COL_WHITE
debug.reset_color   = COL_RESET

class Job(object): #{{{1
	@debug(1)
	def __init__(self, name, active, hour, minute, func, args):
		self.name   = name
		self.hour   = hour
		self.minute = minute
		self.m      = 3600 * self.hour + self.minute
		self.active = active
		self.func   = func
		self.args   = args
#}}}1
class Cron(threading.Thread): #{{{1
	@debug(1)
	def __init__(self):
		threading.Thread.__init__(self)
		self.name       ="CRON"
		self.deamon     = True
		self.is_running = True
		self.jobs = []

	@debug(1)
	def run(self):
		self.is_running = True
		while self.is_running:
			t = time.localtime()
			tm = 3600 * t.tm_hour + t.tm_min
			for j in self.jobs:
				if j.active > 0 and tm == j.m :
					j.func(*j.args)
			n = 0
			while n < 50:
				if self.is_running == False:
					debug.out(f"{self.name}: ENDE", 1)
					return
				time.sleep(1)
				n += 1
		debug.out(f"{self.name}: ENDE", 1)

	@debug(1)
	def stop(self):
		debug.out(f"{self.name}: stopping...", 1)
		self.is_running = False

	@debug(1)
	def add(self, name, active, hour, minute, func, args):
		j = Job(name, active, hour, minute, func, args)
		self.jobs.append(j)

	@debug(1)
	def reschedule(self, name, active, hour, minute):
		for i, j in enumerate(self.jobs):
			if j.name == name:
				self.jobs[i].active = active
				self.jobs[i].hour   = hour
				self.jobs[i].minute = minute
				self.jobs[i].m      = 3600 * hour + minute
				debug.out(f"{self.name}: reschedule {j.name}  {j.active} {j.hour}:{j.minute} {j.m}")
	
	@debug(1)
	def list(self):
		s = ""
		n = 0
		for j in self.jobs:
			debug.out(f"{self.name}: list {j.name}  {j.active} {j.hour}:{j.minute} {j.m}", 9)
			s += f"{n} {j.name:12} {j.active} {j.hour:02}:{j.minute:02} {j.m:05}\n"
			n += 1
		return s
	
	@debug(1)
	def sort(self):
		self.jobs.sort(key = lambda job: job.m)

	@debug(1)
	def set_time_state(self):
		t = time.localtime()
		tm = 3600 * t.tm_hour + t.tm_min
		for j in self.jobs:
			if j.active > 0 and j.m <= tm :
				debug.out(f"{self.name}: execute job {j.name}")
				j.func(*j.args)
#}}}1
class TimerInterval(threading.Thread): #{{{1
	@debug(1)
	def __init__(self, interval, func, *args):
		threading.Thread.__init__(self)
		self.deamon = True
		self.name = "TIMER"
		self.__running = threading.Event()
		self.__execute = threading.Event()
		self.__interval = interval
		self.__func = func
		self.__args = args
	
	@debug(1)
	def __del__(self):
		pass

	@debug(1)
	def run(self):
		# debug.out("TimerInterval: run() thread: " + str(threading.get_ident()), 2, COL_start)
		self.__running.set()
		self.__execute.set()
		t = 0
		while self.__running.is_set():
			if t >= self.__interval:
				if self.__execute.is_set():
					self.task()
				t = 0
			else:
				time.sleep(1)
				t += 1
		debug.out(f"{self.name}: ENDE", 2)

	def stop(self):
		debug.out(f"{self.name}: stopping", 2)
		self.__running.clear()

	def task(self):
		self.__func(*self.__args)

	@debug(1)
	def set_interval(self, i):
		self.__interval = i

	@debug(1)
	def start_exec(self):
		self.__execute.set()

	@debug(1)
	def stop_exec(self):
		self.__execute.clear()
#}}}1
class Shift_74X595(object): #{{{1
	@debug(1)
	def __init__(self, n, GPIO_DATA = 19, GPIO_OE = 13, GPIO_LATCH = 6, GPIO_CLOCK = 5):
		self.clock_tick = 0
		self.out_DATA  = gpiozero.DigitalOutputDevice(GPIO_DATA)
		self.out_OE    = gpiozero.DigitalOutputDevice(GPIO_OE)
		self.out_LATCH = gpiozero.DigitalOutputDevice(GPIO_LATCH)
		self.out_CLOCK = gpiozero.DigitalOutputDevice(GPIO_CLOCK)
		self.switches = [0] * n
		self.output_array()
	
	@debug(1)
	def __del__(self):
		pass

	def output_array(self):
		for i in range(len(self.switches) - 1, -1, -1):
			self.out_DATA.value = self.switches[i]
			self.out_CLOCK.on()
			self.out_CLOCK.off()
		self.out_LATCH.on()
		self.out_LATCH.off()

	def set(self, i, s):
		if i < 0 or i > len(self.switches) -1 : return
		self.switches[i] = s
		self.output_array()

	def set_array(self, a, show = True):
		l = len(a)
		if l > len(self.switches):
			l = len(self.switches)
		self.switches[0 : l - 1] = a
		self.output_array()

	def set_array_str(self, s, show = True):
		l = len(s)
		if l > len(self.switches): l = len(self.switches)
		for i in range(l):
			if s[i] == '0': self.switches[i] = 0
			else          : self.switches[i] = 1
		self.output_array()

	def fill_array(self, s, show = True):
		self.switches = [s] * len(self.switches)
		self.output_array()

	def size(self): return self.n

	def shift(self):
		self.out_CLOCK.on()
		self.out_CLOCK.off()
		self.out_LATCH.on()
		self.out_LATCH.off()

	def shift_array_right(self, show = True):
		for i in range(len(self.switches) - 1, 0, -1):
			self.switches[i] = self.switches[i - 1]
		self.output_array()

	def rotate_array_right(self, show = True):
		for i in range(len(self.switches) - 1, 0, -1):
			self.switches[i] = self.switches[i - 1]
		self.switches[0] = self.switches[len(self.switches) - 1]
		self.output_array()

	def rotate_array_left(self, show = True):
		for i in range(1, len(self.switches)):
			self.switches[i - 1] = self.switches[i]
		self.switches[len(self.switches) - 1] = self.switches[0]
		self.output_array()

	def push(self, s):
		self.out_DATA.value = s
		self.shift()

	def push_array_right(self, s, show = True ):
		self.shift_array_right(show = False)
		self.switches[0] = s
		self.output_array()

	def off(self):
		self.out_OE.on()

	def on(self):
		self.out_OE.off()

	def print_status(self):
		s = ''
		for i in self.switches:
			if i == 1 : s += '1'
			else      : s += '0'
		return s
#}}}1
class VideoAnnotation(object): #{{{1
	@debug(1)
	def __init__(self, cam):
		# debug.out("VideoAnnotation: __init__()", 2, COL_init)
		self.cam  = cam
		self.vs1    = None
		self.vs2    = None
		self.vr     = None
		self.md     = None
		self.pirs   = {}
		self.text   = ''
		self.debug  = False
	
	@debug(1)
	def __del__(self):
		pass
	
	def update(self):
		if self.cam == None: return
		s = ' '
		#if self.vs1 != None and self.vs1.is_streaming(): s += '-'
		s += time.strftime("%H:%M:%S")
		#if self.vs1 != None and self.vs1.is_streaming(): s += '-'
		s += self.text
		if self.debug == True:
			if self.vr  != None and self.vr.is_recording():
				s += f" [REC{str(int(self.vr.get_timer() - (int(time.clock_gettime(time.CLOCK_MONOTONIC)) - self.vr.get_start_time()))):>4}s"
			s += f" [{int(self.cam.framerate):02d}]"
			s += f" [{self.cam.exposure_speed / 1000000 * self.cam.framerate:1.2f}]"
			for key in self.pirs.keys():
				if self.pirs[key]: s += f" [{key}]"
			if self.md != None and self.md.motion_detected():
				if self.md.camera_is_enabled():
					s += " [P]"
				else:
					s += " [M]"
			else:
				s += " [ ]"
			s += f" [{(self.md.get_pixel_count()):04d}]"
		self.cam.annotate_text = s
	def pir(self, pirname, state):
		self.pirs[pirname] = state
#}}}1
class StepperMotor(object):#{{{1
	step_delay = 0.005
	sequence = [
	  [1,0,0,0],
	  [1,1,0,0],
	  [0,1,0,0],
	  [0,1,1,0],
	  [0,0,1,0],
	  [0,0,1,1],
	  [0,0,0,1],
	  [1,0,0,1]
	]

	@debug(1)
	def __init__(self, A = 12, B = 16, C = 20, D = 21, LeftStop = 24, RightStop = 23):
		self.pins = [
			gpiozero.DigitalOutputDevice(A),
			gpiozero.DigitalOutputDevice(B),
			gpiozero.DigitalOutputDevice(C),
			gpiozero.DigitalOutputDevice(D)
		]
		for p in self.pins:
			p.off()
		self.LeftStop  = gpiozero.Button(LeftStop,  pull_up = True)
		self.RightStop = gpiozero.Button(RightStop, pull_up = True)
	
	@debug(1)
	def __del__(self):
		pass

	def step_l(self):
		for i in range(8):
			for k in range(4):
				self.pins[k].value = self.sequence[i][k]
			time.sleep(self.step_delay)
		for p in self.pins:
			p.off()

	def step_r(self):
		for i in range(7, -1, -1):
			for k in range(4):
				self.pins[k].value = self.sequence[i][k]
			time.sleep(self.step_delay)
		for p in self.pins:
			p.off()

	def steps(self, dir, n):
		if type(n) is str:
			try:
				n = int(n)
			except:
				return
		if n > 400 : n = 400
		if dir == "l":
			for i in range(n):
				if self.left_stop():
					# debug.out("StepperMotor: LeftStop")
					return
				self.step_l()
		else:
			for i in range(n):
				if self.right_stop():
					# debug.out("StepperMotor: RightStop")
					return
				self.step_r()

	def left_stop(self):
		return self.LeftStop.is_pressed

	def right_stop(self):
		return self.RightStop.is_pressed
#}}}1
class VideoRecorder2(threading.Thread):#{{{1
	"""
	Start and stop picamera recording,
	calls writer for every frame
	"""

	@debug(1)
	def __init__(self, camera, writer, videores = (640, 480), splitter_port = 1):
		threading.Thread.__init__(self)
		self.deamon = True
		self.name   ="VideoRecorder2"
		self.__camera = camera
		self.__writer = writer
		self.__videores = videores
		self.__splitter_port = splitter_port
		self.__running = threading.Event()
		self.__recording = threading.Event()
		self.start()

	@debug(1)
	def __del__(self):
		pass

	def run(self):
		debug.out(f"{self.name}: start thread")
		self.__running.set()
		self.start_recording()
		while self.__running.is_set():
			if self.__recording.is_set():
				try:
					self.__camera.wait_recording(1)
				except Exception as e:
					debug.out(f"{self.name}: {e}")
			else:
				time.sleep(1)
		self.stop_recording()
		debug.out(f"{self.name}: thread ENDE")

	def stop(self):
		debug.out(f"{self.name}: stopping thread...")
		self.__running.clear()

	@debug(1)
	def start_recording(self):
		if self.__camera != None and not self.__recording.is_set():
			try:
				self.__camera.start_recording(
					self.__writer,
					format = 'h264',
					intra_period = 15,
					inline_headers = True,
					splitter_port = self.__splitter_port,
					resize = self.__videores
					)
			except Exception as e:
				debug.out(f"VideoRecorder2: {e}")
			else:
				self.__recording.set()

	@debug(1)
	def stop_recording(self):
		if self.__recording.is_set():
			#debug.out(f"{self.__class__.__name__}: camera.stop_recording()", color = COL_RED)
			try:
				self.__camera.stop_recording()
			except Exception as e:
				debug.out(f"VideoRecorder2: {e}" )
			self.__recording.clear()

	@debug(1)
	def set_resolution(self, videores):
		self.__videores = videores
	
	@debug(1)
	def get_resolution(self):
		return self.__videores
#}}}1
class FrameWriter(object):#{{{1
	lock = threading.Lock()

	@debug(1)
	def __init__(self):
		self.frame = 0
		#self.chunk_size = 32 * 1024
		self.video_stream_set = set()

	@debug(1)
	def __del__(self):
		pass

	@debug(1)
	def register_video_stream(self, vs):
		self.frame = 0
		FrameWriter.lock.acquire()
		self.video_stream_set.add(vs)
		FrameWriter.lock.release()

	@debug(1)
	def unregister_video_stream(self, vs):
		FrameWriter.lock.acquire()
		self.video_stream_set.remove(vs)
		FrameWriter.lock.release()

	def write(self, data):
		FrameWriter.lock.acquire()
		for s in self.video_stream_set:
			s.write(data)
		FrameWriter.lock.release()
#}}}1
class VideoStreamUDP(object):#{{{1
	"""
	creates an UDP stream
	"""
	#CHUNK_SIZE = 8 * 1024
	CHUNK_SIZE = 1395

	@debug(1)
	def __init__(self, server, writer, remote_addr, local_addr):
		self.__udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# private Multicast address range 239.0.0.0 - 239.255.255.255
		if remote_addr[0].split('.')[0] == "239":
			self.__udp_server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
		if 1024 < local_addr[1] < 65536:
			try:
				self.__udp_server_socket.bind(local_addr)
				debug.out(f"{__class__.__name__}: bind to {local_ip}:{local_port}")
			except:
				debug.out(f"{__class__.__name__}: ERROR: bind to {local_ip}:{local_port} failed", color = COL_RED)
		else:
			debug.out(f"{__class__.__name__}: socket not bound")
		self.__udp_client_addr = remote_addr
		self.__writer = writer
		self.__writer.register_video_stream(self)
		self.__frame = 0

	@debug(1)
	def __del__(self):
		pass

	@debug(1)
	def stop(self):
		self.__writer.unregister_video_stream(self)
		self.__udp_server_socket
	
	def write(self, data):
		"""called by FrameWriter for every Frame
		chops data stream in pieses < 64K for UDP"""
		self.__frame += 1
		n = len(data) / VideoStreamUDP.CHUNK_SIZE
		i = 0
		while i < n:
			self.__udp_server_socket.sendto(
				data[i * VideoStreamUDP.CHUNK_SIZE : (i + 1) * VideoStreamUDP.CHUNK_SIZE],
				self.__udp_client_addr)
			i += 1
#}}}1
class VideoStreamServer():#{{{1

	@debug(1)
	def __init__(self, camera, splitter_port = 1, videores = (640, 480), local_ip = None):
		self.__camera = camera
		if self.__camera == None:
			debug.out(f"{__class__.__name__}: no camera", color = COL_RED)
		self.__local_ip = local_ip
		self.__local_port = 4001
		self.__streams = {}
		self.__writer = FrameWriter()
		self.vidrec = VideoRecorder2(self.__camera, self.__writer, videores = videores, splitter_port = splitter_port)
	
	@debug(1)
	def __del__(self):
		pass

	@debug(1)
	#def create_video_stream(self, ws, remote_addr_str, local_addr_str):
	def create_video_stream(self, remote_addr_str, local_addr_str):
		"""
		remote_addr_str      data send to
		local_addr_str       bind socket to address
		"""
		if self.__camera == None:
			debug.out(f"{__class__.__name__}: ERROR: no camera", color = COL_RED)
			retstr = "ERROR: no camera"
		elif remote_addr_str == "":
			debug.out(f"{__class__.__name__}: ERROR: no address", color = COL_RED)
			retstr = "ERROR: no address"
		elif not remote_addr_str in self.__streams:
			remote_addr = (remote_addr_str.split(':')[0], int(remote_addr_str.split(':')[1]))
			local_addr  = (local_addr_str.split(':')[0],  int(local_addr_str.split(':')[1]))
			self.__streams[remote_addr_str] = VideoStreamUDP(self, self.__writer, remote_addr, local_addr)
			retstr = f"stream: {remote_addr_str} created"
		else:
			debug.out(f"{__class__.__name__}: stream: {remote_addr_str} already exists.")
			retstr = f"ERROR: stream: {remote_addr_str} already exists." 
		return retstr

	@debug(1)
	def close_video_stream(self, ws, remote_addr_str):
		if remote_addr_str in self.__streams:
			vs = self.__streams.pop(remote_addr_str)
			vs.stop()
			retstr = f"stream: {remote_addr_str} closed."
		else:
			retstr = f"ERROR: stream: {remote_addr_str} not found."
		return retstr

	@debug(1)
	def close_all_video_streams(self):
		for key in self.__streams:
			self.__streams[key].stop()
		self.__streams.clear()
		return

	@debug(1)
	def stop(self):
		self.close_all_video_streams()
		self.vidrec.stop()
		self.vidrec.join()
		return

	@debug(1)
	def list_all(self):
		retstr = ''
		for s in self.__streams:
			retstr += str(s) + " "
		return retstr

	@debug(1)
	def list_addr(self, ip):
		print(ip)
		retstr = ''
		for s in self.__streams:
			if s.split(':')[0] == ip:
				retstr += str(s) + " "
		return retstr

	@debug(1)
	def status(self):
		retstr = ''
		n = 0
		for s in self.__streams:
			n += 1
			retstr += str(n) + " " + str(s) + "\n"
		return retstr

	def status0(self, key):
		if key in self.__streams:
			return '1'
		else:
			return '0'

	@debug(1)
	def num_streams(self):
		return str(len(self.__streams))
#}}}1
class VideoRecorder(threading.Thread): #{{{1
	@debug(1)
	def __init__(self, camera, splitter_port, videores = (640, 480), rec_timer = 600.0):
		threading.Thread.__init__(self)
		self.deamon = True
		self.__camera   = camera
		self.__videores = videores
		self.__splitter_port = splitter_port
		self.__request   = threading.Event() # request recoding
		self.__recording = threading.Event() # recording is running
		self.__running   = threading.Event() # VideoRecorder is running
		self.__rec_timer = rec_timer
		self.__start_time = 0
		self.va = None

	@debug(1)
	def __del__(self):
		pass

	@debug(1)
	def run(self):
		global BASE_DIR
		if self.__camera == None:
			debug.out("VidRec: *** NO CAMERA ***", 1, COL_error)
			return
		self.__running.set()
		self.__recording.clear()
		self.__request.clear()
		while True:
			self.__request.wait()
			self.__request.clear()
			if not self.__running.is_set(): break

			datedir = time.strftime(TIMESTR_PHOTO_DIR)
			videodir = BASE_DIR + "/videos/"+ datedir
			if not os.path.isdir(videodir):
				try:
					os.makedirs(videodir)
					debug.out("VidRec: " + videodir + " created", 2, COL_warning)
				except:
					# !!! Falsch
					debug.out("VidRec: " + "ERROR creating: " + videodir, 2, COL_error)
					return
			file = videodir + "/" + socket.gethostname() + "_" + time.strftime(TIMESTR_PHOTO) + "_fr" + str(camera.framerate).zfill(2) + ".h264"
			debug.out("VidRec: " + file, 4)
			if self.va != None:
				self.va.text = ''
				self.va.update()
			debug.out("VidRec: kamera_lock.acquire(5)")
			try:
				self.__recording.set()
				self.__camera.start_recording(file, format = 'h264', splitter_port = self.__splitter_port, resize = self.__videores);
				debug.out("VidRec: recording started.", 2)
				timer = threading.Timer(self.__rec_timer, self.stop_recording)
				timer.start()
				self.__start_time = int(time.clock_gettime(time.CLOCK_MONOTONIC))
				debug.out("VidRec: max recording time is " + str(self.__rec_timer) + "s", 2);
				while self.__recording.is_set():
					self.__camera.wait_recording(1, self.__splitter_port)
			except Exception as e:
				self.__recording.clear();
				debug.out("VidRec: EXCEPTION: " + str(e), 1, COL_error);
			if self.va != None: self.va.update()
			camera.stop_recording(self.__splitter_port)
			self.__recording.clear();
			debug.out("VidRec: recording stoped", 2);
		debug.out("VidRec: ENDE.", 1, COL_stop);

	@debug(1)
	def set_resolution(self, res):
		self.__videores = res

	@debug(1)
	def get_resolution(self):
		return self.__videores

	def timer(self, t):
		self.__rec_timer = t

	def get_timer(self):
		return self.__rec_timer

	def get_start_time(self):
		return self.__start_time

	def is_recording(self):
		return self.__recording.is_set()

	@debug(1)
	def start_recording(self):
		# make a request to record
		# if the request is granted the self.running.set flag is set
		self.__request.set()

	@debug(1)
	def stop_recording(self):
		self.__recording.clear()

	@debug(1)
	def stop(self):
		self.__running.clear()
		self.__recording.clear()
		self.__request.set()
#}}}1
class MotionAnalyzer(picamera.array.PiRGBAnalysis):#{{{1
	@debug(1)
	def __init__(self, camera, size, mask_file):
		super(MotionAnalyzer, self).__init__(camera, size)
		self.enabled = threading.Event()
		self.motion = False
		self.camera = camera
		self.t = 0
		self.n = 0
		self.detect_time = 5 # Sekunden
		self.action = Action(2, take_photo, camera, "motion", "motion")
		self.action.start()
		self.frame_counter = 0
		self.frame_stride = 0
		self.fr = self.frame_stride
		self.pixel_threshold = 500
		self.mog2 = cv2.createBackgroundSubtractorMOG2(history = 500, varThreshold = 100.0, detectShadows = False) 
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
		self.mask = cv2.imread(mask_file, cv2.IMREAD_GRAYSCALE)
		if self.mask is not None:
			debug.out(f"MotionAnalyzer: mask = {mask_file}")
		else:
			debug.out(f"MotionAnalyzer: no mask")

	def analyze(self, frame_data):
		if self.fr > 0:
			self.fr = self.fr - 1
			return
		else:
			self.fr = self.frame_stride
		self.frame_counter = self.frame_counter + 1
		fg = self.mog2.apply(frame_data)
		if self.mask is not None:
			fg = cv2.bitwise_and(fg, fg, mask = self.mask)
		fgop = cv2.morphologyEx(fg, cv2.MORPH_OPEN, self.kernel)
		self.n = cv2.countNonZero(fgop)
		#---DEBUG_OPENCV-----------------------------------------------------
		if DEBUG_OPENCV:
			# print(".", end="", flush=True)
			n = cv2.countNonZero(fg)
			n_op = self.n
			cv2.rectangle(fg,   (5, 5), (100, 40), (255, 255, 255), -1)
			cv2.rectangle(fgop, (5, 5), (100, 40), (255, 255, 255), -1)
			cv2.putText(fg,   str(n),    (10, 36), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0))
			cv2.putText(fgop, str(n_op), (10, 36), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0))
			cv2.imshow("fg",   fg)
			cv2.imshow("fgop", fgop)
			cv2.waitKey(1)
		#--------------------------------------------------------------------
		if self.n > self.pixel_threshold and self.enabled.is_set():
			self.t = self.detect_time * (self.frame_stride + 1)
			if self.motion == False:
				self.motion = True
				self.action.action_start()
		else:
			if self.t > 0:
				self.t = self.t - 1
			else:
				if self.motion == True:
					self.motion = False
					self.action.action_stop()

	@debug(1)
	def flush(self):
		self.t = 0
		self.n = 0
		self.motion = False
		self.action.action_stop()
#}}}1
class MotionDetection(threading.Thread): #{{{1
	@debug(1)
	def __init__(self, camera, splitter_port, size = (320, 240), mask_file = MOTION_MASK):
		threading.Thread.__init__(self)
		self.camera = camera
		self.size = size
		self.splitter_port = splitter_port
		self.analyzer = MotionAnalyzer(camera, mask_file = mask_file, size = self.size)
		self.daemon  = True
		self.running = threading.Event()
		self.recording = threading.Event()
		self.recording_stoped = threading.Event()
	
	@debug(1)
	def run(self):
		self.running.set()
		self.recording_stoped.set()
		self.recording.set()
		while self.running.is_set():
			self.recording.wait()
			if self.running.is_set():
				self.camera.start_recording(self.analyzer, format = "bgr", splitter_port = self.splitter_port, resize = self.size)
				debug.out("MotionDetection: recording started")
				self.recording_stoped.clear()
			else:
				break
			while self.running.is_set() and self.recording.is_set():
				self.camera.wait_recording(1, splitter_port = self.splitter_port)
			self.camera.stop_recording(splitter_port = self.splitter_port)
			debug.out("MotionDetection: recording stoped")
			self.recording_stoped.set()
		self.analyzer.action.stop()
		self.analyzer.action.join()
		debug.out("MotionDetection: ENDE")

	@debug(1)
	def stop(self):
		self.running.clear()
		self.recording.set()

	@debug(1)
	def is_enabled(self):
		if self.analyzer.enabled.is_set(): return "on"
		else                             : return "off"

	@debug(1)
	def enable(self):
		self.analyzer.enabled.set()

	@debug(1)
	def disable(self):
		self.analyzer.enabled.clear()

	@debug(1)
	def set_pixel_threshold(self, pixel_threshold):
		self.analyzer.pixel_threshold = pixel_threshold

	@debug(1)
	def get_pixel_threshold(self):
		return self.analyzer.pixel_threshold

	@debug(1)
	def set_detect_time(self, t):
		self.analyzer.detect_time = t

	@debug(1)
	def get_detect_time(self):
		return self.analyzer.detect_time

	@debug(1)
	def set_photo_interval(self, t):
		self.analyzer.action.interval = t
	
	@debug(1)
	def get_photo_interval(self):
		return self.analyzer.action.interval

	#@debug(1)
	def get_frame_counter(self):
		return self.analyzer.frame_counter

	def get_pixel_count(self):
		return self.analyzer.n

	@debug(1)
	def enable_camera(self):
		self.analyzer.action.enabled.set()

	@debug(1)
	def disable_camera(self):
		self.analyzer.action.enabled.clear()

	@debug(1)
	def camera_is_enabled_str(self):
		return self.analyzer.action.is_enabled()

	#@debug(1)
	def camera_is_enabled(self):
		return self.analyzer.action.enabled.is_set()

	#@debug(1)
	def motion_detected(self):
		return self.analyzer.motion

	@debug(1)
	def start_recording(self):
		self.recording.set()

	@debug(1)
	def stop_recording(self):
		self.recording.clear()
		# wait until recording is realy stoped
		self.recording_stoped.wait()

	@debug(1)
	def set_var_threshold(self, var):
		self.analyzer.mog2.setVarThreshold(var)

	@debug(1)
	def get_var_threshold(self):
		return self.analyzer.mog2.getVarThreshold()

	def set_frame_stride(self,frame_stride):
		self.analyzer.frame_stride = frame_stride

	def get_frame_stride(self):
		return self.analyzer.frame_stride

	@debug(1)
	def __del__(self):
		pass
#}}}1
class Action(threading.Thread):#{{{1

	@debug(1)
	def __init__(self, interval, func, *args):
		threading.Thread.__init__(self)
		self.interval = interval
		self.func = func
		self.args = args
		self.running = threading.Event()
		self.action  = threading.Event()
		self.enabled = threading.Event()
		self.daemon = True
	
	@debug(1)
	def run(self):
		self.running.set()
		while self.running.is_set():
			self.action.clear()
			self.action.wait()
			while self.running.is_set() and self.action.is_set():
				if self.enabled.is_set():
					self.func(*self.args)
				time.sleep(self.interval)
		debug.out("Action: ENDE.", 1)
	
	@debug(1)
	def stop(self):
		self.running.clear()
		self.action.set()
	
	@debug(3)
	def action_start(self):
		self.action.set()
	
	@debug(3)
	def action_stop(self):
		self.action.clear()
	
	@debug(1)
	def enable(self):
		self.enabled.set()
	
	@debug(1)
	def is_enabled(self):
		if self.enabled.is_set(): return "on"
		else                    : return "off"

	@debug(1)
	def disable(self):
		self.enabled.clear()

	@debug(1)
	def __del__(self):
		pass
#}}}1
class PIR(threading.Thread):#{{{1

	@debug(9)
	def __init__(self, pir_name, pin, min_time = 30, va = None):
		threading.Thread.__init__(self)
		self.deamon     = True
		self.pir_name   = pir_name
		self.ws_address = ""
		self.sw_nr      = '0'
		self.sw_pir_on  = '1'
		self.sw_pir_off = '0'
		self.state      = 0
		self.vidannot   = va
		n = 0
		while True:
			try:
				self.pin = gpiozero.Button(pin, pull_up = False)
			except:
				debug.out(f"PIR: gpio ERROR n = {n}")
				n +=1
				if n > 10 :
					debug.out("PIR: gpio ERROR exit Program")
					sys.exit(1)
				continue
			break
		self.pir_event  = threading.Event()
		self.running    = threading.Event()
		self.active     = False
		self.ws_flag    = False
		self.daemon     = True
		self.min_time   = min_time
		self.logfile    = None
		self.stop_detection()
		self.start()
	
	@debug(1) 
	def run(self):
		global BASE_DIR
		self.running.set()
		self.logfile = open(BASE_DIR + "/" + self.pir_name  + ".txt", "a", buffering = 1)
		while self.running.is_set():
			if self.ws_flag: asyncio.run(self.ws_send(self.sw_pir_off))
			self.pir_event.wait()
			if self.running.is_set():
				if self.ws_flag: asyncio.run(self.ws_send(self.sw_pir_on))
				debug.out("PIR: " + self.pir_name + " on", 7)
				self.state = 1
				if self.vidannot:
					self.vidannot.pir(self.pir_name, True)
					self.vidannot.update()
				self.logfile.write(time.strftime(TIMESTR_PIR) + "\t")
				t = self.min_time
				while self.running.is_set() and (self.pir_event.is_set() or t > 0):
					if camera and PIRCAM:
						take_photo(camera, self.pir_name, "pir")
					time.sleep(1)
					t = t - 1
				self.logfile.write(time.strftime(TIMESTR_PIR) + "\n")
				if self.vidannot: 
					self.vidannot.pir(self.pir_name, False)
					self.vidannot.update()
				self.state = 0
				debug.out("PIR: " + self.pir_name + " off", 7)
		self.logfile.close()
		debug.out("PIR: " + self.pir_name + " ENDE", 1)
	
	@debug(9)
	async def ws_send(self, sw_state):
		try:
			async with websockets.client.connect(self.ws_address) as ws:
				await asyncio.wait_for(ws.send('sw ' + self.sw_nr + ' ' + sw_state), timeout = 1.0)
				m = await asyncio.wait_for(ws.recv(), timeout = 1.0)
				debug.out("PIR: " + self.pir_name + " " + m, 9)
		except:
			debug.out("PIR: " + self.pir_name + " ERROR connection timeout", 1, COL_error)

	@debug(9)
	def start_detection(self):
		self.active = True
		self.pin.when_pressed  = self.pir_event.set
		self.pin.when_released = self.pir_event.clear
	
	@debug(9)
	def stop_detection(self):
		self.active = False
		self.pin.when_pressed  = self.pir_event.clear
		self.pin.when_released = self.pir_event.clear
	
	@debug(1)
	def stop(self):
		self.stop_detection()
		self.running.clear()
		self.pir_event.set()
	
	@debug(9)
	def get_state(self):
		if self.active == True : return '1'
		else                   : return '0'
	
	@debug(9)
	def set_ws_flag(self):
		self.ws_flag = True
	
	@debug(9)
	def clear_ws_flag(self):
		self.ws_flag = False

	@debug(9)
	def set_sw_pir_on(self, sw_pir_on):
		if sw_pir_on == '0' :
			self.sw_pir_on  = '0'
			self.sw_pir_off = '1'
		else:
			self.sw_pir_on  = '1'
			self.sw_pir_off = '0'

	@debug(9)
	def set_sw_nr(self, sw_nr):
		self.sw_nr = sw_nr

	@debug(9)
	def set_ws_address(self, addr):
		self.ws_address = "ws://" + addr
#}}}1

def print_status1():#{{{1
	global BASE_DIR
	s=""
	s += f"__KAMERA-SERVER__{VERSION}__({socket.gethostname()})___________\n\n"
	for k in configurations.keys():
		if k == config_name : s += "[" + k + "] "
		else                : s += k + " "
	s += "\n----------------------------------------------\n"
	s += f"TIMEOFFSET: {TIMEOFFSET}\n"
	s += cron.list()
	s += "----------------------------------------------\n"
	# s += "pir 123  sh 0123456789ABCDEF  LR\n"
	s += "pir 3  sh 0123456789ABCDEF  LR\n"
	s += "    "
	# s += pir1.get_state()
	# s += pir2.get_state()
	s += pir3.get_state()
	s += "     "
	s += shreg.print_status()
	s += "  "
	if steppermotor.left_stop():  s += "1"
	else:                         s += "0"
	if steppermotor.right_stop(): s += "1"
	else:                         s += "0"
	s += "\n----------------------------------------------\n"
	if camera:
		if kamera_lock.locked():
			s += f"                  *** CAMERA LOCKED ***\n"
		s += f"     Camera type: {camera.revision}\n"
		x, y = camera.resolution
		s += f"Photo resolution: {x}x{y}\n"
		x, y = vidrec.get_resolution()
		s += f"Video Resolution: {x}x{y}\n"
		s += f"       framerate: {camera.framerate}  iso {camera.iso}  speed: {camera.exposure_speed}\n"
		s += f"      saturation: {camera.saturation}\n"
		s += f"        rotation: {camera.rotation}\n"
		s += f"      camera PIR: "
		if PIRCAM: s += "on\n"
		else :     s += "off\n"
		s += f"motion detection: {motion_detect.is_enabled()}\n"
		s += f"   motion camera: {motion_detect.camera_is_enabled_str()}\n"
		s += f" pixel threshold: {motion_detect.get_pixel_threshold()}\n"
		s += f"   var threshold: {motion_detect.get_var_threshold()}\n"
		s += f"     detect time: {motion_detect.get_detect_time()}\n"
		s += f"     pixel count: {motion_detect.get_pixel_count()}\n"
		s += f"   frame counter: {motion_detect.get_frame_counter()}\n"
		s += f"    frame stride: {motion_detect.get_frame_stride()}\n"
	else :
		s += "    *** NO CAMERA ***\n"
	s += f"      debuglevel: {debug.debug_level}\n"
	s += f"        BASE_DIR: {BASE_DIR}\n"
	s += f"Video-Streams:\n"
	s += f"{vidstrsrv.status()}"
	return s
#}}}1
def print_status2():#{{{1
	s  = f"STATUS "
	s += f"hst={socket.gethostname()};"
	s += f"ver={VERSION};"
	if   "Zero W"         in RASPI: s += f"rpi=0W;"
	elif "3 Model B Rev"  in RASPI: s += f"rpi=3B;"
	elif "3 Model B Plus" in RASPI: s += f"rpi=3B+;"
	elif "4 Model B"      in RASPI: s += f"rpi=4B;"
	else                          : s += f"rpi=?;"
	# s += f"pi1={pir1.get_state()};" 
	# s += f"pi2={pir2.get_state()};" 
	s += f"pi3={pir3.get_state()};" 
	if PIRCAM: s += "pic=1;"
	else:      s += "pic=0;"
	s += f"shr={shreg.print_status()};"
	if camera :
		s += f"cam={camera.revision};"
		if kamera_lock.locked(): s += "lck=1;"
		else                   : s += "lck=0;"
		s += f"phr={camera.resolution[0]}x{camera.resolution[1]};"
		s += f"vir={vidrec.get_resolution()[0]}x{vidrec.get_resolution()[1]};"
		s += f"str={vidstrsrv.vidrec.get_resolution()[0]}x{vidstrsrv.vidrec.get_resolution()[1]};"
		s += f"stn={vidstrsrv.num_streams()};"
		if vidrec.is_recording(): s += "rec=1;"
		else:                     s += "rec=0;"
		s += f"rct={vidrec.get_timer()};"
		s += f"fmr={str(camera.framerate)};"
		s += f"iso={str(camera.iso)};"
		s += f"spd={str(camera.exposure_speed)};"
		s += f"mod={str(camera.exposure_mode)};"
	else :
		s += f"cam=0;"
	s += f"cfg={config_name};"
	s += f"dbg={debug.debug_level}"
	return s
#}}}1
def print_status3():#{{{1
	s="STATUS3 "
	s += f" ver[{VERSION}]"
	if   "Zero W"         in RASPI: s += f" rpi[0W ]"
	elif "3 Model B Rev"  in RASPI: s += f" rpi[3B ]"
	elif "3 Model B Plus" in RASPI: s += f" rpi[3B+]"
	elif "4 Model B"      in RASPI: s += f" rpi[4B ]"
	else                          : s += f" rpi[ ? ]"
	# s += f" pir[{pir1.get_state()}{pir2.get_state()}{pir3.get_state()}"
	s += f"[ {pir3.get_state()}"
	if PIRCAM: s += f"*]"
	else:      s += f" ]"
	if camera:
		s += f" cam[{camera.revision}]"
		if kamera_lock.locked(): s += " lck[L]"
		else                   : s += " lck[ ]"
		s += f" nst[{vidstrsrv.num_streams()}]"
		s += f" fmr[{int(camera.framerate):>2}]"
		s += f" spd[{camera.exposure_speed:>6}]"
	else :
		s += f" [*** NO CAMERA ***]"
	s += f" cfg[{config_name:<5}]"
	s += f" dbl[{debug.debug_level}]"
	return s
#}}}1
def print_help():#{{{1
	return "__KAMERA-SERVER_" + VERSION + "___("  + socket.gethostname() + ")_________\n" + HELPSTR
#}}}1
def read_config(): #{{{1
	global configurations
	global curr_config
	global HELPSTR
	line = 0
	configurations = {'base': []}
	curr_config = 'base'
	try:
		file = open(CONFIG_FILE)
		lines = file.read().split('\n')
	except IOError:
		debug.out("read_config: ERROR opening " + CONFIG_FILE, 1, COL_error)
		return "ERROR"
	file.close()
	for l in lines:
		# ignore all empty lines
		line += 1
		if len(l) > 0:
			# ignore all comment lines
			if l[0] == "#":	continue
			# build help string
			if l[0] == "%":	HELPSTR +=  l[1:] + "\n"; continue
			# split into command tokens:
			# command parameter1 [parameter2]
			k = l.split()
			# k[0]          k[1]
			# configuration base
			if k[0] == "configuration":
				if len(k) > 1:
					debug.out(f"{COL_CYAN}read_config:{COL_RESET} {COL_GREEN}[{k[1]}]", 4)
					# Wenn der Name nicht als Key im Dict ist
					# denn füge einen neuen key ein
					curr_config = k[1]
					if not curr_config in configurations:
						configurations[curr_config] = []
			else:
				configurations[curr_config] += [k]
#}}}1
def set_config(key):#{{{1
	debug.out(f"{COL_MAGENTA}setconfig:{COL_RESET} " + key, 4)
	global PIRCAM
	global jpgquality
	global sched
	global MULTICASTADDR
	global TIMEOFFSET
	global HELPSTR
	global configurations
	global config_name
	global sched
	global START_MULTICAST
	global HOME_DIR
	global BASE_DIR
	return_str = ''
	if not key in configurations.keys(): return 'ERROR: ' + key
	config_name = key
	for k in configurations[config_name]:
		if len(k) == 2:
			debug.out(f"{COL_MAGENTA}setconfig:{COL_RESET} {k[0]} {k[1]}")
			if k[0] == "pircam":
				if k[1] == "on": PIRCAM = True
				else           : PIRCAM = False
			elif k[0] == "shift":         shreg.set_array_str(k[1])
			elif k[0] == "debuglevel":    debug.debug_level = int(k[1])
			elif k[0] == "multicast" :    MULTICASTADDR = k[1]
			elif k[0] == "autostart_multicast" :
				if k[1] == "on" : START_MULTICAST = True
				else            : START_MULTICAST = False
			elif k[0] == "timeoffset":
				TIMEOFFSET = int(k[1])
				reschedule_day_night()
			elif k[0] == "phototimer": phototimer.set_interval(int(k[1]))
			elif k[0] == "motion_detection":
				if k[1] == "on": motion_detect.enable()
				else           : motion_detect.disable()
			elif k[0] == "motion_camera":
				if k[1] == "on": motion_detect.enable_camera()
				else           : motion_detect.disable_camera()
			elif k[0] == "motion_pixel_threshold": motion_detect.set_pixel_threshold(int(k[1]))
			elif k[0] == "motion_var_threshold"  : motion_detect.set_var_threshold(float(k[1]))
			elif k[0] == "motion_detect_time"    : motion_detect.set_detect_time(int(k[1]))
			elif k[0] == "motion_frame_stride"   : motion_detect.set_frame_stride(int(k[1]))
			elif k[0] == "motion_photo_interval" : motion_detect.photo_interval = float(k[1])
			elif k[0] == "base_dir"              :
				BASE_DIR = HOME_DIR + "/" + str(k[1])
				if not os.path.isdir(BASE_DIR):
					try:
						os.makedirs(BASE_DIR)
						debug.out("main: BASE_DIR " + BASE_DIR + " created", 1, COL_warning)
					except:
						debug.out("main: ERROR creating BASE_DIR: " + BASE_DIR, 1, COL_error)
						debug.out("main: EXIT PROGRAM", 1, COL_error)
						sys.exit(1)
			elif k[0] == "camera":
				if camera:
					if k[1] == "stop":
						if kamera_lock.acquire(True, 10):
							debug.out(f"{COL_MAGENTA}setconfig:{COL_YELLOW} camera lock acquired", 9)
							vidstrsrv.vidrec.stop_recording()
							motion_detect.stop_recording()
						else:
							debug.out(f"{COL_MAGENTA}setconfig:{COL_error} camera lock timeout", 1)
							debug.out(f"{COL_MAGENTA}setconfig:{COL_error} return", 1)
							return return_str
					elif k[1] == "start":
						vidstrsrv.vidrec.start_recording()
						motion_detect.start_recording()
						kamera_lock.release()
						debug.out(f"{COL_MAGENTA}setconfig:{COL_GREEN} camera lock released", 9, COL_MAGENTA)
		elif len(k) == 3:
			if k[0] == "camera":
				if camera:
					debug.out(f"{COL_MAGENTA}setconfig:{COL_RESET} {k[0]} {k[1]} {k[2]}")
					if   k[1] == "framerate":     camera.framerate = int(k[2])
					elif k[1] == "streamres":
						if   k[2] == "640x480":   vidstrsrv.vidrec.set_resolution((640, 480))
						elif k[2] == "1296x972":  vidstrsrv.vidrec.set_resolution((1296, 972))
					elif k[1] == "photores":
						if   k[2] == "1296x972":  camera.resolution = (1296,  972)
						elif k[2] == "1640x1232": camera.resolution = (1640, 1232)
						elif k[2] == "2592x1944": camera.resolution = (2592, 1944)
						elif k[2] == "3280x2464": camera.resolution = (3280, 2464) 
					elif k[1] == "recorderres":
						if   k[2] ==  "640x480":  vidrec.set_resolution(( 640, 480))
						elif k[2] == "1296x972":  vidrec.set_resolution((1296, 972))
					elif k[1] == "iso":                   camera.iso                   = int(k[2])
					elif k[1] == "exposure_mode":         camera.exposure_mode         = k[2]
					elif k[1] == "awb_mode":              camera.awb_mode              = k[2]
					elif k[1] == "shutter_speed":         camera.shutter_speed         = int(k[2])
					elif k[1] == "saturation":            camera.saturation            = int(k[2])
					elif k[1] == "contrast":              camera.contrast              = int(k[2])
					elif k[1] == "exposure_compensation": camera.exposure_compensation = int(k[2])
					elif k[1] == "annotate_text_size":    camera.annotate_text_size    = int(k[2])
					elif k[1] == "annotate_background":   camera.annotate_background   = picamera.Color(k[2])
					elif k[1] == "annotate_foreground":   camera.annotate_foreground   = picamera.Color(k[2])
					elif k[1] == "rotation":              camera.rotation              = int(k[2])
					elif k[1] == "jpgquality":            jpgquality                   = int(k[2])
					elif k[1] == "recording_timer":       vidrec.timer(int(k[2]))
#				cron.reschedule( k[1], int(k[2]), int(k[3]), int(k[4]) )
		elif len(k) == 6:
			debug.out(f"{COL_MAGENTA}setconfig:{COL_RESET} {k[0]} {k[1]} {k[2]} {k[3]} {k[4]} {k[5]}")
			# if   k[0] == "pir1":
			# 	if k[1] == "on": pir1.start_detection()
			# 	else :           pir1.stop_detection()
			# 	if k[2] == "on": pir1.set_ws_flag()
			# 	else :           pir1.clear_ws_flag()
			# 	pir1.set_ws_address(k[3])
			# 	pir1.set_sw_nr(k[4])
			# 	pir1.set_sw_pir_on(k[5])
			# elif k[0] == "pir2":
			# 	if k[1] == "on": pir2.start_detection()
			# 	else :           pir2.stop_detection()
			# 	if k[2] == "on": pir2.set_ws_flag()
			# 	else :           pir2.clear_ws_flag()
			# 	pir2.set_ws_address(k[3])
			# 	pir2.set_sw_nr(k[4])
			# 	pir2.set_sw_pir_on(k[5])
			if k[0] == "pir3":
				if k[1] == "on": pir3.start_detection()
				else :           pir3.stop_detection()
				if k[2] == "on": pir3.set_ws_flag()
				else :           pir3.clear_ws_flag()
				pir3.set_ws_address(k[3])
				pir3.set_sw_nr(k[4])
				pir3.set_sw_pir_on(k[5])
	vidannot.update()
	if START_MULTICAST : vidstrsrv.create_video_stream(MULTICASTADDR, "0:0")
	return return_str
#}}}1
def reschedule_day_night():#{{{1
	o = astral.Observer(latitude = 51.144167, longitude = 11.456111, elevation = 214.0)
	s = astral.sun.sun(o)
	cron.reschedule("day",   1, s['sunrise'].hour + TIMEOFFSET, s['sunrise'].minute)
	cron.reschedule("night", 1, s['sunset'].hour  + TIMEOFFSET,  s['sunset'].minute)
#}}}1
def signal_handler(sig, frame):#{{{1
	debug.out("SIGNAL:" + str(sig), 1, COL_warning)
	if   sig == signal.SIGTERM: asyncio.get_event_loop().call_soon_threadsafe(asyncio.get_event_loop().stop)
	elif sig == signal.SIGHUP:  read_config()
#}}}1
def take_photo(camera, photoid, dir_name):#{{{1
	global BASE_DIR
	global LASTPHOTO
	LASTPHOTO = None
	if not camera:
		debug.out("Photo: *** NO CAMERA ***", 1, COL_error)
		return "no camera"
	if not kamera_lock.acquire(True, 0):
		debug.out("Photo: " + photoid + " camera lock", 1, COL_error)
		return "locked"
	datedir = time.strftime(TIMESTR_PHOTO_DIR)
	photodir = BASE_DIR + "/photos-" + dir_name  + "/"+ datedir
	if not os.path.isdir(photodir):
		try:
			os.makedirs(photodir)
			debug.out("Photo: " + photodir + " created", 1, COL_warning)
		except:
			debug.out("Photo: " + "ERROR creating: " + photodir, 1, COL_error)
			kamera_lock.release()
			return
	filename = socket.gethostname() + "_" + time.strftime(TIMESTR_PHOTO) + "_" + photoid + ".jpg"
	f = photodir + "/" + filename
	debug.out("Photo: " + photoid + " " + filename, 8, COL_ok)
	camera.capture(f, format = 'jpeg', quality = jpgquality, use_video_port = True)
	kamera_lock.release()
	LASTPHOTO = f
	return f
#}}}1
def feed_watchdog():#{{{
	try:
		f = open("/def/watchdog")
		f.write('A')
	except:
		debug.out("Watchdog feed: ERROR opening")
	finally:
		f.close()
#}}}
def stop_watchdog():#{{{
	try:
		f = open("/dev/watchdog")
		f.write('V')
		debug.out("Watchdog stop: STOP")
	except:
		debug.out("Watchdog stop: ERROR opening")
	finally:
		f.close()
#}}}zo
def remove_cron_job(sched, id):#{{{1
	sched.remove_job(id)
#}}}1
async def ws_broadcast(message):#{{{1
	if ws_set:
		await asyncio.wait([ws.send(message) for ws in ws_set])
#}}}1
async def ws_closeall():#{{{1
	if ws_set:
		await asyncio.wait([ws.close() for ws in ws_set])
#}}}1
async def ws_register(ws):#{{{1
	ws_set.add(ws)
#}}}1
async def ws_unregister(ws):#{{{1
	ws_set.remove(ws)
#}}}1
async def ws_message_handler(ws, path):#{{{1
	await ws_register(ws)
	try:
		async for m in ws:
			await ws_process_message(ws, m)
	finally:
		await ws_unregister(ws)
#}}}1
async def ws_process_message(ws, message):#{{{1
	debug.out(f"{COL_YELLOW}Command:{COL_RESET} {COL_GREEN}{message}", 2)
	s = 'OK'
	ms = message.split(' ')
	ms[0] = ms[0].upper()
	if   ms[0] == 'SWITCH-STATE':
		await ws_broadcast('SWITCH-STATE ' + shreg.print_status())
	elif ms[0] == 'SWITCH-SET' :
		if len(ms) > 1 :
			shreg.set_array_str(ms[1])
			await ws.send('SWITCH-SET ' + shreg.print_status());
		else:
			await ws.send('ERROR 1 SWITCH-SET')
	elif ms[0] == 'SWITCH':
		if len(ms) > 2 :
			shreg.set(int(ms[1]), int(ms[2]))
			await ws.send('SWITCH OK')
		else:
			await ws.send('ERROR 1 SWITCH')
	elif ms[0] == "VERSION"  : 
		await ws.send('VERSION ' + VERSION)
	elif ms[0] == "QUIT":
		await ws_broadcast('QUIT OK')
		await ws_closeall()
		asyncio.get_event_loop().stop()
	elif ms[0] == "STATUS"   : await ws.send(print_status2())
	elif ms[0] == "STATUSX"  : await ws.send(print_status1())
	elif ms[0] == "STATUS3"  : await ws.send(print_status3())
	elif ms[0] == "PING"     :
		if kamera_lock.locked():
		    await ws.send("CAMLOCK")
		else :
		    await ws.send("PONG")
	# video streams
	elif ms[0] == "MD-PHOTO-ON" : motion_detect.enable_camera();   await ws.send("MD-PHOTO-ON OK")
	elif ms[0] == "MD-PHOTO-OFF": motion_detect.disable_camera();  await ws.send("MD-PHOTO-OFF OK")
	elif ms[0] == "MD-ON"       : motion_detect.start_recording(); await ws.send("MD-ON OK")
	elif ms[0] == "MD-OFF"      : motion_detect.stop_recording();  await ws.send("MD-OFF OK")
	elif ms[0] == "VS-COUNT"    : await ws.send("VS-COUNT " + vidstrsrv.num_streams())
	elif ms[0] == "VS-LIST"     : await ws.send("VS-LIST "  + vidstrsrv.list_all())
	elif ms[0] == "VS-START":
		if len(ms) > 1 :
			vidstrsrv.create_video_stream(ms[1], "0:0")
			await ws_broadcast("VS-START OK")
		else :
			await ws_broadcast("ERROR 1 VS-START")
	elif ms[0] == "VS-STOP" :
		if len(ms) > 1 :
			vidstrsrv.close_video_stream (ws, ms[1])
			await ws_broadcast("VS-STOP OK")
		else :
			await ws_broadcast("ERROR 1 VS-STOP")
	elif ms[0] == "VS-STOP-ALL" : 
		vidstrsrv.close_all_video_streams()
		await ws_broadcast("VS-STOP-ALL OK")
	elif ms[0] == "MC-START" : vidstrsrv.create_video_stream(MULTICASTADDR, "0:0");                                         await ws_broadcast("mc-start " + MULTICASTADDR)
	elif ms[0] == "MC-STOP"  : vidstrsrv.close_video_stream (ws, MULTICASTADDR);                                            await ws_broadcast("mc-stop "  + MULTICASTADDR)
	elif ms[0] == "PHOTO" : 
		filename = take_photo(camera, photoid = "remote", dir_name = "remote")
		await ws.send("PHOTO " + filename)
	elif ms[0] == "PHOTOX"    : 
		filename = take_photo(camera, photoid = "remote", dir_name = "remote")
		with open(filename, 'rb') as f:
			b64enc = base64.b64encode(f.read())
			b64enc_ascii = b64enc.decode('ascii')
			await ws.send("PHOTOX " + filename + ' ' + b64enc_ascii)
	elif ms[0] == "PHOTOX-LAST":
		if LASTPHOTO :
			with open(LASTPHOTO, 'rb') as f :
				b64enc = base64.b64encode(f.read())
				b64enc_ascii = b64enc.decode('ascii')
				await ws.send("PHOTOX-LAST " + LASTPHOTO + ' ' + b64enc_ascii)
		else :
				await ws.send("ERROR 3 PHOTOX-LAST")
			
	elif ms[0] == "REC-START" :
		if not vidrec.is_recording() :
			vidrec.start_recording()
			await ws.send("REC-START OK")
		else :
			await ws.send("ERROR 3 REC-START")
	elif ms[0] == "REC-STOP"  : vidrec.stop_recording(); await ws.send (s)
	elif ms[0] == "DEBUG-ON"  : 
		vidannot.debug = True
		vidannot.update()
		await ws.send('DEBUG-ON OK')
	elif ms[0] == "DEBUG-OFF" :
		vidannot.debug = False
		vidannot.update()
		await ws.send('DEBUG-OFF OK')
	elif ms[0] == "CONFIG-LOAD" : read_config(); await ws.send('CONFIG-LOAD OK')
	elif ms[0] == "CONFIG-SET":
		if len(ms) > 1 :
			set_config(ms[1])
			await ws.send('CONFIG-SET OK')
		else:
			await ws.send('ERROR 1 CONFIG-SET')
	elif ms[0] == "TURN-RIGHT":
		if len(ms) > 1 :
			steppermotor.steps("r", ms[1])
			await ws.send('TURN-RIGHT')
		else:
			await ws.send('ERROR 1 TURN-RIGHT')

	elif ms[0] == "TURN-LEFT":
		if len(ms) > 1 :
			steppermotor.steps("l", ms[1])
			await ws.send('TURN-LEFT')
		else:
			await ws.send('ERROR 1 TURN-LEFT')
	else: 
		await ws.send("ERROR 0 " + ms[0])
#}}}1

if __name__ == "__main__":
#{{{
#__Commandline_Arguments___________________________________________
	if str(sys.argv).count("-version") > 0 :
		print(VERSION)
		sys.exit()
	parser = ArgumentParser()
	parser.add_argument("-x", action='count', default = 0)
	parser.add_argument("-g", type=int,       default = DEBUGLEVEL)

	args = parser.parse_args()

	if args.x > 0 : DEBUG_OPENCV = True
	else          : DEBUG_OPENCV = False

	#__DEBUG________________________________________________________
	debug.debug_level = args.g
	debug.out("\n\n___KAMERA_SERVER_" + VERSION + "___ (" + HOSTNAME + ")_________", 1, COL_ok)
	debug.out("main thread: " + str(threading.get_ident()), 9, COL_start)

	#__BASE_DIR______________________________________________________
	if not os.path.isdir(BASE_DIR):
		try:
			os.makedirs(BASE_DIR)
			debug.out("main: BASE_DIR " + BASE_DIR + " created", 1, COL_warning)
		except:
			debug.out("main: ERROR creating BASE_DIR: " + BASE_DIR, 1, COL_error)
			sys.exit(1)
	
	#__Camera___________________________________________________________________________
	try:
		camera = picamera.PiCamera(sensor_mode=2, framerate = 15, resolution=(1296, 972))
		camera.rotation = 0
		camera.annotate_text_size = 32
		camera.annotate_background = picamera.Color('black')
		camera.annotate_foreground = picamera.Color('white')
	except:
		camera = None

	#__Video_________________________________________________________
	vidstrsrv   = VideoStreamServer(camera)
	vidrec      = VideoRecorder(camera, splitter_port = 2)
	vidannot    = VideoAnnotation(camera)
	vidannot.vr = vidrec
	vidrec.va   = vidannot
	vidrec.start()

	#__PIR___________________________________________________________
	# pir1 = PIR("pir1", PIN_PIR1, va = vidannot)
	# pir2 = PIR("pir2", PIN_PIR2, va = vidannot)
	pir3 = PIR("pir3", PIN_PIR3, va = vidannot)

	#__Cron____________________________________________________________
	cron = Cron();
	cron.add("day",        1,  9, 30, set_config, ['day'])
	cron.add("night",      1, 21, 30, set_config, ['night'])
	cron.add("night0",     1,  0,  0, set_config, ['night'])
	cron.add("reschedule", 1, 23,  0, reschedule_day_night, [])
	cron.sort()
	reschedule_day_night()
	cron.set_time_state()
	cron.start()

	#__UNIX_Signals____________________________________________________
	signal.signal(signal.SIGTERM, signal_handler)  # shut down the program
	signal.signal(signal.SIGHUP,  signal_handler)  # read the config file
	debug.out("main: UNIX-signals registered.")

	#__Stepper-Motor___________________________________________________
	steppermotor = StepperMotor()

	#__Shift_Register__________________________________________________
	shreg = Shift_74X595(16)

	#__Motion_Detection________________________________________________
	motion_detect = MotionDetection(camera, splitter_port = 3)
	motion_detect.start()
	vidannot.md = motion_detect	
	#__Timer___________________________________________________________
	phototimer = TimerInterval(60, take_photo, camera, "timer", "timer")
	annottimer = TimerInterval(1, vidannot.update)
	# watchtimer = TimerInterval(5, feed_watchdog)
	phototimer.start()
	annottimer.start()
	# watchtimer.start()

	#__read_config_file________________________________________________
	read_config()
	set_config(curr_config)

	#__Web-Sockets_____________________________________________________
	ws = websockets.serve(ws_message_handler, port = WS_PORT)
	debug.out("main: websockets initialized.")

	#__Async_Main_Loop_________________________________________________
	asyncio.get_event_loop().run_until_complete(ws)
	# for t in threading.enumerate():
	# 	if t.ident != threading.get_ident():
	# 		debug.out("thread: " + str(t.ident), 9, COL_warning)
	# 	else:
	# 		debug.out("main thread: " + str(t.ident),9, COL_warning)
	debug.out(f"main: multicast {MULTICASTADDR}", 2, COL_start)
	debug.out(f"main: ______ENTER_MAIN_LOOP______", 1, COL_ok)
	try:
		asyncio.get_event_loop().run_forever()
	except KeyboardInterrupt:
		debug.out("main: KeyboardInterrupt...", 1, COL_warning)
	debug.out(f"main: ______LEAVING_MAIN_LOOP____", 1, COL_warning)

	#__Stop_Threads____________________________________________________
	vidstrsrv.close_all_video_streams()
	vidstrsrv.stop()
	# pir1.stop();       pir1.join()
	# pir2.stop();       pir2.join()
	pir3.stop();       pir3.join()
	phototimer.stop(); phototimer.join()
	annottimer.stop(); annottimer.join()
	# watchtimer.stop(); watchtimer.join(); stop_watchdog()
	vidrec.stop();     vidrec.join()
	cron.stop();       cron.join()
	motion_detect.stop(); motion_detect.join();
	
	del vidrec
	del vidannot
	del vidstrsrv
	del phototimer
	del annottimer
	del motion_detect
	del cron
	# del pir1
	# del pir2
	del pir3

	#__close_camera___________________________________________________________
	if camera:
		debug.out("main: wait 2s befor closing the camera", 1)
		time.sleep(2)
		camera.close()
		debug.out("main: camera.close()", 1)
	else:
		debug.out("main: no camera to close", 1)

	#__any_Threads_left?______________________________________________________
	for t in threading.enumerate():
		debug.out("main: " + t.name, 9, COL_warning)
	debug.out("ENDE.\n", 1, COL_ok)
#}}}
