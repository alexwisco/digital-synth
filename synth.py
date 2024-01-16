# Prototype 05
# Automating wave object generation

import numpy as np
import sounddevice as sd
from gpiozero import Button
import sys
import time
from signal import pause

# map buttons
btn1 = Button(4)
btn2 = Button(17)
btn3 = Button(27)
btn4 = Button(22)
btn5 = Button(5)
btn6 = Button(6)
btn7 = Button(13)
btn8 = Button(19)
btn9 = Button(21)
btn10 = Button(20)
btn11 = Button(16)
btn12 = Button(12)
btn_wave_down = Button(25) # cycle left through wave array
btn_wave_up = Button(24) # cycle right through wave array 
btn_octave_down = Button(23) # cycle left through octaves
btn_octave_up = Button(18) # cycle right through octaves

# array of frequencies correlating to each C note (C0 to C8) that changes the octave while playing
C_ARR = np.array([16.35, 32.70, 65.41, 130.81, 261.63, 523.25, 1046.50,
                 2093.00, 4186.01])


# starting button on the board that is changed with `btn_wave_down` and `btn_wave_up` 
c_freq = C_ARR[5] # let's start with C5
c_freq_ind = 5 # index of c note

# array of wave forms to choose from 
WAVES_ARR = np.array(["sin", "sawtooth", "square"])
# lets just follow the same format used for octave changing
wave = WAVES_ARR[0] # always start program on sin
wave_ind = 0 # index of current wave form
num_waves = 3 # number of waves user has to choose from

# sample rate 
sr = 44100

# Helper Functions
def direction(start, end):
    """Return 1 if end > start, -1 if end < start. (Keeps values consistent instead of sliding up or down)"""
    return 1 if end > start else -1

# freq of pitch given middle c
def pitch_to_frequency(pitch):
    return c_freq * 2 ** (pitch / 12)

# ratio of two amps on dB change
def decibels_to_amplitude_ratio(decibels):
    return 2 ** (decibels / 10)

def interval_to_frequency_ratio(interval):
    return 2 ** (interval / 12)

# frame # to time 
def frames_to_time(frames, framerate):
    return frames / framerate

# frame data into time arr
def frames_to_time_array(start_frame, frames, framerate):
    # frame to time
    start_time = frames_to_time(start_frame, framerate)
    end_time = frames_to_time(start_frame + frames, framerate)
    # time array with one entry for each frame
    time_array = np.linspace(start_time, end_time, frames)
    return time_array

# wave object with dynamic duration
class SineWaveGenerator:

    def __init__(self, pitch=0, decibels=10, decibels_per_second=1, samplerate=sr):
        self.frequency = pitch_to_frequency(pitch)
        self.phase = 0
        self.amplitude = decibels_to_amplitude_ratio(decibels)
        self.pitch_per_second = 12
        self.decibels_per_second = 1
        self.goal_frequency = self.frequency
        self.goal_amplitude = self.amplitude
        self.sr = sr
        
        # create output stream
        self.output_stream = sd.OutputStream(
            channels=1,
            callback=lambda *args: self._callback(*args),
            samplerate=samplerate,
        )

    # set the objects frequency
    def set_pitch(self, value):
        self.frequency = pitch_to_frequency(value)
        self.goal_frequency = self.frequency

    # calc frequency values for next chunk
    def new_frequency_array(self, time_array):
        direc = direction(self.frequency, self.goal_frequency)
        new_frequency = self.frequency * interval_to_frequency_ratio(
            direc * self.pitch_per_second * time_array
        )
        return new_frequency

    # calc amplitudes for next chunk
    def new_amplitude_array(self, time_array):
        direc = direction(self.amplitude, self.goal_amplitude)
        new_amplitude = self.amplitude * decibels_to_amplitude_ratio(
            direc * self.decibels_per_second * time_array
        )
        return new_amplitude

    # calc phase 
    def new_phase_array(self, new_frequency_array, delta_time):
        return self.phase + np.cumsum(new_frequency_array * delta_time)

    # next array for given number of frames
    def next_data(self, frames):

        # convert frame info to time info
        time_array = frames_to_time_array(0, frames, self.sr)
        # delta time = elapsed time
        delta_time = time_array[1] - time_array[0]

        # calc the frequencies, phases, and amplitudes of this batch of data
        new_frequency_array = self.new_frequency_array(time_array)
        new_phase_array = self.new_phase_array(new_frequency_array, delta_time)
        new_amplitude_array = self.new_amplitude_array(time_array)

        # create the sinewave array
        sinewave_array = new_amplitude_array * np.sin(2 * np.pi * new_phase_array)

        # update phase to prevent overflow error
        self.phase = new_phase_array[-1] % 1

        return sinewave_array

    # for output stream
    def _callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        # get and use the waves next batch of data
        data = self.next_data(frames)
        outdata[:] = data.reshape(-1, 1)

    # run this osc
    def start(self):
        self.output_stream.start()
    # stop this osc
    def stop(self):
        self.output_stream.stop()

# Create oscillator objects
osc = SineWaveGenerator()
osc1 = SineWaveGenerator()
osc2 = SineWaveGenerator()
osc3 = SineWaveGenerator()
osc4 = SineWaveGenerator()

# for printing and documenting
osc_m = "osc freq: " 
osc1_m = "\nosc1 freq: "
osc2_m = "\nosc2 freq: "
osc3_m = "\nosc3 freq: "
osc4_m = "\nosc4 freq: "

osc_amp_m = "osc amplitude: "
osc1_amp_m = "osc1 amplitude: "
osc2_amp_m = "osc2 amplitude: "
osc3_amp_m = "osc3 amplitude: " 
osc4_amp_m = "osc4 amplitude: "

# change octave up or down dependent on which octave shifting button is pressed
def drop_octave():
    global c_freq
    global C_ARR
    global c_freq_ind
    
    if (c_freq == C_ARR[0]):
        print("                     ")
        print("********************")
        print("Cannot shift octave down, limit reached")
    else: # else shift the octave down
        c_freq_ind = c_freq_ind - 1 # shift index down
        c_freq = C_ARR[c_freq_ind]
        print("Octave changed to octave: " + str(c_freq_ind))
# same thing
def up_octave():
    global c_freq
    global C_ARR
    global c_freq_ind
    
    if (c_freq == C_ARR[8]):
        print("                     ")
        print("********************")
        print("Cannot shift octave up, limit reached")
        print("********************")
    else:
        c_freq_ind = c_freq_ind + 1
        c_freq = C_ARR[c_freq_ind]
        print("Octave changed to octave: " + str(c_freq_ind))
            
    
#change the wave form on button press
def up_wave():
    global WAVES_ARR
    global wave
    global wave_ind
    global num_waves
    if (wave_ind == num_waves - 1):
        print("                     ")
        print("********************")
        print("No more waves in this direction, try other button")
        print("********************")
    else:
        wave_ind = wave_ind + 1
        wave = WAVES_ARR[wave_ind]
        print("                     ")
        print("********************")
        print("********************")
        print("Wave form has been changed to: " + WAVES_ARR[wave_ind])
        print("********************")
        print("********************")
        
# same thing
def drop_wave():
    global WAVES_ARR
    global wave
    global wave_ind
    global num_waves
    if (wave_ind == 0):
        print("                     ")
        print("********************")
        print("No more waves in this direction, try other button")
        print("********************")
    else:
        wave_ind = wave_ind - 1
        wave = WAVES_ARR[wave_ind]
        print("                     ")
        print("********************")
        print("********************")
        print("Wave form has been changed to: " + WAVES_ARR[wave_ind])
        print("********************")
        print("********************")
        
# Function to automate saw oscillator objects creation to clean up each note's function
def gen_saw(new_osc, prev_osc, pitch):
    new_osc.set_pitch(pitch + 12)
    new_osc.amplitude = prev_osc.amplitude/2
    

# same for square. use pitch + 24 (skip an octave/harmonic) since square waves only contain odd-ordered harmonics
def gen_square(new_osc, prev_osc, pitch):
    new_osc.set_pitch(pitch + 24)
    # note for square amplitude tranformations: new amp is supposed to be previous * 0.66, but 0.33 just sounds better 
    new_osc.amplitude = (prev_osc.amplitude * 0.33) # squares drop amplitude by 1/3 while saws drop by half
    

# params: all of the oscillators used plus the starting pitch which adjusts each new pitch accordingly
def gen_all_saw(osc, osc1, osc2, osc3, osc4, pitch):
    gen_saw(osc1, osc, pitch)
    gen_saw(osc2, osc1, pitch + 12)
    gen_saw(osc3, osc2, pitch + 24)
    gen_saw(osc4, osc3, pitch + 36)
    ## all oscillators have been set, now print values and start
    
    print(osc1_m + str(osc1.frequency))
    print(osc1_amp_m + str(osc1.amplitude))
    #######################################
    print(osc2_m + str(osc2.frequency))
    print(osc2_amp_m + str(osc2.amplitude))
    #######################################
    print(osc3_m + str(osc3.frequency))
    print(osc3_amp_m + str(osc3.amplitude))
    #######################################
    print(osc4_m + str(osc4.frequency))
    print(osc4_amp_m + str(osc4.amplitude))
    osc1.start()
    osc2.start()
    osc3.start()
    osc4.start()
    
def gen_all_square(osc, osc1, osc2, osc3, pitch):
    gen_square(osc1, osc, pitch + 24)
    gen_square(osc2, osc1, pitch + 48)
    gen_square(osc3, osc2, pitch + 72)
    #gen_square(osc4, osc3, pitch + 96)
    
    print(osc1_m + str(osc1.frequency))
    print(osc1_amp_m + str(osc1.amplitude))
    #######################################
    print(osc2_m + str(osc2.frequency))
    print(osc2_amp_m + str(osc2.amplitude))
    #######################################
    print(osc3_m + str(osc3.frequency))
    print(osc3_amp_m + str(osc3.amplitude))
    #######################################
    #print(osc4_m + str(osc4.frequency))
    #print(osc4_amp_m + str(osc4.amplitude))
    osc1.start()
    osc2.start()
    osc3.start()
    #osc4.start()
    
def c():
    print("                     ")
    print("********************")
    print("Note: C")
    # always play a sin wave (thats how other waves are built)
    osc.set_pitch(0)
    osc.start()
    print(osc_m + str(osc.frequency))
    print(osc_amp_m + str(osc.amplitude))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 12)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 24)
    
    print("********************")

def csharp():
    print("                     ")
    print("********************")
    print("Note: C#")
    osc.set_pitch(1)
    osc.start()
    print("***" + osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 13)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 25)
    print("********************")

def d():
    print("                     ")
    print("********************")
    print("Note: D")
    osc.set_pitch(2)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 14)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 26)
    print("********************")

def dsharp():
    print("                     ")
    print("********************")
    print("Note: D#")
    osc.set_pitch(3)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 15)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 27)
    print("********************")

def e():
    print("                     ")
    print("********************")
    print("Note: E")
    osc.set_pitch(4)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 16)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 28)
    print("********************")

def f():
    print("                     ")
    print("********************")
    print("Note: F")
    osc.set_pitch(5)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 17)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 29)
    print("********************")

def fsharp():
    print("                     ")
    print("********************")
    print("Note: F#")
    osc.set_pitch(6)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 18)

        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 30)
    print("********************")

def g():
    print("                     ")
    print("********************")
    print("Note: G")
    osc.set_pitch(7)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 19)

        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3,31)
    print("********************")

def gsharp():
    print("                     ")
    print("********************")
    print("Note: G#")
    osc.set_pitch(8)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 20)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 32)
    print("********************")

def a():
    print("                     ")
    print("********************")
    print("Note: A")
    osc.set_pitch(9)
    osc.start()
    print(osc_m + str(osc.frequency))
    print(osc_amp_m + str(osc.amplitude))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 21)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 33)
    print("********************")

def asharp():
    print("                     ")
    print("********************")
    print("Note: A#")
    osc.set_pitch(10)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 22)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3,34)
    print("********************")

def b():
    print("                     ")
    print("********************")
    print("Note: B")
    osc.set_pitch(11)
    osc.start()
    print(osc_m + str(osc.frequency))
    
    if (WAVES_ARR[wave_ind] == "sawtooth"): # if saw tooth, add harmonics and amp changes
        gen_all_saw(osc, osc1, osc2, osc3, osc4, 23)
        
    if (WAVES_ARR[wave_ind] == "square"): # if square, add appropriate harmonics and amp changes
        gen_all_square(osc,osc1,osc2,osc3, 35)
    print("********************")

def stop():
    osc.stop()
    osc1.stop()
    osc2.stop()
    osc3.stop()
    osc4.stop()

########################################################################
# lets play
btn1.when_pressed = c
btn1.when_released = stop
###########################
btn2.when_pressed = csharp
btn2.when_released = stop
###########################
btn3.when_pressed = d
btn3.when_released = stop
###########################
btn4.when_pressed = dsharp
btn4.when_released = stop
###########################
btn5.when_pressed = e
btn5.when_released = stop
###########################
btn6.when_pressed = f
btn6.when_released = stop
###########################
btn7.when_pressed = fsharp
btn7.when_released = stop
###########################
btn8.when_pressed = g
btn8.when_released = stop
###########################
btn9.when_pressed = gsharp
btn9.when_released = stop
###########################
btn10.when_pressed = a
btn10.when_released = stop
###########################
btn11.when_pressed = asharp
btn11.when_released = stop
###########################
btn12.when_pressed = b
btn12.when_released = stop
###########################
btn_wave_up.when_pressed = up_wave
btn_wave_down.when_pressed = drop_wave
###########################
btn_octave_up.when_pressed = up_octave
btn_octave_down.when_pressed = drop_octave
pause()
########################################################################
