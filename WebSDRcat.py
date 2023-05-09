#
# Demo of how to control (i.e. synchronize) a WebSDR in a browser, from an
# actual physical radio connected to the computer by CAT control.


# This requires to install

# - hamlib (https://hamlib.github.io/hamlib/), which is used to control the radio with CAT commands, by
#       . rigctld (https://hamlib.github.io/hamlib/rigctld.1.html)
#       . rigctl (https://hamlib.github.io/hamlib/rigctl.1.html)

# - Python (https://www.python.org/), which is used to run this script, and the following Python packages
# - Selenium (https://www.selenium.dev/), which is used to control the browser
# - the Chrome driver (https://chromedriver.chromium.org/downloads), which is used to control the Chrome browser
# - the Chrome browser (https://www.google.com/chrome/)
# - a known WebSDR (tested so far only with http://websdr.ewi.utwente.nl:8901/)

# 9 May 2023 - Michele Giugliano, PhD (iv3ifz)


# This script is released under the MIT license
# https://opensource.org/licenses/MIT

#------------------------------------------------------------
# Import the required libraries
import os                   # for system calls
import subprocess           # for system calls
import time                 # for sleep

from selenium import webdriver                  # for browser control
from selenium.webdriver.common.keys import Keys # for browser control
from selenium.webdriver.common.by import By     # for browser control

# Let's define some constants...
serial_port = '/dev/cu.usbserial-0567003F3120'      # The serial port of the radio, check it with ls /dev/cu.usbserial*
baud_rate   = '115200'                              # The baud rate of the radio, set for CAT control in the radio's menu
model       = '2037'                                # The model of the radio (KENWOOD TS-590SG)
URL         = 'http://websdr.ewi.utwente.nl:8901/'  # The URL of the WebSDR


#------------------------------------------------------------
# Let's define some useful functions
def launch_process(command):    # Launch a process in the background...
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    try:
        out, err = p.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        #p.kill()                           # The child process is not killed if the timeout expire. I exploit it to launch rigctld.
        #out, err = proc.communicate()
        return None, ''                     # If the process is still running, return an empty string


    out = out.decode('utf-8')
    return err, out


def check_rigctld():    # Check that a process named 'rigctld' is running in the background...
    err, out = launch_process(['ps', '-A'])
    # p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    # out, err = p.communicate()
    # out = out.decode('utf-8')

    for line in out.splitlines():
        if 'rigctld' in line:
            print('The daemon rigctld was already running!')
            return True     # rigctld is already running: nothing to do, exiting!

    # ...if not, start it
    print('Starting the deamon rigctld...')
    err, out = launch_process(['rigctld', '-m', model, '-r', serial_port, '-s',  baud_rate])

    # p = subprocess.Popen(['rigctld', '-m', model, '-r', serial_port, '-s',  baud_rate], stdout=subprocess.PIPE)
    # out, err = p.communicate()
    # out = out.decode('utf-8')

    if err is not None:
        print('Error starting the daemon rigctld!')
        print(err)
        exit()

    return True


def read_frequency(): # Let's now read the frequency from the radio
    err, out = launch_process(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'f'])
    # p = subprocess.Popen(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'f'], stdout=subprocess.PIPE)
    # out, err = p.communicate()
    # out = out.decode('utf-8')

    out = float(out[:-1])     # Let's remove the trailing \n and convert it to a float
    return out                # Let's return the frequency


def read_mode(): # Let's now read the mode from the radio
    err, out = launch_process(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'm'])
    # p = subprocess.Popen(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'm'], stdout=subprocess.PIPE)
    # out, err = p.communicate()
    # out = out.decode('utf-8')

    # out is made of two lines: the first one is the mode name, the second one is the bandwidth
    mode = out.splitlines()[0] # Let's take the first line
    bandwidth = out.splitlines()[1] # Let's take the second line
    return mode, bandwidth
#------------------------------------------------------------
#------------------------------------------------------------
#------------------------------------------------------------


# Let's start the script
freq_old = 0
mode_old = ""
bandwidth_old = ""

# Let's first check that rigctld is running or launch it otherwise!
check_rigctld()

# Let's now launch the Chrome browser
driver = webdriver.Chrome()

# Let's point it to the WebSDR URL and wait a few seconds...
driver.get(URL)
time.sleep(3)       # wait 3 seconds


# Let's make the waterfall very large and build the corresponding javascript command
script = "waterfallheight(400); waterfallspeed(2); stretch_waterfalls(); settings_store();"
driver.execute_script(script)

# Now let's read the of the radio frequency and set WebSDR accordingly, in an infinite loop
while True:
    freq = read_frequency()               # read the frequency from the radio
    mode, bandwidth = read_mode()         # read the mode from the radio
    time.sleep(.02)                       # wait 20 ms

    # Let's zoom in, in case the frequency has changed by more than 1 MHz
    if abs(freq-freq_old) > 1e6: # If the frequency has changed by more than 1 MHz, let's zoom out and build the javascript command
        script = "wfset(2)"     # Let's zoom maximally and build the corresponding javascript command
        #script = "wfset(3)"     # Let's zoom on the current band and build the corresponding javascript command
        driver.execute_script(script)

    # Take an action only if the frequency has changed
    if freq != freq_old:       # if the frequency has changed, print it
        #print('{:.2f} kHz      '.format(freq/1000.), end='\r')
        freq_old = freq        # update the old frequency

        # Now set the frequency by executing a javascript command
        script = "setfreqb(" + '{:.2f}'.format(freq/1000.) + ")" # Let's convert the frequency to a string and build the javascript command
        driver.execute_script(script)


    # script = "setmute(1)" # Let's unmute the audio and build the javascript command
    # driver.execute_script(script)

    # script = "sethidelabels(1)" # Let's hide the labels and build the javascript command
    # driver.execute_script(script)

    # Take an action only if the mode has changed
    if mode != mode_old:
        mode_old = mode
        match mode:         # Now set the mode by executing a javascript command (i.e. AM, LSB, USB, CW, FM, DIGI, SAM, DRM)
            case "AM":   driver.execute_script("set_mode('AM')")
            case "PKTLSB":  driver.execute_script("set_mode('LSB')")
            case "PKTUSB":  driver.execute_script("set_mode('USB')")
            case "LSB":  driver.execute_script("set_mode('LSB')")
            case "USB":  driver.execute_script("set_mode('USB')")
            case "CW":   driver.execute_script("set_mode('CW')")
            case "RTTY":   driver.execute_script("set_mode('CW')")
            case "FM":   driver.execute_script("set_mode('FM')")
            case "FM-D":   driver.execute_script("set_mode('FM')")
            case _:      driver.execute_script("set_mode('AM')")

    # Check whether the frequency on the WebSDR page changed (i.e. the user clicked on the waterfall)
    tmp = driver.find_element(By.NAME, "frequency") # Let's read the frequency from the WebSDR page
    freq_web = float(tmp.get_attribute('value'))*1000. # Let's convert it to a float and to kHz

    if abs(freq-freq_web) > 1:   # If the WebSDR frequency has changed by more than 1 kHz, let's invoke hamlib to set the frequency on the radio!
        # Let's set the frequency by invoking hamlib
        err, out = launch_process(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'F', str(freq_web)])
        # p = subprocess.Popen(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'F', str(freq_web)], stdout=subprocess.PIPE)
        # out, err = p.communicate()
        # out = out.decode('utf-8')

    # Check whether the mode on the WebSDR page changed (i.e. the user clicked on the buttons)
    # for mode_web in ["AM", "LSB", "USB", "CW", "FM"]:
    #     tmp = driver.find_element(By.ID, "btn-" + mode_web)
    #     tmp.get_attribute('style')
    #     if tmp != '':
    #         break

    # if mode_web != mode:   # If the WebSDR mode has changed, let's invoke hamlib to set the mode on the radio!
    #     # Let's set the mode by invoking hamlib
    #     err, out = launch_process(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'M', mode_web])
    #     # p = subprocess.Popen(['rigctl', '-m', model, '-r', serial_port, '-s', baud_rate, 'M', mode_web], stdout=subprocess.PIPE)
    #     # out, err = p.communicate()
    #     # out = out.decode('utf-8')



# <input type="text" style="font-size:20px; text-align:center" size="10" name="frequency" onkeyup="setfreqif_fut(this.value);">
