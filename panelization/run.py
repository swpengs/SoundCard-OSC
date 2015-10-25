#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from tsp import *
import time
import sys



# config
basefile = 'input/SoundCard-OSC.top.etch.tap'
#x_count = 1 已無用，改成用argv傳入
#y_count = 1 已無用，改成用argv傳入
F508 = 508 * 1.2
F254 = 254
frame_config = [
    (0.70, F508/7.0*3.0, "solid"),
    (1.40, F508/7.0*3.0, "dashed"),
    ]


# data
x_dist = None
y_dist = None
x_start = None
y_start = None
gcode_header = None
gcode_etch = None
gcode_drill = None
gcode_frame = None
gcode_footer = None


# 分析每一行gcode
class Gline():
    paralist = 'XYZRPF'

    def __init__(self, line):
        self.oriline = line

        # split
        while '  ' in line:
            line = line.replace('  ', ' ')
        line = line.split(' ')

        # code
        self.code = line[0]
        line = line[1:]

        # analyze
        for x in line:
            assert x[0] in Gline.paralist
            value = float(x[1:])
            if '.' not in x[1:]:
                precision = 0
            else:
                precision = len(x[1:]) - x[1:].index('.') - 1
            setattr(self, x[0], value)
            setattr(self, x[0] + "_precision", precision)

        # clean up
        for para in Gline.paralist:
            try:
                getattr(self, para)
            except:
                setattr(self, para, None)

    def __str__(self):
        result = [self.code]
        for para in Gline.paralist:
            if getattr(self, para) is not None:
                F = ("{0:." + str(getattr(self, para + "_precision")) + "f}")
                value = getattr(self, para)
                value = F.format(value)
                result.append(para + value)
        return " ".join(result)







def list_join(L, mark):
    result = []
    for i, x in enumerate(L):
        if i > 0:
            result.append(mark)
        result += x
    return result


def list_split(L, mark):
    result = []
    while 1:
        try:
            i = L.index(mark)
            result.append(L[:i])
            L = L[i+1:]
        except:
            result.append(L)
            break
    return result



def readfile():
    global gcode_header, gcode_frame, gcode_etch, gcode_drill, gcode_footer

    # read file
    f = open(basefile, 'r')
    lines = f.readlines()
    lines = map(lambda x: x.strip(), lines)
    f.close()

    # G00 Z5.0000
    mark = 'G00 Z5.0000'
    temp = list_split(lines, mark)
    assert len(temp) == 3
    gcode_header = temp[0] + [mark]
    lines = temp[1]
    gcode_footer = [mark] + temp[2]

    # G00 Z3.0000
    mark = 'G00 Z3.0000'
    temp = list_split(lines, mark)
    gcode_header += temp[0]
    gcode_frame = [mark] + temp[1]
    gcode_etch = [mark] + list_join(temp[2:-1], mark)
    gcode_drill = [mark] + temp[-1]



def dist_analyze():
    global x_start, y_start, x_dist, y_dist, x_count, y_count

    x_sml = []
    x_big = []
    y_sml = []
    y_big = []
    global gcode_header, gcode_frame, gcode_etch, gcode_drill, gcode_footer
    for line in gcode_frame:
        L = Gline(line)
        if L.code == 'G01':
            if L.X:
                if L.X > 10:
                    x_big.append(L.X)
                else:
                    x_sml.append(L.X)
            if L.Y:
                if L.Y > 10:
                    y_big.append(L.Y)
                else:
                    y_sml.append(L.Y)
    # start
    x_start = sum(x_sml) / len(x_sml)
    y_start = sum(y_sml) / len(y_sml)

    # dist
    x_dist = sum(x_big) / len(x_big)
    y_dist = sum(y_big) / len(y_big)

    # 確保誤差在1條線以內
    delta_e = 0.01
    assert abs(max(x_sml) - x_start) < delta_e
    assert abs(max(y_sml) - y_start) < delta_e
    assert abs(max(x_big) - x_dist) < delta_e
    assert abs(max(y_big) - y_dist) < delta_e
    assert abs(min(x_sml) - x_start) < delta_e
    assert abs(min(y_sml) - y_start) < delta_e
    assert abs(min(x_big) - x_dist) < delta_e
    assert abs(min(y_big) - y_dist) < delta_e

    x_dist = x_dist - x_start
    y_dist = y_dist - y_start

    print "拼版數量        = %d x %d" % (x_count, y_count)
    print "起始點          = %.4f x %.4f mm" % (x_start, y_start)
    print "間距            = %.4f x %.4f mm" % (x_dist, y_dist)



# ecth,drill multiply
def multiply(gcode):
    global x_count, y_count
    result = []
    for x_i in range(x_count):
        for y_i in range(y_count):
            for g in gcode:
                L = Gline(g)
                if L.X or L.Y:
                    L.X = L.X + x_i * x_dist
                    L.Y = L.Y + y_i * y_dist
                result.append(str(L))
    return result


# drill optimize
def drill_optimize(gcode):
    global x_count, y_count, cities, F508

    # prepare for TSP algorithm
    for g in gcode:
        L = Gline(g)
        if L.X or L.Y:
            add_city(L.X, L.Y)

    # TSP algorithm
    dt = time.time()
    tourlist = altered_greedy_tsp(frozenset(cities))
    print "TSP algorithm run %.2f seconds / %d cities" % (time.time() - dt, len(cities))

    # result
    result = []
    result.append("G00 Z2.0000")
    for i, tour in enumerate(tourlist):
        temp = "G82 X%.4f Y%.4f" % (tour.real, tour.imag)
        if i == 0:
            temp += " Z-1.6000 R2.0000 P0.100000 F%d" % int(F508)
        result.append(temp)

    return result






def writefile(path):
    f = open(path, 'w')
    gcode = []
    gcode.append('(----- header -----)')
    gcode += gcode_header
    gcode.append('(----- etch -----)')
    gcode += gcode_etch
    gcode.append('(----- drill -----)')
    gcode += gcode_drill
    gcode.append('(----- frame -----)')
    gcode += gcode_frame
    gcode.append('(----- footer -----)')
    gcode += gcode_footer
    f.write("\n".join(gcode))
    f.close()

# 包含頭尾，不管方向的range
def myrange(start, end):
    if end >= start:
        return range(start, end, 1) + [end]
    else:
        return range(start, end, -1) + [end]



class Grid():
    def __init__(self, x_i, y_i):
        self.x_i = x_i
        self.y_i = y_i

    @ property
    def x_mm(self):
        global x_start, x_dist
        return x_start + self.x_i * x_dist

    @ property
    def y_mm(self):
        global y_start, y_dist
        return y_start + self.y_i * y_dist

    def gcode(self, feedrate):
        return "G01 X%.4f Y%.4f F%d" % (self.x_mm, self.y_mm, feedrate)

    def __repr__(self):
        return "Grid(%d, %d)" % (self.x_i, self.y_i)

    # 虛線的前點跟後點
    def dashed(self, point_end):
        global x_dist, y_dist

        point_start = self

        # check
        x_dir = (point_start.y_i == point_end.y_i and abs(point_start.x_i - point_end.x_i) == 1)
        y_dir = (point_start.x_i == point_end.x_i and abs(point_start.y_i - point_end.y_i) == 1)
        assert x_dir or y_dir

        # 中點
        x_middle = (point_start.x_i + point_end.x_i) / 2.0
        y_middle = (point_start.y_i + point_end.y_i) / 2.0

        # 往前1個mm 向量
        x_mm_vector = float(point_end.x_i - point_start.x_i) / x_dist
        y_mm_vector = float(point_end.y_i - point_start.y_i) / y_dist

        # 虛線的長度 mm
        dashed_length = 6.0

        # dashed前方的點
        dashed_front = Grid(x_middle - dashed_length / 2.0 * x_mm_vector,
                            y_middle - dashed_length / 2.0 * y_mm_vector)
        dashed_rear = Grid(x_middle + dashed_length / 2.0 * x_mm_vector,
                           y_middle + dashed_length / 2.0 * y_mm_vector)

        return (dashed_front, dashed_rear)


    # 中間經過的點
    def route(self, point_end):
        point_start = self
        if point_start.x_i == point_end.x_i:
            return [Grid(point_start.x_i, y) for y in myrange(point_start.y_i, point_end.y_i)]
        else:
            return [Grid(x, point_start.y_i) for x in myrange(point_start.x_i, point_end.x_i)]


    # 產生蛇形的路線，dir=0先走X，dir=1先走Y
    def snake(self, direction):
        assert direction in [0,1]
        global x_count, y_count
        (x_start, y_start) = (self.x_i, self.y_i)

        result = []

        # 先走x方向
        if direction == 0:
            row1 = Grid(x_start, y_start).route(Grid(x_start, y_count - y_start))
            row2 = Grid(x_count - x_start, y_start).route(Grid(x_count - x_start, y_count - y_start))

        # 先走y方向
        elif direction == 1:
            row1 = Grid(x_start, y_start).route(Grid(x_count - x_start, y_start))
            row2 = Grid(x_start, y_count - y_start).route(Grid(x_count - x_start, y_count - y_start))

        # row合併
        row = zip(row1, row2)
        row = list(reduce(lambda x, y : x + y, row))

        # 把 0 1 2 3 | 4 5 6 7 | 8 9 10 11 | 12 對調
        #        ^^^       ^^^       ^^^^^
        for i in range(2, len(row), 4):
            row[i], row[i+1] = row[i+1], row[i]

        return row, row[-1]




# Step 4：劃蛋糕
def frame_gen():
    global frame_config, x_start, y_start, x_dist, y_dist, F254, F508

    result = []
    result.append('G00 Z3.0000')
    result.append('G00 X%.4f Y%.4f' % (x_start, y_start))
    last_point = Grid(0, 0)

    for Z, feedrate, linestyle in frame_config:
        result.append('G01 Z-%.4f F%d' % (Z, int(F254)))
        print "Z = %.3f" % Z

        # 先走x方向，再走y方向
        for direction in [0, 1]:
            pathlist, last_point = last_point.snake(direction)

            for point_i in range(len(pathlist) - 1):
                # 虛線
                if linestyle.lower().startswith('d'):
                    segment_list = pathlist[point_i].route(pathlist[point_i + 1])
                    for segment_i in range(len(segment_list) - 1):
                        #result.append('(---up---)')
                        dashed_front, dashed_rear = segment_list[segment_i].dashed(segment_list[segment_i + 1])
                        result.append(dashed_front.gcode(feedrate = feedrate))
                        result.append("G01 Z0.000 F%d" % int(F508))
                        result.append(dashed_rear.gcode(feedrate = feedrate))
                        result.append("G01 Z-%.4f F%d" % (Z, int(F254)))

                # 終點，不管虛線實線都要
                #result.append('(---single---)')
                result.append(pathlist[point_i + 1].gcode(feedrate = feedrate))

    return result




# 取代feed rate
def replace_feedrate(gcode):
    global F508, F254

    result = []
    for line in gcode:
        g = Gline(line)
        if g.F is not None:
            if g.F == 508:
                g.F = int(F508)
            if g.F == 254:
                g.F = int(F254)
        result.append(str(g))

    return result


def run(para1, para2):
    global x_count, y_count
    x_count = para1
    y_count = para2

    print '(0) Readfile'
    readfile()
    dist_analyze()

    global gcode_etch, gcode_drill, gcode_frame

    # change feedrate
    gcode_etch = replace_feedrate(gcode_etch)
    gcode_drill = replace_feedrate(gcode_drill)

    # etch, drill panlization
    print '\n(1) Etch'
    gcode_etch = multiply(gcode_etch)
    print '\n(2) Drill'
    gcode_drill = multiply(gcode_drill)

    # drill optimize
    gcode_drill = drill_optimize(gcode_drill)

    # frame
    print '\n(3) Frame'
    gcode_frame = frame_gen()

    # output
    print '\n(X) Output'
    filename = 'output/%s_%dx%d.nc' % (time.strftime("%Y%m%d_%H%M%S"), x_count, y_count)
    writefile(filename)
    print "Write to file: %s" % filename



if __name__ == '__main__':
    run(int(sys.argv[1]), int(sys.argv[2]))
