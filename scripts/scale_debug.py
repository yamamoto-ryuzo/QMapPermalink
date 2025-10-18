# Simple script to compare bbox calculation methods
import math

def bbox_old(center_x, center_y, scale, width=800, height=600):
    # old: scale as meters per pixel
    half_width_meters = (width / 2) * scale
    half_height_meters = (height / 2) * scale
    minx = center_x - half_width_meters
    maxx = center_x + half_width_meters
    miny = center_y - half_height_meters
    maxy = center_y + half_height_meters
    return (minx, miny, maxx, maxy)

def bbox_new(center_x, center_y, scale, width=800, height=600, dpi=96.0):
    # new: scale is scale denominator (1:scale)
    meters_per_inch = 0.0254
    pixels_per_meter = dpi / meters_per_inch
    map_width_m = (width / pixels_per_meter) * scale
    map_height_m = (height / pixels_per_meter) * scale
    half_width = map_width_m / 2.0
    half_height = map_height_m / 2.0
    minx = center_x - half_width
    maxx = center_x + half_width
    miny = center_y - half_height
    maxy = center_y + half_height
    return (minx, miny, maxx, maxy)

if __name__ == '__main__':
    cx = -21611.739862
    cy = -9666.733525
    scale = 134.1
    w = 800
    h = 600
    old = bbox_old(cx, cy, scale, w, h)
    new = bbox_new(cx, cy, scale, w, h)
    def area(b):
        return abs((b[2]-b[0])*(b[3]-b[1]))
    print('Center:', cx, cy)
    print('Scale:', scale)
    print('\nOld bbox (scale as m/px):')
    print(old)
    print('Area (m^2):', area(old))
    print('\nNew bbox (scale as denom 1:scale):')
    print(new)
    print('Area (m^2):', area(new))
    print('\nRatio old/new (area):', area(old)/area(new))
