from math import *

def rotate(p, t):
    return (p[0] * cos(t) - p[1] * sin(t), p[0] * sin(t) + p[1] * cos(t))

def SVG_move(p, t):
    pp = rotate(p, t)
    return 'M ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_line(p, t):
    pp = rotate(p, t)
    return 'L ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_circle(p, r, sweep, t):
    pp = rotate(p, t)
    return 'A ' + str(r) + ',' + str(r) + ' 0 0,' + str(sweep) + ' ' + str(pp[0]) + ',' + str(pp[1]) + '\n'

def SVG_curve(p, c1, c2, t):
    pp = rotate(p, t)
    c1p = rotate(c1, t)
    c2p = rotate(c2, t)
    return 'C ' + str(pp[0]) + ',' + str(pp[1]) + ' ' + str(c1p[0]) + ',' + str(c1p[1]) + ' ' + str(c2p[0]) + ',' + str(c2p[1]) + '\n'

def SVG_curve2(p1, c11, c12, p2, c21, c22, t):
    p1p = rotate(p1, t)
    c11p = rotate(c11, t)
    c12p = rotate(c12, t)
    p2p = rotate(p2, t)
    c21p = rotate(c21, t)
    c22p = rotate(c22, t)
    return 'C ' + str(p1p[0]) + ',' + str(p1p[1]) + ' ' + str(c11p[0]) + ',' + str(c11p[1]) + ' ' + str(c12p[0]) + ',' + str(c12p[1]) + ' ' + str(p2p[0]) + ',' + str(p2p[1]) + ' ' + str(c21p[0]) + ',' + str(c21p[1]) + ' ' + str(c22p[0]) + ',' + str(c22p[1]) + '\n'

def SVG_close():
    return 'Z\n'