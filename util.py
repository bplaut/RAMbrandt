# util.py - helper functions for art.py
# Author: Ben Plaut
# Contains helper functions for main.py
# Required external modules: PIL
# Required python files: None

from tkinter import *
from PIL import Image, ImageTk
import random
import copy
import math
import os
import sys
import threading

def call_with_large_stack(f,*args):
    threading.stack_size(2**27)  # 64MB stack
    sys.setrecursionlimit(2**27) # will hit 64MB stack limit first
    # need new thread to get the redefined stack size
    def wrapped_fn(result_wrapper): result_wrapper[0] = f(*args)
    result_wrapper = [None]
    thread = threading.Thread(target=wrapped_fn, args=[result_wrapper])
    thread.start()
    thread.join()
    return result_wrapper[0]

def weighted_random_index(L, wts):
    rand_float = random.random() # between 0.0 and 1.0
    # blow it up to correct scale
    rand_float *= sum(wts)
    wt_sum = 0
    for i in range(len(wts)):
        wt_sum += wts[i]
        if rand_float < wt_sum:
            return i
 
def weighted_random_shuffle(L, wts):
    result = [None] * len(L)
    L = copy.copy(L)
    wts = copy.copy(wts)
    for i in range(len(result)):
        rand_index = weighted_random_index(L, wts)
        result[i] = L.pop(rand_index)
        wts.pop(rand_index)
    return result
 
def append_to_dict(d, key, val):
    if key in d:
        d[key].append(val)
    else:
        d[key] = [val]
 
def closest_val_in_dict(d, key):
    (lower, upper) = (key, key)
    while (lower not in d) and (upper not in d):
        lower -= 1
        upper += 1
    if lower in d:
        return lower
    else:
        return upper
 
def upper_left_region(x, y, n):
    result = []
    for i in range(0, n + 1): # we want to include (x - n, y) so n + 1
        for j in range(0, n + 1):
            if 1 <= i + j <= n:
                result.append((x - i, y - j))
    return result
 
def lower_right_region(x, y, n):
    result = []
    for i in range(0, n + 1): # we want to include (x - n, y) so n + 1
        for j in range(0, n + 1):
            if 1 <= i + j <= n:
                result.append((x + i, y + j))
    return result
 
def surrounding_region(x, y, n):
    result = []
    for i in range(-n, n + 1): # we want to include (x - n, y) so n + 1
        for j in range(-n, n + 1):
            if 1 <= abs(i) + abs(j) <= n:
                result.append((x - i, y - j))
    return result


def get_func_string(func):
    s = str(func)
    name_index = s.find("function ") + len("function ")
    name_length = 6
    return s[name_index:name_index + name_length]

def resize_intelligently(image, train_size):
    # want to resize so that dimension ratio is maintained, but the
    # number of pixels is now self.train_size
    (curr_width, curr_height) = image.size
    resize_factor = (float(train_size)/(curr_height*curr_width))**.5
    new_width = int(round(curr_width * resize_factor))
    new_height = int(round(curr_height * resize_factor))
    image = image.resize((new_width, new_height))
    return image

def pixel_argmax(pixels, pixels_to_exclude, width, height):
    max_x = None
    max_y = None
    max_val = None
    for x in range(width):
        for y in range(height):
            if pixels[x,y] > max_val and (x,y) not in pixels_to_exclude:
                max_val = pixels[x,y]
                (max_x, max_y) = (x,y)
    return (max_x, max_y)

def show_im(image, width, height):
    root = Tk()
    canvas = Canvas(root, width = width, height = height)
    canvas.pack()
    tk_gray = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor = NW, image = tk_gray)
    root.mainloop()

def set_from_binary_image(image, width, height):
    white_val = 255
    image_pixels = image.load()
    result = set()
    for y in range(height): # row major order
        for x in range(width):
            if image_pixels[x,y] == 255:
                result.add((x,y))
    return result
                

def binary_image_from_set(white_pixels, width, height):
    result = Image.new('L', (width, height))
    result_pixels = result.load()
    white_val = 255
    for (x,y) in white_pixels:
        result_pixels[x,y] = white_val
    return result

def get_input_paths(image_short_dir, filenames):
    image_dir = os.path.join(os.getcwd(), image_short_dir)
    found_files = os.listdir(image_dir)
    image_paths = []
    for filename in filenames:
        if filename in found_files:
            image_paths.append(os.path.join(image_dir, filename))
        else:
            print("Could not find file \'%s\', skipping" % filename)
    return image_paths

def sans_brackets(L):
    return str(L)[1:len(L) - 1]

def make_output_name(shape_func, train_region_size, gen_region_size, 
                     train_palette_size, palette_files):
    return ('output/%s_train_size=%d_gen_region_size=%d_train_pal_size=%d_palette_files=%s.jpg' %
            (get_func_string(shape_func), train_region_size, gen_region_size, 
             train_palette_size, sans_brackets(palette_files)))

def get_all_pixels(width, height):
    result = []
    for y in range(height):
        result += [(x,y) for x in range(width)]
    return set(result)

    

    
