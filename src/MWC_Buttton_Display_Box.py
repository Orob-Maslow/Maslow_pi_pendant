#!/usr/bin/python
import requests
import time
'''
 TODO
  1- add functionality to change port number if changed in webcontrol...  startup arguement?
 add it as a startup arguement... call it with IP address and port from command line
  2- add webcontrol.json setting to enable use of external input (such as pendant, led, status, etc)
  3- add webcontrol.json setting to enable local service + #5
  4- add webcontrol.json file picker for file location of service file so users can make their own setup
    - have WC then "make" the service work, by making the folder if not there
    - moving the file to the .local/share/systemctl/<username>/ folder
    - enabling the service 
    - starting the service
  5- add webcontrol.json file picker for actual pendant executable file so it can "make" the service file.
  6- action menu to stop, reset or change the service options
'''
class Pendant():
 '''
    This class will set up buttons and take input from the buttons and send to the socket interface.
    Buttons:
      Shutdown
      Select
      Play / Run
      Pause
      STOP
      Up
      Left
      Right
      Down
      
    Menu items
      Select (STOP for 3 seconds) to activate menu, then red UP-DOWN buttons to move through options
        LED set to indicate menu change option
        put text on z display for xy mode
        put text on x for z mode
        put text on z for home mode
        put clock on X for clock mode and flash it
        PressSelect to select that mode
        Play mode can always be entered from play if machine not moving
      XY
        Go home Save (SELECT + UP) when not moving
        Save home position (SELECT + PAUSE) when not moving
        Reset home to center (SELECT + DOWN) when not moving
        increment change (SELECT + LEFT OR RIGHT) - 1,2,5,10,20,50,100,300 , show on z display
        STOP will stop movement
        STOP for 3 seconds will put back in menu
      Z
        zero (SELECT + PAUSE) When not moving
        increment change (SELECT + UP or DOWN) - 0.5, 1, 2, 5, 10 show on Y display
        STOP will stop movement
        STOP for 3 seconds will put back in menu
      Clock / Timer
        Clock on X, Date on Y
        Timer on z.  start is UP, stop is DOWN, reset is RIGHT
      Play
        default view is elapsed time on X
        gcode line number on Y
        SELECTt button will toggle 
          toggle to X position and Y position display for a few seconds
          toggle date/time for a few seconds 
        pause/resume
          show pause message on z line
          elapsed pause time on x (different counter)
          revert elapsed time back to original cut time minus pause time
        stop - works with simple press to stop all movment
     
 '''

 def __init__(self):
    '''
    init sets up the object properties that are used with the various functions below
    Setup gpio for buttons
    A, trigger, ztrigger, confirm, home, a, b, all help with making the buttons single press
    wm is the wiimote object
    wiiPendantConnect is the flag that lets the class know to try and reconnect
    '''   
    self.L = [1,2,4,8]
    self.DISTANCE = [0.1,1,10,100]
    self.Z = [0.1, 0.5, 1, 5]
    self.LED_ON = 2 # default is 10 mm.  range is  = 0.1, 1, 10, 100  Z_LED = 1 # default is 1 m.  range is 0.1, 0.5, 1, 5
    self.MINUS = 0
    self.PLUS = 0
    self.TRIGGER = 0
    self.ZTRIGGER = 0
    self.CONFIRM = -10
    self.StartTiime = time.time()
    self.HOME = 0
    self.A = 0
    self.B = 0
    self.wm = None
    self.wiiPendantConnected = False
    
    if self.connect():
      self.Send("system:connect")
    else:
      print("no controllers found")
 
 def Send(self,command):
    '''
    sends a put request to the webcontrol flask / socket io server at port 5000
    the /pendant in the address directs the server what commands to interpret
    input is the command that is set by the wiimote button press
    '''
    URL = "http://localhost:5000/pendant"
    try:
      r=requests.put(URL,command)
      print (r)
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)

 def connect(self):
      '''
      try to establish bluetooth communication with wii controller
      once connected, set LED to indicate distance
      set to button mode or it won't work at all
      if no connection, count and then return
      
      funciton returns 
         True when it connects
         False after 10 timeouts
      
      '''
      i=2
      while not self.wm:
        try:
          #self.wm=cwiid.Wiimote()
          #self.wiiPendantConnected = True
          #self.wm.led = self.L[self.LED_ON]
          #self.wm.rpt_mode = cwiid.RPT_BTN
          return(True)
        except RuntimeError:
          if (i>5):
            return(False)
          #print ("Error opening wiimote connection" )
          time.sleep(5)
          print ("attempt " + str(i))
          i += 1
#end init

 def rumble(self,mode=0):
  '''
  rumble shakes the wiimote when called.  short time delays vary the shake pattern
  '''
  if mode == 0: # start up heartbeat = 2 quick rumbles / prompt for confirmation
    self.wm.rumble=True
    time.sleep(.2)
    self.wm.rumble = False
    time.sleep(0.1)
    self.wm.rumble=True
    time.sleep(.2)
    self.wm.rumble = False

  if mode == 1: # shutdown or timeout
    self.wm.rumble=True
    time.sleep(.1)
    self.wm.rumble = False
    time.sleep(0.1)
    self.wm.rumble=True
    time.sleep(.2)
    self.wm.rumble = False

  if mode == 2: # shutdown or timeout
    self.wm.rumble=True
    time.sleep(.3)
    self.wm.rumble = False
    time.sleep(0.1)
    self.wm.rumble=True
    time.sleep(.3)
    self.wm.rumble = False

  if mode >= 30: # shutdown or timeout
    self.wm.rumble=True
    time.sleep(.5)
    self.wm.rumble = False
#end rumble

 def read_buttons(self):
   if (self.wiiPendantConnected == False):
      time.sleep(10)
      print ("connecting")
      if (self.connect()):
          print("connected")
   while(self.wiiPendantConnected == True):      
      # not using classic, this is if the remote is standing up though you hold it sideways
      if (self.CONFIRM > 0):
        elapsed = 1 - (time.time() - self.startTime)
        if elapsed > 5:
          self.rumble(1)  # cancelled due to timeout
          self.CONFIRM = - 10 # go back to normal

      if (self.wm.state['buttons'] & cwiid.BTN_A):
        if (self.A == 0):
            if (self.wm.state['buttons'] & cwiid.BTN_HOME):
                print ("Wiimote MOVE SLED TO HOME")
                self.Send("sled:home")
                self.rumble(1)
                self.A = 1
            if (self.wm.state['buttons'] & cwiid.BTN_B):
                print("Wii Remote Disconnect")
                self.Send("system:disconnect")
                self.wiiPendantConnected = False
                self.rumble(0)
                self.wm = None
                return # this should kill the process... if not how to do it?
        else:
          self.A = 0
        
      if (self.wm.state['buttons'] & cwiid.BTN_B):
        if (self.B == 0):
            if (self.wm.state['buttons'] & cwiid.BTN_RIGHT):
                print("Wiimote Start")
                self.rumble(1)
                self.B = 1
                self.Send("gcode:startRun")
            if (self.wm.state['buttons'] & cwiid.BTN_UP):
                print("Wiimote Pause")
                self.rumble(1)
                self.B = 1
                self.Send("gcode:pauseRun")
            if (self.wm.state['buttons'] & cwiid.BTN_DOWN):
                print("Wiimote Resume")
                self.rumble(1)
                self.B = 1
                self.Send("gcode:resumeRun")
            if (self.wm.state['buttons'] & cwiid.BTN_LEFT):
                print("Wiimote Stop")
                self.rumble(1)
                self.B = 1
                self.Send("gcode:stopRun")
            elif (self.wm.state['buttons'] & cwiid.BTN_A):
                print("Wii Remote Disconnect")
                self.Send("system:disconnect")
                self.wiiPendantConnected = False
                self.rumble(0)
                self.wm = None
                return
        else:
          self.B = 0
          
      if (self.wm.state['buttons'] & cwiid.BTN_1):
        if self.TRIGGER == 0:
          if (self.wm.state['buttons'] & cwiid.BTN_UP):
            print("Wiimote MOVE SLED LEFT")
            self.rumble(1)
            self.TRIGGER = 1
            self.Send("sled:left:" + str(self.DISTANCE[self.LED_ON]))
          if (self.wm.state['buttons'] & cwiid.BTN_DOWN):
            print("Wiimote MOVE SLED RIGHT")
            self.rumble(1)
            self.TRIGGER = 1
            self.RIGHT = 0
            self.Send("sled:right:" + str(self.DISTANCE[self.LED_ON]))
          if (self.wm.state['buttons'] & cwiid.BTN_RIGHT):
            print("Wiimote MOVE SLED UP")
            self.rumble(1)
            self.TRIGGER = 1
            self.UP = 0
            self.Send("sled:up:" + str(self.DISTANCE[self.LED_ON]))
          if (self.wm.state['buttons'] & cwiid.BTN_LEFT):
            print("Wiimote MOVE SLED DOWN")
            self.rumble(1)
            self.TRIGGER = 1
            self.DOWN = 0
            self.Send("sled:down:" + str(self.DISTANCE[self.LED_ON]))
          if (self.wm.state['buttons'] & cwiid.BTN_HOME):
            print("Wiimote SET NEW HOME POSITION")
            self.rumble(1)
            self.TRIGGER = 1
            self.Send("sled:defineHome")
      else:
        self.TRIGGER = 0

      if (self.wm.state['buttons'] & cwiid.BTN_2):
        if self.ZTRIGGER == 0:
          self.TRIGGER = 0
          if (self.wm.state['buttons'] & cwiid.BTN_RIGHT):
            print("Wiimote MOVE Z UP")
            self.rumble(2)
            self.ZTRIGGER = 1
            self.Send("zAxis:raise:" + str(self.Z[self.LED_ON]))
          if (self.wm.state['buttons'] & cwiid.BTN_LEFT):
            print("Wiimote MOVE Z DOWN")
            self.rumble(2)
            self.ZTRIGGER = 1
            self.Send("zAxis:lower:"+ str(self.Z[self.LED_ON]))
          if (self.wm.state['buttons'] & cwiid.BTN_UP):
            print("Wiimote stop Z axis")
            self.rumble(2)
            self.ZTRIGGER = 1
            self.Send("zAxis:stopZ")
          if (self.wm.state['buttons'] & cwiid.BTN_HOME):
            print("Wiimote Reset Z AXIS to 0")
            self.rumble(2)
            self.ZTRIGGER = 1
            self.Send("zAxis:defineZ0")
      else:
        self.ZTRIGGER = 0

      if (self.wm.state['buttons'] & cwiid.BTN_MINUS):
        if self.MINUS == 0:
          self.MINUS = 1
          self.LED_ON = self.LED_ON - 1
          if self.LED_ON < 0:
            self.LED_ON = 3
          print("Sled Move Distance is ", self.DISTANCE[self.LED_ON])
          print("Z Distance is ", self.Z[self.LED_ON])
          self.wm.led = self.L[self.LED_ON]
      else:
        self.MINUS = 0

      if (self.wm.state['buttons'] & cwiid.BTN_PLUS):
        if self.PLUS == 0:
          self.PLUS = 1
          self.LED_ON = self.LED_ON + 1
          if self.LED_ON > 3:
            self.LED_ON = 0
          print("Sled move Distance is ", self.DISTANCE[self.LED_ON])
          print("Z Distance is ", self.Z[self.LED_ON])
          self.wm.led = self.L[self.LED_ON]
      else:
        self.PLUS = 0
   #return True

  #end button scan
#END class


def main():
  wp = WiiPendant() # instantiate a wiipendant object named wp
  #while True:
  wp.read_buttons() # read the buttons in the wp object
   
  # when the remote is disconnected, the program stops
  # datetime A combination of a date and a time. Attributes: ()
if __name__ == "__main__":
    main()
