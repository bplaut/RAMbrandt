# util.py - helper functions for art.py
# Author: Ben Plaut
# Contains random helper functions for art.py and objects.py
# Required external modules: PIL
# Required python files: None

from tkinter import *
from PIL import Image, ImageTk
import random
import copy
import math
import os

# function taken from 112 course notes at http://www.kosbie.net/cmu/fall-12/15-112/handouts/notes-recursion/floodFill-pixel-based.py
def callWithLargeStack(f,*args):
    import sys
    import threading
    threading.stack_size(2**27)  # 64MB stack
    sys.setrecursionlimit(2**27) # will hit 64MB stack limit first
    # need new thread to get the redefined stack size
    def wrappedFn(resultWrapper): resultWrapper[0] = f(*args)
    resultWrapper = [None]
    #thread = threading.Thread(target=f, args=args)
    thread = threading.Thread(target=wrappedFn, args=[resultWrapper])
    thread.start()
    thread.join()
    return resultWrapper[0]

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

def get_input_paths(image_short_dir, indices_to_keep):
    image_dir = os.path.join(os.getcwd(), image_short_dir)
    short_paths = os.listdir(image_dir)
    image_paths = [os.path.join(image_dir, path) for path in short_paths]

    image_paths = [image_paths[i] for i in range(len(image_paths))
                   if i in indices_to_keep]
    return image_paths

def sans_brackets(L):
    return str(L)[1:len(L) - 1]

def make_output_name(unformatted_func, x_scale, y_scale, train_region_size,
                     gen_region_size, train_palette_size, train_objects_size,
                     palette_short_dir,
                     pal_indices, obj_short_dir,obj_indices,i):
    j = palette_short_dir.find("/") + 1 # skip the /
    palette_short_dir = palette_short_dir[j:]
    j = obj_short_dir.find("/") + 1
    obj_short_dir = obj_short_dir[j:]
    return ('output/%s_x%d_y%d_trp%d_tro%d_ge%d_si%d_p-%s%s_o-%s%s_%d.jpg' %
            (get_func_string(unformatted_func), x_scale, y_scale,
             train_region_size, gen_region_size, train_palette_size,
             train_objects_size, palette_short_dir,
             sans_brackets(pal_indices), obj_short_dir,
             sans_brackets(obj_indices), i))

def get_all_pixels(width, height):
    result = []
    for y in range(height):
        result += [(x,y) for x in range(width)]
    return set(result)

def adjust_object(obj, curr_width, curr_height, new_left, new_top, new_width,
                  new_height):
    # obj is a pixel set representing the pixels in the object
    white_val = 255

    obj_image = binary_image_from_set(obj, curr_width, curr_height)
    resized_obj_image = obj_image.resize((new_width, new_height))
    resized_set = set_from_binary_image(resized_obj_image, new_width,
                                        new_height)
    translated_obj = [(x + new_left, y + new_top) for (x,y) in resized_set]
    return translated_obj

def randomly_modify_object(obj, curr_width, curr_height, result_width,
                           result_height):
    if (float(curr_width)/result_width) > (float(curr_height)/result_height):
        # width is limiting dimension
        max_factor = float(result_width)/curr_width
    else: # it's height
        max_factor = float(result_height)/curr_height
    min_factor_we_want = max_factor
    min_factor = min(min_factor_we_want, max_factor) # can't be bigger than max
    rand_float = random.random()
    # 0 <= rand_float < 1, but we want min_factor <= rand_float < max_factor
    rand_float = 1
    resize_factor = rand_float * (max_factor - min_factor) + min_factor
    
    new_width = int(round(resize_factor * curr_width))
    new_height = int(round(resize_factor * curr_height))

    left_range = (0, result_width - new_width)
    top_range = (0, result_height - new_height)
    new_left = random.randint(*left_range)
    new_top = random.randint(*top_range)
    
    adjusted_obj = adjust_object(obj, curr_width, curr_height, new_left,
                                 new_top, new_width, new_height)
    return adjusted_obj


    

    
