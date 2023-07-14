# shape_funcs.py - helper functions for main.py
# Author: Ben Plaut
# Contains different functions used for the weighting the different directions
# when choosing which neighbor to floodfill next (in main.py). For example,
# if you always weight going right really high, you'll get horizontal
# "brushstrokes". You can also make other shapes, like cirlces, etc.
# Required external modules: None
# Required python files: None

import math
import matplotlib
matplotlib.use("TkAgg") # without this, matplotlib and Tk conflict
import matplotlib.pyplot as plt

def uniform(x,y,width,height, shape_strength_x, shape_strength_y):
    return format_result(1,1)

# Note for all of the trigonometric functions (which is most of them):
# The inputs x and y are the values on the canvas (origin in upper left corner).
# I convert the x and y values so that (0,0) is at the center of the canvas
# and so increasing y goes upward (instead of downward, as it does on the canvas)
# Then I convert it back in format result
def theta(x,y,width,height):
    # adjust coordinates so that (0,0) is the center of the canvas
    adjusted_x = x - width/2
    adjusted_y = height/2 - y
    if x == width/2: # must special case this
        if y < height/2:
            return math.pi/2
        else:
            return -math.pi/2
    else: 
        arctan = math.atan(float(adjusted_y)/adjusted_x)
        # if the angle should be in quadrant 2 or 3, need to return
        # pi + atan(y/x). This occurs if x <0
        if adjusted_x < 0:
            return math.pi + arctan
        else:
            return arctan

def format_result(x_comp, y_comp, num_wts = 4, default_wt = 1):
    result = [default_wt] * num_wts
    # order is: increase x, increase y, decrease y, decrease x
    if x_comp >= 0: # we want to go right
        result[0] = x_comp
    else: # negative x means we want to go left
        result[3] = abs(x_comp)
    if y_comp >= 0:
        # we want to go up on the screen, which means DECREASING Y
        result[2] = y_comp
    else:
        result[1] = abs(y_comp)
    return result

def visualize_vector_field(shape_func, w, h, shape_strength_x, shape_strength_y):
    # for now, ignore sign
    vector_field_x = [[None] * w for _ in range(h)]
    vector_field_y = [[None] * w for _ in range(h)]   
    for x in range(w):
        for y in range(h):
            wts = shape_func(x, y, w, h, shape_strength_x, shape_strength_y)
            # order of wts is: increase x, increase y, decrease y, decrease x            
            vector_field_x[y][x] = max(wts[0], wts[3])
            vector_field_y[y][x] = max(wts[1], wts[2])
    fig, (ax1, ax2) = plt.subplots(1,2)
    fig.suptitle('Vector field for chosen shape')
    ax1.imshow(vector_field_x, cmap='gray')
    ax1.set_title('x component')
    ax2.imshow(vector_field_y, cmap='gray')   
    ax2.set_title('y component')          
    plt.show()

def normalize(x_comp, y_comp, shape_strength_x, shape_strength_y):
    if x_comp == y_comp == 0: (x_comp, y_comp) = (1, 1)
    magnitude = math.sqrt(x_comp**2 + y_comp**2)
    x_comp /= magnitude
    y_comp /= magnitude
    x_comp *= shape_strength_x
    y_comp *= shape_strength_y
    return (x_comp, y_comp)

def cosine(x, y, w, h, shape_strength_x, shape_strength_y):
    period = w / 2
    adjusted_x = 2 * math.pi * x / period
    y_comp = -math.sin(adjusted_x) * shape_strength_y
    x_comp = (1 - abs(math.sin(adjusted_x))) * shape_strength_y
    return format_result(x_comp, y_comp)

def parabola(x, y, w, h, shape_strength_x, shape_strength_y):
    x = x - w/2 # adjust so that x = 0 is the center. y doesn't matter
    x_comp = shape_strength_x
    y_comp = shape_strength_y * 2*x
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    return format_result(x_comp, y_comp)
        
def circle(x, y, w, h, shape_strength_x, shape_strength_y):
    x_component = shape_strength_x * (-math.sin(theta(x,y,w,h)))
    y_component = shape_strength_y * math.cos(theta(x,y,w,h))
    return format_result(x_component, y_component)

def double_circle(x,y,w,h, shape_strength_x, shape_strength_y):
    # left half and right half are separate circles
    if x > w/2:
        x = x - w/2
    # two circles, each with width w/2
    return circle(x, y, w/2, h, shape_strength_x, shape_strength_y)

def superimposed_circles(x,y,w,h, shape_strength_x, shape_strength_y):
    wts1 = circle(x,y,w,h,shape_strength_x,shape_strength_y)
    wts2 = four_circles(x,y,w,h,shape_strength_x,shape_strength_y)
    return [wts1[i] + wts2[i] for i in xrange(len(wts1))]

def four_circles(x,y,w,h, shape_strength_x, shape_strength_y):
    # figure out which quadrant it's in
    if x > w/2 and y > w/2:
        x = x - w/2
        y = y - h/2
    elif x < w/2 and y > h/2:
        y = y - h/2
    elif x > w/2 and y < h/2:
        x = x - w/2
    return circle(x,y, w/2, h/2, shape_strength_x, shape_strength_y)

# heart doesn't actually work :(
def heart(x, y, w, h, shape_strength_x, shape_strength_y):
    real_theta = theta(x,y,w,h)
    adjusted_x, adjusted_y = x,y
    actual_theta = theta(adjusted_x, adjusted_y, w,h)
    adjusted_theta = math.pi/2 - actual_theta

    x_comp = 48*math.cos(adjusted_theta)*((math.sin(adjusted_theta))**2)
    y_comp = (-13*math.cos(adjusted_theta) + 10*math.cos(2*adjusted_theta)
              + 6*math.cos(3*adjusted_theta) +4*math.cos(4*adjusted_theta))      
    # now normalize
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    if (x > w/2 and y > h/2) or (x < w/2 and y < h/2): y_comp *= -1
    return format_result(x_comp, y_comp)

def horiz(x,y,h,shape_strength_x, shape_strength_y):
    return [shape_strength_x, 1, 1, 1]

def split_over_width(x,y, width, height, shape_strength_x, shape_strength_y):
    return ([1, (x-width/2)/100 + 1, 1, 1] if x > width/2
            else [(width/2-x)/100 + 1 + y, 1, 1, 1])

# not very good
def fermat_spiral(x,y,w,h, shape_strength_x, shape_strength_y):
    t = theta(x,y,w,h)
    x_comp = math.cos(t) - 2*t*math.sin(t)
    y_comp = 2*t*math.cos(t) + math.sin(t)
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    return format_result(x_comp, y_comp)

# not very good
def hyperbola(x,y,w,h, shape_strength_x, shape_strength_y):
    adjusted_x = x - w/2
    adjusted_y = h/2 - y
    if adjusted_x == adjusted_y == 0:
        return [1,1,1,1] # avoid division by 0 in normalization
    x_comp = adjusted_y
    y_comp = adjusted_x
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    return format_result(x_comp, y_comp)

# not very good
def figure_8(x,y,w,h, shape_strength_x, shape_strength_y):
    adjusted_x = x - w/2
    adjusted_y = h/2 - y
    if adjusted_y == 0: return [1,1,1,1]
    x_comp = 1
    y_comp = (adjusted_x**2 - 2*(adjusted_x**3))/adjusted_y
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    return format_result(x_comp, y_comp)

def weird_circle(x, y, w, h, shape_strength_x, shape_strength_y):
    curr_theta = theta(x,y,w,h)
    x_comp = -math.sin(curr_theta) + .7
    y_comp =  math.cos(curr_theta)
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    return format_result(x_comp, y_comp)

def trying_random_things(x,y,w,h, shape_strength_x, shape_strength_y):
    x_comp = 100
    y_comp = 1
    (x_comp, y_comp) = normalize(x_comp, y_comp, shape_strength_x, shape_strength_y)
    return format_result(x_comp, y_comp)
    
