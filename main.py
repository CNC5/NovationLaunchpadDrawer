from math import sqrt
import numpy as np
import mido
from time import sleep

class LaunchPad:
    def __init__(self,midi_dev = 'Launchpad Mini MIDI 1', midi_ch = '0', midi_height = 8, midi_width = 8, debug = False):
        # Zeros, Red 25-100%, Green 25-100%, 
        self.debug = debug
        self.colors = { 'Z': 0,
                        'R25':  1,  'R50':  2,  'R100': 3,      'R':    3,
                        'G25':  16, 'G50':  32, 'G100': 48,     'G':    48,
                        '1L50': 49,                             '1L':   49,
                        '2L25': 33, '2l50': 50,                 '2L':   50,
                        '3l25': 17, '3L50': 34, '3L100':51,     '3L':   51,
                                    '4L50': 18, '4L100':35,     '4L':   35,
                                                '5L100':19,     '5L':   19}
        self.top_colors = ['R','5L','4L','3L','2L','1L','G']
        self.midi_dev = midi_dev
        self.midi_ch = midi_ch
        self.midi_height = midi_height
        self.midi_width = midi_width
        self.color_threshold = 128
        self.states = np.zeros([self.midi_width, self.midi_height])
        self.port = mido.open_output(self.midi_dev)
        self.inport = mido.open_input(self.midi_dev)
        self.update()

    def length_to_xy(self, length):
        x = min(7, length%16)
        y = length//16
        return [x, y]

    def is_inside(self, x, y):
        if x in range(self.midi_width) and y in range(self.midi_height):
            return 1
        else:
            return 0

    def pixel(self, x: int, y: int, color):
        distance = x + y*16
        if color == 'N':
            return
        if type(color) == str:
            color = self.colors[color.upper()]
        self.port.send(mido.Message('note_on', note=int(distance), velocity=int(color)%128))
        self.states[y][x] = color

    def update(self):
        if self.debug:
            updates = np.zeros([self.midi_height, self.midi_width])
        for y in range(self.midi_height):
            for x in range(self.midi_width):
                self.pixel(x, y, self.states[y][x]) ###
                if self.debug:
                    updates[y][x] = self.states[y][x]
        if self.debug:
            print(updates)

    def invert(self, pixel):
        if self.states[pixel[1]][pixel[0]] != self.colors['G']:
            self.states[pixel[1]][pixel[0]] = self.colors['G']
        else:
            self.states[pixel[1]][pixel[0]] = self.colors['R']

    def reset(self):
        self.states = np.zeros([self.midi_width, self.midi_height])
        self.update()

    def patch(self, feed, color):
        for link in feed:
            self.states[link[0]][link[1]] = color

    def roll(self, cycles=127):
        for i in range(cycles):
            for y in range(self.midi_height):
                for x in range(self.midi_width):
                    self.pixel(x, y, self.states[y][x]+1)
                    sleep(0.01)
                    self.states[y][x] += 1

    def flush(self, color):
        for y in range(self.midi_height):
            for x in range(self.midi_width):
                self.pixel(x, y, self.states[y][x]+1)
                sleep(0.01)
        for y in range(self.midi_height):
            for x in range(self.midi_width):
                self.pixel(x, y, 0)
                sleep(0.01)

    def flood(self, color: int):
        if color == 'N':
            return
        if type(color) == str:
            color = self.colors[color.upper()]
        self.states.fill(color)
        self.update()

    def square(self, center: list, a: int, color):
        if self.debug:
            print(f'square at {center}')
        if color == 'N':
            return
        if type(color) == str:
            color = self.colors[color.upper()]
        if a == 0:
            self.pixel(center[0], center[1], color)

        for x in range(center[0]-a, center[0]+a+1):
            y0 = center[1]-a
            y1 = center[1]+a
            x = x
            if self.is_inside(x, y0):
                self.states[y0][x] = color
            if self.is_inside(x, y1):
                self.states[y1][x] = color

        for y in range(center[1]-a, center[1]+a+1):
            x0 = center[0]-a
            x1 = center[0]+a
            y = y
            if self.is_inside(x0, y):
                self.states[y][x0] = color
            if self.is_inside(x1, y):
                self.states[y][x1] = color

    def negative_square(self, center: list, a: int):
        if self.debug:
            print(f'square at {center}')
        if a == 0:
            self.invert(center)

        updates = []
        for x in range(center[0]-a, center[0]+a+1):
            y0 = center[1]-a
            y1 = center[1]+a
            x = x
            if self.is_inside(x, y0):
                self.invert([x,y0])
                updates.append([x,y0])
            if self.is_inside(x, y1):
                self.invert([x,y1])
                updates.append([x,y0])

        for y in range(center[1]-a, center[1]+a+1):
            x0 = center[0]-a
            x1 = center[0]+a
            y = y
            if self.is_inside(x0, y) and not [x0, y] in updates:
                self.invert([x0,y])
            if self.is_inside(x1, y) and not [x1, y] in updates:
                self.invert([x1,y])

    def circle(self, center, radius, color):
        arc = [[ x, round(sqrt((radius-x)*(radius+x)))] for x in range(radius+1) ]
        print(arc)
        self.patch(arc, color)
        self.update()

    def splash_square(self, center, delay=0.01, repeats = 1,
                        sequence = ['Z','Z','Z','Z','Z','Z','Z','Z',
                                    'R','N','5L','N','4L','N','3L','N','2L','N','1L','N','G']):
        unsplashed = np.copy(self.states)
        for n in range(len(sequence)*repeats):
            for i in range(n+1):
                self.square(center, i, sequence[i])
            self.update()
            sleep(delay)
            tmp = sequence.pop(-1)
            sequence.insert(0, tmp)
        self.states = np.copy(unsplashed)
        del unsplashed
        self.update()

    def negative_splash_square(self, center, delay=0.01, repeats = 1,
                        sequence = ['Z','Z','Z','Z','Z','Z','Z','Z',
                                    'R','N','5L','N','4L','N','3L','N','2L','N','1L','N','G']):
        unsplashed = np.copy(self.states)
        for n in range(len(sequence)*repeats):
            for i in range(n+1):
                self.negative_square(center, i)
            self.update()
            sleep(delay)
            tmp = sequence.pop(-1)
            sequence.insert(0, tmp)
        self.states = np.copy(unsplashed)
        del unsplashed
        self.update()

    def process(self):
        color = 3
        for click in self.inport:
            print(click)
            if click.type == 'control_change' and click.value != 0:
                if click.control == 111:
                    self.flush(self.colors['R'])
                    continue
                color = self.colors[self.top_colors[click.control%len(self.top_colors)]]
            elif click.type == 'note_on' and click.velocity != 0:
                self.negative_splash_square(self.length_to_xy(click.note), 0.03, sequence=['N','N','N','R'])
                if self.states[self.length_to_xy(click.note)[1], self.length_to_xy(click.note)[0]] == color:
                    self.pixel(self.length_to_xy(click.note)[0], self.length_to_xy(click.note)[1], 0)
                else:
                    self.pixel(self.length_to_xy(click.note)[0], self.length_to_xy(click.note)[1], color)

if __name__=='__main__':
    lp = LaunchPad(debug = False)
    lp.process()
