# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 17:05:33 2017

@author: jesse
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 11:04:42 2016

@author: Jesse Trinity (Coleman Lab)
"""

from psychopy import visual #always import visual first
from psychopy import monitors, logging, core
from psychopy import event as psyevent
from time import time
import Tkinter as tk
import tkFileDialog
import numpy as np
import csv as csv
import sys
import random

import serial.tools.list_ports
from pyfirmata import Arduino, util, serial

#Set up Arduino
class PhantomController:
    #Simulates Arduino pin functions
    #Used when no cotroller is connected
    def __init__(self):
        pass
    def get_pin(self, s):
        return PhantomPin()
    def exit(self):
        pass

class PhantomPin:
    #Pin for PhantomController class
    def __init__(self):
        pass
    def read(self):
        return 0.0
    def write(self, f):
        pass
        
#Open serial port
ports = list(serial.tools.list_ports.comports())
connected_device = None
for p in ports:
    if 'Arduino' in p[1]:
        try:
            board = Arduino(p[0])
            connected_device = p[1]
            print "Connected to Arduino"
            print connected_device
            break
        except serial.SerialException:
            print "Arduino detected but unable to connect to " + p[0]
if connected_device == None:
    for p in ports:
        if 'ttyACM' in p[0]:
            try:
                board = Arduino(p[0])
                connected_device = p[1]
                print "connected"
                break
            except serial.SerialException:
                pass
            
#start arduino if found
if connected_device is not None:
    it = util.Iterator(board)
    it.start()
    board.analog[0].enable_reporting()
elif connected_device is None:
    print "No connected Arduino - timestamp data will be text only"
    board = PhantomController()

trigger = board.get_pin('d:2:o')

trigger.write(0.0)


#-----WIDGETS-----
#Generic window framework
class Window(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.bind("<FocusIn>", self.parent.on_focus_in)
        
        if ('title' in kwargs):
            self.title(kwargs['title'])
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    #kill root when this window is closed
    def on_closing(self):
        self.parent.destroy()
        

#Generic *gridded* button framework
class Button(tk.Button):
    def __init__(self, container, text, command, position):
        self.button_text = tk.StringVar()
        self.button_text.set(text)
        button = tk.Button(container, textvariable = self.button_text, command = command)
        button.grid(row = position[0], column = position[1], padx = 5, pady  = 5, sticky = tk.N+tk.S+tk.E+tk.W)

class Entry(tk.Frame):
    def __init__(self, parent, label, position, default = ""):
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text = label)
        self.entry = tk.Entry(self)
        self.entry.insert(0, default)
        
        self.label.pack(side = "left")
        self.entry.pack(side = "right")
        
        self.grid(row = position[0], column = position[1], padx = 5, pady = 5, sticky = tk.N+tk.S+tk.E+tk.W)
    
    def get(self):
        return self.entry.get()
    
    def set_entry(self, v):
        self.entry.delete(0,tk.END)
        self.entry.insert(0,v)
        return


#-----Main Application-----
class MainApp(tk.Tk):
    def __init__(self, master = None, *args, **kwargs):
        tk.Tk.__init__(self, master, *args, **kwargs)
        self.title("Visual Light")
        self.refresh_rate= 60
        
        #populate windows by (class, name)
        self.windows = dict()
#        for (C, n) in ((window_one, "window 1"), (window_two,"window 2")):
        for (C, n) in ():
            window = C(self, title = n)
            self.windows[C] = window
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<FocusIn>", self.on_focus_in)
        
        self.anchor_frame = tk.Frame(self)
        self.anchor_frame.pack(side = "top")
        
        self.toolbar_frame = tk.Frame(self.anchor_frame)
        self.toolbar_frame.pack(side = "top")
        
        #Stim Options

        
        self.options_frame = tk.Frame(self.anchor_frame)
        self.options_frame.pack(side = "top")
        
        self.stim_frame = tk.Frame(self.anchor_frame)
        self.stim_frame.pack(side = "top")
        
        self.phase_reversal_frame = tk.Frame(self.stim_frame)
        self.phase_reversal_frame.pack(side = "left")
        
        self.drifting_frame = tk.Frame(self.stim_frame)
        self.drifting_frame.pack(side = "right")
        
        self.mix_frame = tk.Frame(self.anchor_frame)
        self.mix_frame.pack(side = "top")
                
        #create windows by name
#        window_names = ("window1", "window2")
#        windows = {name:Window(self.root, title = name) for name in window_names}
        
        #-----begin FLAGS-----
        self.ABORT = False
        
        #-----end FLAGS-----
               
        #-----begin app widgets-----
        #labels
        self.title_frame= tk.Frame(self.toolbar_frame)
        self.title_frame.pack(side = "top")
        
#        self.title_label = tk.Label(self.title_frame, text = "PsychoPy Controller")
#        self.title_label.grid(row = 0, column = 0)
        
        #Buttons
        self.button_frame = tk.Frame(self.toolbar_frame)
        self.button_frame.pack(side = "top")
        
        self.load_button = Button(self.button_frame, "Load File", self.load, (1, 0))
    
        self.open_screen_button = Button(self.button_frame, "Open Screen", self.open_experiment_window, (1, 1))
        
        self.run_test_grating_button = Button(self.button_frame, "Run Test Grating", self.run_stimulus(self.run_test_grating), (1, 2))
        
        self.abort_run_button = Button(self.button_frame, "Abort Run", self.abort_run, (1, 3))
        self.abort_warning_string = tk.StringVar()
        self.abort_warning_string.set("ready")
        self.abort_warning = tk.Label(self.button_frame, textvariable = self.abort_warning_string)
        self.abort_warning.grid(row = 1, column = 4, padx = 5, pady  = 5, sticky = tk.N+tk.S+tk.E+tk.W)
        
        #Entry Fields
        self.entry_frame = tk.Frame(self.options_frame)
        self.entry_frame.pack(side = "top")
        
        self.monitor_width_entry = Entry(self.entry_frame, "Monitor Width (cm)", (0, 0))
        self.monitor_width_entry.entry.insert(0, 37)
        
        self.monitor_distance_entry = Entry(self.entry_frame, "Monitor Distance (cm)", (1, 0))
        self.monitor_distance_entry.entry.insert(0, 20)
        
        self.horizontal_resolution_entry = Entry(self.entry_frame, "Horiz. Res (px)", (0,1))
        self.horizontal_resolution_entry.entry.insert(0, 1280)
        
        self.vertical_resolution_entry = Entry(self.entry_frame, "Vert. Res (px)", (1,1))
        self.vertical_resolution_entry.entry.insert(0, 1024)
        

        #Standard Phase Reversal
        self.phase_title_frame= tk.Frame(self.phase_reversal_frame)
        self.phase_title_frame.pack(side = "top")
        
        self.phase_options_frame = tk.Frame(self.phase_reversal_frame)
        self.phase_options_frame.pack(side = "top")
        
        self.phase_title = tk.Label(self.phase_title_frame, text = "Quick Phase Reversal")
        self.phase_title.pack(side = "top")
        
        self.phase_sessions = Entry(self.phase_options_frame, "Sessions", (0,0), default = 5)
        self.phase_orientation = Entry(self.phase_options_frame, "Orientation", (1,0), default = 0)
        self.phase_reversals = Entry(self.phase_options_frame, "Reversals", (2,0), default = 10)
        self.phase_frequency = Entry(self.phase_options_frame, "Frequency (hz)", (3,0), default = 2)
        self.phase_relaxation = Entry(self.phase_options_frame, "Inter-session length (s)", (4,0), default = 3)
        self.phase_startdelay = Entry(self.phase_options_frame, "Start Delay (s)", (5,0), default = 5)
        
        self.run_reversal_button = Button(self.phase_options_frame, "Run", self.run_stimulus(self.run_phase_reversal), (6, 0))
        
        #Standard Drifting Grating
        self.drift_title_frame = tk.Frame(self.drifting_frame)
        self.drift_title_frame.pack(side = "top")
        
        self.drift_options_frame = tk.Frame(self.drifting_frame)
        self.drift_options_frame.pack(side = "top")
        
        self.drift_title = tk.Label(self.drift_title_frame, text = "Quick Drifting Grating")
        self.drift_title.pack(side = "top")
        
        self.drift_sessions = Entry(self.drift_options_frame, "Sessions", (0,0), default = 5)
        self.drift_orientation = Entry(self.drift_options_frame, "Orientation", (1,0), default = 0)
        self.drift_duration = Entry(self.drift_options_frame, "Duration (s)", (2,0), default = 3)
        self.drift_rate_entry = Entry(self.drift_options_frame, "Drift Rate (hz)", (3,0), default = 1)
        self.drift_relaxation = Entry(self.drift_options_frame, "Inter-session length (s)", (4,0), default = 3)
        self.drift_startdelay = Entry(self.drift_options_frame, "Start Delay (s)", (5,0), default = 5)
        
        self.run_drift_button = Button(self.drift_options_frame, "Run", self.run_stimulus(self.run_drifting_grating), (6, 0))
        
        #Mixed Run
        self.mix_title_frame = tk.Frame(self.mix_frame)
        self.mix_title_frame.pack(side = "top")
        
        self.mix_options_frame = tk.Frame(self.mix_frame)
        self.mix_options_frame.pack(side = "top")
        
        self.mix_title = tk.Label(self.mix_title_frame, text = "Mixed Run")
        self.mix_title.pack(side = "top")
        
        self.mix_relaxation = Entry(self.mix_options_frame, "Inter-session length (s)", (0,4), default = 3)
        self.mix_startdelay = Entry(self.mix_options_frame, "Start Delay (s)", (0,5), default = 5)
        self.run_mix_button = Button(self.mix_options_frame, "Run", self.run_stimulus(self.run_mixed_stimuli), (0, 6))

        #-----end app widgets-----
        
        #-----begin psychopy charm-----
        self.experiment_window = 0
        self.hres = 1920
        self.vres = 1080
        self.monitor_width = 37
        self.monitor_distance = 20
        self.Wgamma = 1.793
    
        self.stim_seconds =1
        self.drift_rate = 0.01
        self.gray_level = 2*((0.5)**(1/self.Wgamma))-1
        
        self.Nframes = self.refresh_rate * self.stim_seconds
        
        self.spatial_freq=0.05
        self.number_reversals = 100
        
        self.levels = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        self.level_mapping = {0:self.levels[0], 45:self.levels[1], 90: self.levels[2],
                              135:self.levels[3], 180:self.levels[4], 225:self.levels[5],
                                270:self.levels[6], 315:self.levels[7]}
        
        self.mon = monitors.Monitor("newmon", distance = self.monitor_distance, width = self.monitor_width)
        self.mon.currentCalib['sizePix'] = [self.hres, self.vres]
        self.mon.saveMon()
        
        print "Monitor details:"
        print self.mon.currentCalib
        
        self.window = None
        self.fixation = None
        self.stim = None
        self.frame_list = list()

        sin = np.sin(np.linspace(0, 2 * np.pi, 256)).astype(np.float64)
        sin = (sin + 1)/2
        sin = sin**(1/self.Wgamma)
        sin = 2* sin -1
        self.texture = np.array([sin for i in range(256)])
        
        
        #-----end psychopy charm-----
        
        #variables
        self.file_list = list()
        self.data = list()
        
        #set root window position (needs to happen last to account for widget sizes)
        self.update()
        self.hpos =  self.winfo_screenwidth()/2 - self.winfo_width()/2
        self.vpos = 0
        self.geometry("+%d+%d" % (self.hpos, self.vpos))
        
        self.mainloop()
    
    #Dummy command function
    def default_onclick(self):
        print "widget pressed"
    

    def open_experiment_window(self):
        #Opens the experiment window, closes if already open
        if self.window is None:
            #build window and draw calibrated gray
            self.window = visual.Window(size=[self.hres,self.vres],monitor=self.mon, fullscr = False ,allowGUI = True, units="deg", screen = self.experiment_window)
            self.window.waitBlanking = False
            self.fixation = visual.GratingStim(win=self.window, size=200, pos=[0,0], sf=0, color=[self.gray_level, self.gray_level, self.gray_level])
            self.fixation.setAutoLog(False)
            self.fixation.draw()
            self.window.flip()
            self.open_screen_button.button_text.set("Close Window")
        elif self.window is not None:
            self.window.close()
            self.open_screen_button.button_text.set("Open Window")
            self.window = None
    

    def run_test_grating(self):
        #Displays a test grating for predetermined interval
        #Use to check timing
        for i in range(2):
            self.build_stim(self.stim, 'drift', 2.0, direction = '-', orientation = 0)
            self.build_stim(self.fixation, 'gray', 1.0)
            self.build_stim(self.stim, 'reversal', 4, frequency = 2, orientation = 45)
            self.build_stim(self.fixation, 'gray', 1.0)
        for i in range(2):
            self.build_stim(self.stim, 'drift', 2.0, direction = '+', orientation = 90)
            self.build_stim(self.fixation, 'gray', 1.0)
            self.build_stim(self.stim, 'reversal', 4, frequency = 2, orientation = 135)
            self.build_stim(self.fixation, 'gray', 1.0)
            
    def run_phase_reversal(self):
        #builds a set of randomly interleaved phase reversal stimuli
        #takes input @ 'Quick Phase Reversal' toolbar
        start_delay = self.get_num_field(self.phase_startdelay)[0]
        sessions = int(self.get_num_field(self.phase_sessions)[0])
        reversals = int(self.get_num_field(self.phase_reversals)[0])
        frequency = self.get_num_field(self.phase_frequency)[0]
        relaxation = self.get_num_field(self.phase_relaxation)[0]
        orientations = self.get_num_field(self.phase_orientation)
        
        #EACH orientation is presented session # of times
        presentations = orientations * sessions
        random.shuffle(presentations)
        
        self.build_stim(self.fixation, 'gray', start_delay)
        for block in presentations:
            self.build_stim(self.stim, 'reversal', reversals, frequency = frequency, orientation = block)
            self.build_stim(self.fixation, 'gray', relaxation)
    
    def run_drifting_grating(self):
        #builds a set of randomly interleaved drifting grating stimuli
        #takes input @ 'Quick Drifting Grating' toolbar
        start_delay = self.get_num_field(self.drift_startdelay)[0]
        sessions = int(self.get_num_field(self.drift_sessions)[0])
        relaxation = self.get_num_field(self.drift_relaxation)[0]
        orientations = self.get_num_field(self.drift_orientation)
        drift_rate = self.get_num_field(self.drift_rate_entry)[0]
        duration = self.get_num_field(self.drift_duration)[0]
        
        #EACH orientation is presented session # of times
        presentations = orientations * sessions
        random.shuffle(presentations)
        
        self.build_stim(self.fixation, 'gray', start_delay)
        for block in presentations:
            self.build_stim(self.stim, 'drift', duration, drift_rate = drift_rate ,orientation = block)
            self.build_stim(self.fixation, 'gray', relaxation)
    
    def run_mixed_stimuli(self):
        #builds a set of randomly interleaved phase reversal and drifting gratign stimuli
        #takes input @ 'Quick Drifting Grating' and 'Quick Phase Reversal' toolbars
        #inputs are otherwise overwritten by 'Mixed Run' toolbar
        start_delay = self.get_num_field(self.mix_startdelay)[0]
        relaxation = self.get_num_field(self.mix_relaxation)[0]
        
        phase_sessions = int(self.get_num_field(self.phase_sessions)[0])
        reversals = int(self.get_num_field(self.phase_reversals)[0])
        frequency = self.get_num_field(self.phase_frequency)[0]
        phase_orientations = self.get_num_field(self.phase_orientation)
        phase_orientations_p = [['p', x] for x in phase_orientations]
        
        drift_sessions = int(self.get_num_field(self.drift_sessions)[0])
        drift_rate = self.get_num_field(self.drift_rate_entry)[0]
        duration = self.get_num_field(self.drift_duration)[0]
        drift_orientations = self.get_num_field(self.drift_orientation)
        drift_orientations_d = [['d', x] for x in drift_orientations]
        
        #EACH orientation per stim type is presented session # of times
        presentations = (phase_orientations_p * phase_sessions) + (drift_orientations_d * drift_sessions)
        random.shuffle(presentations)
        
        self.build_stim(self.fixation, 'gray', start_delay)
        for block in presentations:
            if block[0] == 'p':
                self.build_stim(self.stim, 'reversal', reversals, frequency = frequency, orientation = block[1])
                self.build_stim(self.fixation, 'gray', relaxation)
            elif block[0] == 'd':
                self.build_stim(self.stim, 'drift', duration, drift_rate = drift_rate ,orientation = block[1])
                self.build_stim(self.fixation, 'gray', relaxation)
            else:
                print "missing stim block"

    

    def build_stim(self, stim, stim_type, length, **kwargs):
        #inserts requested stimuli into frame_list. stimuli are not shown until run_stimulus is called
        #length in seconds for static image and drifting, length in number of reversals for phase reversal (2 * num stims)
        orientation = 0
        direction = '+'
        drift_rate = 1.0/self.refresh_rate
        
        if 'orientation' in kwargs:
            orientation = kwargs['orientation']
        if 'direction' in kwargs:
            direction = kwargs['direction']
        if 'drift_rate' in kwargs:
            drift_rate = drift_rate * kwargs['drift_rate']
        
        
        if stim_type == 'gray':
            
            frame_info = {"type":"gray","draw":stim.draw,"setPhase":stim.setPhase,"setOri":stim.setOri,"orientation":orientation}
            frame_info["phase"] = tuple((0.0,))
            for frame in range(int(length * self.refresh_rate)):
                self.frame_list.append(frame_info)
                
        if stim_type == 'drift':
            
            frame_info = {"type":"drift","draw":stim.draw,"setPhase":stim.setPhase,"setOri":stim.setOri,"orientation":orientation}
            frame_info["phase"] = tuple((drift_rate,direction))
            for frame in range(int(length * self.refresh_rate)):
                self.frame_list.append(frame_info)
                
        if stim_type == 'reversal':
            for reversal in range(length):
                
                frame_info = {"type":"flip","draw":stim.draw,"setPhase":stim.setPhase,"setOri":stim.setOri,"orientation":orientation}
                frame_info["phase"] =  tuple((0.0,))
                for frame in range(int(self.refresh_rate / kwargs['frequency'])):
                    self.frame_list.append(frame_info)
                    
                frame_info_rev = {"type":"flop","draw":stim.draw,"setPhase":stim.setPhase,"setOri":stim.setOri,"orientation":orientation}
                frame_info_rev["phase"] = tuple((0.5,))
                for frame in range(int(self.refresh_rate / kwargs['frequency'])):        
                    self.frame_list.append(frame_info_rev)
                    
    def run_stimulus(self, stim_function):
        #run_stimulus shows stims inserted into frame_list by the input stim_function. 
        #Input stim_function use build_stim to populate frame_list
        def wrapper():
            self.frame_list = list()
            if self.window is None:
                return
            
            self.withdraw()
            self.stim = visual.GratingStim(tex = self.texture, win=self.window, mask=None, size=200, pos=[0,0], sf=self.spatial_freq , ori=135)
            self.stim.setAutoLog(False)
            self.window.setRecordFrameIntervals(True)
            self.window._refreshThreshold=1/60.0+0.002
            
            #set the log module to report warnings to the std output window (default is errors only)
            lastLog = logging.LogFile("lastRun.log", level = logging.WARNING, filemode = 'w')
            timestamps = list()
            #centralLog = logging.LogFile("psychopyExps.log", level=logging.WARNING, filemode='a')
            logging.console.setLevel(logging.WARNING)
            
            fields = self.get_all_fields()
            
            #All experiments given 1 second min padding
            self.build_stim(self.fixation, 'gray', 1)
            
            stim_function()
                        
            #set trigger high on first frame flip
            self.window.callOnFlip(trigger.write, 1.0)
            
            run_clock = core.Clock()
            logging.setDefaultClock(run_clock)
            #self.window.logOnFlip(level=logging.exp, msg=str("begin trial"))
            for i in range(len(self.frame_list)):
                if 'escape' in psyevent.getKeys():
                    self.deiconify()
                    break
                psyevent.clearEvents()
                
                #Sets value of arduino pin and tells psychopy to write it when the monitor refreshes
                
                #calls build stim phase and direction entries in stim.setPhase
                self.frame_list[i]["setPhase"](* self.frame_list[i]["phase"])
                
                #calls build stim orientation entry in stim.setOrientation
                self.frame_list[i]["setOri"](self.frame_list[i]["orientation"])            
                
                #draws the stim
                self.frame_list[i]["draw"]()
                
                if(i > 0 and self.frame_list[i]["type"] != self.frame_list[i-1]["type"]):
                    #self.window.logOnFlip(level=logging.exp, msg=str(self.frame_list[i]["type"])+" "+str(self.frame_list[i]["orientation"]))
                    timestamps.append((run_clock.getTime(), self.frame_list[i]["type"], self.frame_list[i]["orientation"]))

                self.window.flip()
    
    
            self.fixation.draw()
            self.window.callOnFlip(trigger.write, 0.0)
            #self.window.logOnFlip(level=logging.exp, msg=str("end trial"))
            self.window.flip()
            logging.flush()
            self.window.setRecordFrameIntervals(False)
            
            self.update()
            
            #save data
            target = "lastRun.csv"
            self.save_to_csv(target, fields, timestamps)
                            
            print "total frames shown: " + str(len(self.frame_list))
            
            self.deiconify()
            
        return wrapper

    def get_all_fields(self):
        fields = dict()
        fields["startDelay"] = self.get_num_field(self.mix_startdelay)[0]
        fields["relaxation"] = self.get_num_field(self.mix_relaxation)[0]
        
        fields["phaseSessions"] = int(self.get_num_field(self.phase_sessions)[0])
        fields["reversals"] = int(self.get_num_field(self.phase_reversals)[0])
        fields["frequency"] = self.get_num_field(self.phase_frequency)[0]
        fields["phaseOrientations"] = self.get_num_field(self.phase_orientation)
        
        fields["driftSessions"] = int(self.get_num_field(self.drift_sessions)[0])
        fields["driftRate"] = self.get_num_field(self.drift_rate_entry)[0]
        fields["driftDuration"] = self.get_num_field(self.drift_duration)[0]
        fields["driftOrientations"] = self.get_num_field(self.drift_orientation)
        
        fields["phaseStartDelay"] = self.get_num_field(self.phase_startdelay)[0]
        fields["phaseRelaxation"] = self.get_num_field(self.phase_relaxation)[0]
        fields["driftStartDelay"] = self.get_num_field(self.drift_startdelay)[0]
        fields["driftRelaxation"] = self.get_num_field(self.drift_relaxation)[0]
        
        return fields
    
    def set_all_fields(self, fields):
        self.mix_startdelay.set_entry(fields["startDelay"])
        self.mix_relaxation.set_entry(fields["relaxation"])
        self.phase_sessions.set_entry(fields["phaseSessions"])
        self.phase_reversals.set_entry(fields["reversals"])
        self.phase_frequency.set_entry(fields["frequency"])
        self.phase_orientation.set_entry(fields["phaseOrientations"])
        self.drift_sessions.set_entry(fields["driftSessions"])
        self.drift_rate_entry.set_entry(fields["driftRate"])
        self.drift_duration.set_entry(fields["driftDuration"])
        self.drift_orientation.set_entry(fields["driftOrientations"])
        self.phase_startdelay.set_entry(fields["phaseStartDelay"])
        self.phase_relaxation.set_entry(fields["phaseRelaxation"])
        self.drift_startdelay.set_entry(fields["driftStartDelay"])
        self.drift_startdelay.set_entry(fields["driftStartDelay"])
        self.drift_duration.set_entry(fields["driftDuration"])
        
        return
    
    def abort_run(self):
        if self.window is not None:
            self.ABORT = True
            self.abort_warning_string.set("aborting")

    #Dummy event function
    def default_on_event(self):
        print "event detected"
        
    def on_focus_in(self, event):
        self.lift()
        for win in self.windows:
            self.windows[win].lift()
    
    def on_closing(self):
        if self.window is not None:
            #if messagebox.askokcancel("Quit", "Do you want to quit?"):

            self.window.close()
        board.exit()
        self.destroy()
    
    #return fields as float values
    def get_num_field(self, field):
        field_entry = field.get()
        entries = field_entry.split(',')
        num_entries = []
        for entry in entries:
            try:
                num_entry = float(entry)
            except ValueError:
                print "Bad entry field value"
                return None
            num_entries.append(num_entry)
        return num_entries
    
    #create pseudo-random presentation list disallowing repetitions
    def generate_codes(self, orientations):
        orientations.sort()
        
    
    #Open a file dialog and record selected filenames to self.file_names
    def load(self):
        files = tkFileDialog.askopenfilenames()
        self.file_list = list(files)
        fn = self.file_list[0]
        try:
            with open(fn, 'rb') as csv_file:
                reader = csv.reader(csv_file, delimiter = ',')
                field_names = reader.next()
                field_values = reader.next()
                
                fields = {field_names[i]:field_values[i] for i in range(len(field_names))}
                
                fields["phaseOrientations"] = ''.join( c for c in fields["phaseOrientations"] if  c not in '[]' )
                fields["driftOrientations"] = ''.join( c for c in fields["driftOrientations"] if  c not in '[]' )
                
                self.set_all_fields(fields)
        except IOError:
            print "Unable to open file. Is it open in another program?"
            
        return
    
    def file_to_array(self, fn):
        with open(fn, 'rb') as open_file:
            self.data.append(np.array(open_file))
    
    def csv_to_array(self, fn):
        with open(fn, 'rb') as csv_file:
            reader = csv.reader(csv_file, delimiter = ',')
            self.data.append(np.array(reader))
            
    def save_to_csv(self, target, fields, timestamps):
        try:
            with open(target, 'w+') as fn:
                fn.seek(0)
                w=csv.writer(fn, delimiter = ',', lineterminator = "\n")
                w.writerow(fields.keys())
                w.writerow(fields.values())
                for i in range(len(timestamps)):
                    w.writerow(timestamps[i])
                fn.truncate()
        except IOError:
            print "Unable to open file. Is it open in another program?"
            
        return

              
#-----Windows-----
#Not currently in use. Available for adding additional control panels. See tk framework file for usage.
#Left Window
class window_one(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #self.title("Window One")
        #Set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos = 0
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % ( self.hpos, self.vpos))

#Right Window
class window_two(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos =  self.winfo_screenwidth() - self.winfo_width()
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % (self.hpos, self.vpos))

                
if __name__ == "__main__":
    MainApp()
