# main.py - generates artistic pictures
# Author: Ben Plaut
# Main file. Contains main model for training and generation, as well as all
# of the parameters, which are set in the set_parameters function.
# Required external modules: PIL
# Requires python files: util.py

from tkinter import *
from PIL import Image, ImageTk
import os
import random
import util # file with helper functions
import shuffle_wt_funcs # for weighting directions in floodfill

class Model(object):
    def __init__(self, *args):
        (train_region_size, train_region_func, train_palette_size, 
         gen_region_size, mode, gen_pixel_limit, x_scale, y_scale, 
         shuffle_wts_func, extra_args, palette_paths, output_size) = args

        # extra_args specified additional arguments for the generation function
        (self.result_width, self.result_height) = output_size
        self.palette_paths = palette_paths
        self.train_palette_size = train_palette_size
        
        self.gen_region_size = gen_region_size
        self.mode = mode
        self.train_region_func = train_region_func
        # can't be more than width*height
        self.gen_pixel_limit = min(gen_pixel_limit,
                                   self.result_width * self.result_height)
        self.extra_args = extra_args
        if self.mode == 'diagonal':
            self.generation_func = self.generate_diagonally
            self.default_region_func = util.upper_left_region
        elif self.mode == 'flood':
            self.default_region_func = util.surrounding_region
            self.generation_func = self.generate_floodfill
        else:
            raise ValueError("Not a supported mode. Supported modes are 'diagonal' and 'flood' (Flood is way better, choose flood. Flood is pretty much a generalization of diagonal)") 

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
            print(image_path)
            # want to resize so that dimension ratio is maintained, but the
            # number of pixels is now self.train_palette_size
            image = util.resize_intelligently(image, self.train_palette_size)
            (new_width, new_height) = image.size
            pixels = image.load()
            # First, do the markov-chain-style conditioning
            for x in range(new_width):
                for y in range(new_height):
                    self.train_from_pixel(pixels, x, y, new_width, new_height)
                                          
    def generate_from_one_neighbor(self, prev_x, prev_y, pixels):
        (prev_r, prev_g, prev_b) = pixels[prev_x, prev_y]
        prev_r = util.closest_val_in_dict(self.red_model, prev_r)
        prev_g = util.closest_val_in_dict(self.green_model, prev_g)
        prev_b = util.closest_val_in_dict(self.blue_model, prev_b)

        r = random.choice(self.red_model[prev_r])
        g = random.choice(self.green_model[prev_g])
        b = random.choice(self.blue_model[prev_b])
        return (r, g, b)

    def generate_one_pixel(self, x, y, result_pixels, seen_pixels, region_func):
        adj_points = region_func(x, y, self.gen_region_size)
        (acc_r, acc_g, acc_b) = (0, 0, 0)
        wt_sum = 0
        for (adj_x, adj_y) in adj_points:
            if (0 <= adj_x <= self.result_width - 1
                and 0 <= adj_y <= self.result_height - 1
                and (adj_x, adj_y) in seen_pixels):
                (r, g, b) = self.generate_from_one_neighbor(adj_x, adj_y,
                                                            result_pixels)
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
        result_pixels[x,y] = (new_r, new_g, new_b)
        seen_pixels.add((x,y))
               
    def generate_diagonally(self, result_image, region_func):
        # generates the image with one pass through, going from upper left
        # to bottom right
        seen_pixels = set()
        result_pixels = result_image.load()
        for x in range(self.result_width):
            for y in range(self.result_height):
                self.generate_one_pixel(x, y, result_pixels, seen_pixels,
                                        region_func)

    def actually_floodfill(self, result_pixels, region_func, x, y,
                           seen_pixels, allowed_pixels):
        if len(seen_pixels) >= self.gen_pixel_limit:
            return # done every pixel
        else:
            self.generate_one_pixel(x, y, result_pixels, seen_pixels,
                                    region_func)
            adj_points = region_func(x, y, 1) # get all points 1 pixel away
            # traverse neighbors in random order
            shuffle_wts = self.shuffle_wts_func(x,y)
            shuffle_wts = [max(wt, 1) for wt in shuffle_wts] # must be
            # positive, let's say at least 1
            adj_points = util.weighted_random_shuffle(adj_points, shuffle_wts)
            for (adj_x, adj_y) in adj_points:
                # if we haven't seen it, it's in bounds, and it's allowed
                if ((adj_x, adj_y) not in seen_pixels and
                    0 <= adj_x <= self.result_width - 1 and
                    0 <= adj_y <= self.result_height - 1 and
                    (adj_x, adj_y) in allowed_pixels):
                    
                    self.actually_floodfill(result_pixels, region_func,
                                            adj_x, adj_y, seen_pixels,
                                            allowed_pixels)
            
    # this is a wrapper
    def generate_floodfill(self, result_image, region_func):
        (self.shuffle_wts_func,) = self.extra_args
        (result_width, result_height) = result_image.size
        remaining_pixels = util.get_all_pixels(result_width, result_height)
        result_pixels = result_image.load()      

        overall_seen = set()
        while (len(remaining_pixels) > 0 and
                len(overall_seen) < self.gen_pixel_limit):        
            (seed_x, seed_y) = random.choice(list(remaining_pixels))
            util.call_with_large_stack(self.actually_floodfill, result_pixels, region_func,
                                    seed_x, seed_y, overall_seen, remaining_pixels)
            remaining_pixels -= overall_seen     
        
                           
    def generate(self):
        result = Image.new('RGB', (self.result_width, self.result_height))
        self.generation_func(result, self.default_region_func)
        return result
                                
def set_parameters():
    """
    BEGIN PARAMETERS
    - train_region_size:in training, how large a region to condition on
    - train_region_func: function that gets a list of neighboring points
    (i.e., surrounding region, upper left only, etc)
    - train_palette_size: all images will be resized to have this many
    pixels during palette training
    - output_size: the (width, height) size of the output image :P
    - gen_region_size: how large a region to condition on in generation
    - gen_pixel_limit: in generation, we will stop generating pixels after
    this many have been generated (the rest will be black)
    - mode: what method of generation: diagonal, scatter, or floodfill
    Note: mode kind of determines what style the picture is drawn in
    Note: some modes need additional args. They are listed now:
    - shuffle_wts_func: NOTE: don't this. Change unformatted_func instead.
    For floodfill, when we traverse the neighbors in a
    random order, it can be a weighted random order. Higher weight
    means we're more likely to traverse that neighbor earlier in the order.
    - unformatted_func: A function that takes (x,y,width,height,x_scale,
    y_scale) that will be called to determine the wts for the different
    directions at a given x,y location
    Note1: If the function depends on x,y, directions will have different
    wts in different parts of the image. You can get cool effects with this
    Note2: this function must return a list with strictly positive values
    - x_scale, y_scale: your unformmated func can just ignore these if you
    want, but I use them to scale the x and y componenets of the result
    - extra_args: need to pack whatever extra args you want in this tuple
    - palette_short_dir: the path from main.py to the directory containing
    the images you want to use for palette training
    - palette_files: the indices of which images inside palette_short_dir
    to keep
    """
      
    train_region_size = 2
    train_region_func = lambda x,y: util.surrounding_region(x,y,train_region_size)
    train_palette_size = 50*50
    (width, height) = (500, 500)
    output_size = (width, height)
    gen_region_size = 2
    mode = 'flood'
    gen_pixel_limit = 10000000000
    unformatted_func = shuffle_wt_funcs.circle
    x_scale = 100
    y_scale = 100
    shuffle_wts_func = lambda x,y: unformatted_func(x,y, width, height, x_scale, y_scale)
    extra_args = (shuffle_wts_func,)
    palette_files = ['gradient4.jpg', 'gradient3.jpg']
    palette_short_dir = 'input/gradients'
    palette_paths = util.get_input_paths(palette_short_dir, palette_files)
    # END PARAMETERS

    args = (train_region_size, train_region_func, train_palette_size,
            gen_region_size, mode, gen_pixel_limit, x_scale, y_scale, 
            shuffle_wts_func, extra_args, palette_paths, output_size)
    stuff_for_file_naming = (palette_files, palette_short_dir, unformatted_func)

    return (args, stuff_for_file_naming)

def main():
    (args, stuff_for_file_naming) = set_parameters()
    (train_region_size, train_region_func, train_palette_size, gen_region_size,
     mode, gen_pixel_limit, x_scale, y_scale, shuffle_wts_func, extra_args, 
     palette_paths, output_size) = args
    (palette_files, palette_short_dir, unformatted_func) = stuff_for_file_naming

    # initialize canvas
    root = Tk()
    (width, height) = output_size
    canvas = Canvas(root, width = width, height = height)
    canvas.pack()

    model = Model(*args)
    model.train_palette()
    image = model.generate()
    output_name = util.make_output_name(
        unformatted_func, x_scale, y_scale, train_region_size, gen_region_size, 
        train_palette_size, palette_files)
    image.save(output_name)
    tk_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor = NW, image = tk_image)
    root.mainloop()

if __name__ == "__main__":
    main()

# One good parameter set: train_region_size = 3, gen_region_size = 2,
# train_size = (500, 500), mode = flood, training images = gradient1 and
# gradient2, shuffle_wts_func = uniform

# Another: train_region_size = gen_region_size = 2,
# train_size = (50, 50), mode = flood, training images = gradient 1 and 2,
# shuffle_wts_func = circle

