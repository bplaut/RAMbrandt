# main.py - generates artistic pictures
# Author: Ben Plaut
# Main file. Contains main model for training and generation, as well as all
# of the parameters, which are set in the set_parameters function.
# Required external modules: PIL
# Requires python files: util.py

from tkinter import *
from PIL import Image, ImageTk
import os
import sys
import random
import util # file with helper functions
import shape_funcs # for weighting directions in floodfill

class Model(object):
    def __init__(self, *params):
        (train_region_size, train_region_func, train_palette_size, 
         gen_region_size, gen_pixel_limit, shape_strength_x, shape_strength_y, 
         shape_func, palette_paths, output_dims, _, _) = params

        (self.width, self.height) = output_dims
        self.palette_paths = palette_paths
        self.train_palette_size = train_palette_size
        self.floodfill_wts_func = lambda x,y: shape_func(x,y, self.width, self.height, shape_strength_x, shape_strength_y)
        
        self.gen_region_size = gen_region_size
        self.train_region_func = train_region_func
        # can't be more than width*height
        self.gen_pixel_limit = min(gen_pixel_limit,
                                   self.width * self.height)
        self.default_region_func = util.surrounding_region

    def train_from_pixel(self, pixels, x, y, train_width, train_height):
        (r, g, b) = pixels[x,y]
        adj_points = self.train_region_func(x, y)
        for (adj_x, adj_y) in adj_points:
            if (0 <= adj_x <= train_width - 1
                and 0 <= adj_y <= train_height - 1):
                (adj_r, adj_g, adj_b) = pixels[adj_x, adj_y]
                util.append_to_dict(self.red_model, r, adj_r)
                util.append_to_dict(self.green_model, g, adj_g)
                util.append_to_dict(self.blue_model, b, adj_b)
    
    def train_palette(self):
        self.red_model = dict()
        self.green_model = dict()
        self.blue_model = dict()

        for image_path in self.palette_paths: # local path, not full path
            image = Image.open(image_path)
            # want to resize so that dimension ratio is maintained, but the
            # number of pixels is now self.train_palette_size
            image = util.resize_intelligently(image, self.train_palette_size)
            (new_width, new_height) = image.size
            pixels = image.load()
            # First, do the markov-chain-style conditioning
            for x in range(new_width):
                for y in range(new_height):
                    self.train_from_pixel(pixels, x, y, new_width, new_height)
                                          
    def generate_from_one_neighbor(self, prev_x, prev_y):
        (prev_r, prev_g, prev_b) = self.result_pixels[prev_x, prev_y]
        prev_r = util.closest_val_in_dict(self.red_model, prev_r)
        prev_g = util.closest_val_in_dict(self.green_model, prev_g)
        prev_b = util.closest_val_in_dict(self.blue_model, prev_b)

        r = random.choice(self.red_model[prev_r])
        g = random.choice(self.green_model[prev_g])
        b = random.choice(self.blue_model[prev_b])
        return (r, g, b)

    def generate_one_pixel(self, x, y, seen_pixels, region_func):
        adj_points = region_func(x, y, self.gen_region_size)
        (acc_r, acc_g, acc_b) = (0, 0, 0)
        wt_sum = 0
        for (adj_x, adj_y) in adj_points:
            if (0 <= adj_x <= self.width - 1
                and 0 <= adj_y <= self.height - 1
                and (adj_x, adj_y) in seen_pixels):
                (r, g, b) = self.generate_from_one_neighbor(adj_x, adj_y)
                wt = 1
                acc_r += r * wt
                acc_g += g * wt
                acc_b += b * wt
                wt_sum += wt
        if wt_sum == 0: # haven't seen any neighbors yet, so can't predict
            new_r = random.choice(list(self.red_model.keys()))
            new_g = random.choice(list(self.green_model.keys()))
            new_b = random.choice(list(self.blue_model.keys()))
        else:
            new_r = int(round(float(acc_r)/wt_sum))
            new_g = int(round(float(acc_g)/wt_sum))
            new_b = int(round(float(acc_b)/wt_sum))
        self.result_pixels[x,y] = (new_r, new_g, new_b)
        seen_pixels.add((x,y))
               
    def actually_floodfill(self, region_func, x, y, seen_pixels, remaining_pixels):
        # progress update
        total_pixels = self.width * self.height
        if len(seen_pixels) % (total_pixels // 10) == 0 and len(seen_pixels) > 0:
            print("%d%% done" % (100 * len(seen_pixels) // total_pixels))
        # now do the actual stuff
        if len(seen_pixels) >= self.gen_pixel_limit:
            return
        else:
            self.generate_one_pixel(x, y, seen_pixels, region_func)
            adj_points = region_func(x, y, 1) # get all points 1 pixel away
            # traverse neighbors in random order
            wts = self.floodfill_wts_func(x,y)
            wts = [max(wt, 1) for wt in wts] # must be positive, let's say at least 1
            adj_points = util.weighted_random_shuffle(adj_points, wts)
            for (adj_x, adj_y) in adj_points:
                # if we haven't seen it, it's in bounds, and it's allowed
                if ((adj_x, adj_y) not in seen_pixels and
                    0 <= adj_x <= self.width - 1 and
                    0 <= adj_y <= self.height - 1 and
                    (adj_x, adj_y) in remaining_pixels):
                    self.actually_floodfill(region_func, adj_x, 
                                            adj_y, seen_pixels, remaining_pixels)
            
    # this is a wrapper, the main function is actually_floodfill
    def generate_floodfill(self, region_func):
        (width, height) = self.result_image.size
        remaining_pixels = util.get_all_pixels(width, height)
        self.result_pixels = self.result_image.load()      

        seen_pixels = set()
        while (len(remaining_pixels) > 0 and
                len(seen_pixels) < self.gen_pixel_limit):        
            (seed_x, seed_y) = random.choice(list(remaining_pixels))
            util.call_with_large_stack(self.actually_floodfill, region_func,
                                    seed_x, seed_y, seen_pixels, remaining_pixels)
            remaining_pixels -= seen_pixels     
                  
    def generate(self):
        self.result_image = Image.new('RGB', (self.width, self.height))
        self.generate_floodfill(self.default_region_func)
        return self.result_image
                                
def set_parameters():
    """
    PARAMETER DESCRIPTION

    User-specified parameters:
    - train_region_size: in training, how large a region to condition on  
    - palette_files: which files within palette_short_dir to train the palette on
    - output_dims: the (width, height) size of the output image
   - shape_func: This function determines what shape is drawn.
    Specifically, it determines the wts for a given x,y location, which
    determines which pixel we're likely to move to next. This function 
    must return a list with strictly positive values.    

    Non-user-specified parameters:
    - train_region_func: function that gets a list of neighboring points
    (i.e., surrounding region, upper left only, etc)
    - gen_region_size: how large a region to condition on in generation.
    Usually the same as train_region_size
    - train_palette_size: all images will be resized to have this many
    pixels during palette training
    - gen_pixel_limit: in generation, we will stop generating pixels after
    this many have been generated (the rest will be black). Usually you want
    this to be equal to width * height
    - shape_strength_x, shape_strength_y: scales how strongly we pursue shape_func
    - palette_short_dir: the path from main.py to the directory containing
    the images you want to use for palette training
    """
      
    # BEGIN USER PARAMETERS
    user_params = sys.argv
    if len(sys.argv) < 3 or sys.argv[2] == 'circle':
        shape_func = shape_funcs.circle
    elif sys.argv[2] == 'fractal':
        shape_func = shape_funcs.uniform
    elif sys.argv[2] == 'fermat':
        shape_func = shape_funcs.fermat_spiral
    elif sys.argv[2] == 'heart':
        shape_func = shape_funcs.heart
    else:
        raise ValueError("Not a supported shape")    
    try:
        result_size = int(sys.argv[1]) if len(sys.argv) >= 2 else 500
        palette_files = ['gradient3.jpg'] if len(sys.argv) < 4 else sys.argv[3].split(',')
        train_region_size = 2 if len(sys.argv) < 5 else int(sys.argv[4])    
    except:
        raise ValueError("Error with command line args. Usage: python main.py [result_size] [shape] [comma separated training files in a \"gradient\" folder] [training_region_size]")
    # END USER PARAMETERS

    # BEGIN NON-USER PARAMETERS
    train_region_func = lambda x,y: util.surrounding_region(x,y,train_region_size)
    train_palette_size = 50*50
    (width, height) = (result_size, result_size)
    output_dims = (width, height)
    gen_region_size = train_region_size
    gen_pixel_limit = width * height
    shape_strength_x = 100 # value of 1 corresponds to not really pursuing the shape at all
    shape_strength_y = 100 # same here
    palette_short_dir = 'input/gradients'
    palette_paths = util.get_input_paths(palette_short_dir, palette_files)
    # END NON-USER PARAMETERS

    params = (train_region_size, train_region_func, train_palette_size,
            gen_region_size, gen_pixel_limit, shape_strength_x, shape_strength_y, 
            shape_func, palette_paths, output_dims, palette_files, 
            palette_short_dir)

    return params

def main():
    params = set_parameters()
    (train_region_size, train_region_func, train_palette_size, gen_region_size,
     gen_pixel_limit, shape_strength_x, shape_strength_y, shape_func, palette_paths, 
     output_dims, palette_files, palette_short_dir) = params

    # initialize canvas
    root = Tk()
    (width, height) = output_dims
    canvas = Canvas(root, width = width, height = height)
    canvas.pack()

    model = Model(*params)
    print("Training model...")
    model.train_palette()
    print("Generating image...")    
    image = model.generate()
    output_name = util.make_output_name(
        shape_func, train_region_size, gen_region_size, 
        train_palette_size, palette_files)
    print("Saving output to %s..." % output_name)    
    image.save(output_name)
    tk_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor = NW, image = tk_image)
    root.mainloop()

if __name__ == "__main__":
    main()
