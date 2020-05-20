import os
import sys
import time
import math
import pygame
import traceback

from objects import *
from utilities import *
from player import Player

import extensions

class Layer():
    def __init__(self, data, game):
        self.layer = []
        self.game = game
        for row in data:
            lrow = []
            for c1, c2, c3, c4, c5 in zip(*[row[i::5] for i in range(5)]):
                lrow.append(int((c1 + c2 + c3 + c4 + c5).lstrip("0")))
            self.layer.append(lrow)
    
    def render(self):
        for y, row in enumerate(self.layer):
            for x, cell in enumerate(row):
                if cell == 99999:
                    continue
                x2 = x - 1
                y2 = y - 1
                x2 -= self.game.player.pos[0]
                y2 -= self.game.player.pos[1]
                x2 *= 32
                y2 *= 32
                x2 += self.game.resolution[0] // 2
                y2 += self.game.resolution[1] // 2

                x2 -= 16
                y2 += 32

                y2 = self.game.resolution[1] - y2

                self.game.display.blit(self.game.assets["tiles"][cell], (x2, y2))

class Game():

    def get_state(self): 
        return self._state

    def set_state(self, x):
        print(x)
        self._state = x

    state = property(get_state, set_state)

    def main_game_state(self):
        # pygame.mixer.music.set_volume(0)
        self.player.update(self)
                
        x = self.objects.copy()
        for i in x:
            i.update()

        self.display.fill(0)
        self.layer1.render()
        self.layer2.render()
        self.layer3.render()

        # Sort all objects
        arr = sorted(
            list(self.objects) + [self.player, ],
            key=lambda x: (x.y if issubclass(type(x), Object) else x.pos[1]),
            reverse=True
        )

        # Render all objects
        for i in arr:
            if issubclass(type(i), Object):
                i.render()
            else:
                i.render(self)

    def textbox_state_0(self):
        self.textboxy = self.resolution[1] - self.textbox_img.get_size()[1] - 10
        face = self.assets["faces"][self.state_args[0]]

        if not hasattr(self, "index"):
            self.display.blit(self.textbox_img, (10, self.textboxy))
            self.display.blit(face, (self.resolution[0] - face.get_size()[0] - 22, self.textboxy + 16))
            self.index = 0
            self.str_len = sum([len(j) for j in self.state_args[1:]])
            self.LogInfo("%s:\n%s" % (self.state_args[0], "\n".join(self.state_args[1:])))
            self._x = 0
            self._y = 1
            self._y2 = 1
            self.texts = ["" for _ in self.state_args[1:]]
        
        if self.index < self.str_len:
            if len(self.state_args[self._y]) == 0:
                self._y += 1
            else:
                self.texts[self._y - 1] += self.state_args[self._y][self._x]
                self._x += 1
            if self._x >= len(self.state_args[self._y]):
                self._x = 0
                self._y += 1
                if self._y > len(self.state_args[1:]):
                    self._y -= 1
            if self._y > 3:
                # Restart function
                self.state_args = [self.state_args[0]] + self.state_args[self._y:]
                del self.index
                self.mode = 3
                return
            for i in range(len(self.texts)):
                self.display.blit(
                    self.textboxfont.render(self.texts[i], True, [255, 255, 255], [24, 12, 25]),
                    (35, i*29 + self.textboxy + 15)
                )
            self.index += 1
        else:
            self.mode = 1

    def textbox_state(self):
        if self.mode == 0:
            self.textbox_state_0()
        elif self.mode == 1:
            if hasattr(self, "index"):
                delattr(self, "index")
            if self.keys[pygame.K_z] or self.keys[pygame.K_x]:
                self.mode = 2
        elif self.mode == 2:
            if not (self.keys[pygame.K_z] or self.keys[pygame.K_x]):
                self.switch_state("Main game state")
        elif self.mode == 3:
            if self.keys[pygame.K_z] or self.keys[pygame.K_x]:
                self.mode = 4
        elif self.mode == 4:
            if not (self.keys[pygame.K_z] or self.keys[pygame.K_x]):
                self.mode = 0

    def code_state(self):
        if not hasattr(self, "selected_code"):
            self.selected_code = [0, 0, 0, 0]
            self.cursor_pos = 0

        if self.mode == 0:
            self.display.fill(0)

            if self.keys[pygame.K_RIGHT]:
                self.cursor_pos += 1
                if self.cursor_pos > 3:
                    self.cursor_pos = 0
                self.mode = 1
            if self.keys[pygame.K_LEFT]:
                self.cursor_pos -= 1
                if self.cursor_pos < 0:
                    self.cursor_pos = 3
                self.mode = 2

            if self.keys[pygame.K_UP]:
                self.selected_code[self.cursor_pos] += 1
                if self.selected_code[self.cursor_pos] > 9:
                    self.selected_code[self.cursor_pos] = 0
                self.mode = 3
            if self.keys[pygame.K_DOWN]:
                self.selected_code[self.cursor_pos] -= 1
                if self.selected_code[self.cursor_pos] < 0:
                    self.selected_code[self.cursor_pos] = 9
                self.mode = 4

            if self.keys[pygame.K_z]:
                self.mode = 5
            
            self.display.blit(
                self.mainfont.render("Enter code:", True, [255, 255, 255], [0, 0, 0]),
                (10, 10)
            )
            self.display.blit(
                self.mainfont.render(" ".join(str(i) for i in self.selected_code), True, [255, 255, 255], [0, 0, 0]),
                (10, 28)
            )
            self.display.blit(
                self.mainfont.render(2 * self.cursor_pos * " " + "^", True, [255, 255, 255], [0, 0, 0]),
                (10, 48)
            )

        elif self.mode == 1:
            if not self.keys[pygame.K_RIGHT]:
                self.mode = 0

        elif self.mode == 2:
            if not self.keys[pygame.K_LEFT]:
                self.mode = 0

        elif self.mode == 3:
            if not self.keys[pygame.K_UP]:
                self.mode = 0

        elif self.mode == 4:
            if not self.keys[pygame.K_DOWN]:
                self.mode = 0

        elif self.mode == 5:
            if not self.keys[pygame.K_z]:
                self.state_result = "".join(str(i) for i in self.selected_code)
                self.switch_state("Main game state")
        
    def inventory_state(self):
        if self.mode == 1:
            if self.keys[pygame.K_RIGHT]:
                self.assets["sounds"]["menu_cursor"].play()
                self.player.highlighted_item += 1
                if self.player.highlighted_item >= len(self.player.inventory):
                    self.player.highlighted_item = len(self.player.inventory) - 1
                self.mode = 3

            if self.keys[pygame.K_LEFT]:
                self.assets["sounds"]["menu_cursor"].play()
                self.player.highlighted_item -= 1
                if self.player.highlighted_item < 0:
                    self.player.highlighted_item = 0
                self.mode = 4

            if self.keys[pygame.K_UP]:
                self.assets["sounds"]["menu_cursor"].play()
                self.player.highlighted_item -= 2
                if self.player.highlighted_item < 0:
                    self.player.highlighted_item = 0
                self.mode = 5

            if self.keys[pygame.K_DOWN]:
                self.assets["sounds"]["menu_cursor"].play()
                self.player.highlighted_item += 1
                if self.player.highlighted_item >= len(self.player.inventory):
                    self.player.highlighted_item = len(self.player.inventory) - 1
                self.mode = 6

            if self.keys[pygame.K_z]:
                self.mode = 7
                if self.player.highlighted_item == self.player.held_item:
                    self.player.held_item = -1
                    self.assets["sounds"]["menu_cancel"].play()
                elif self.player.held_item == -1:
                    self.player.held_item = self.player.highlighted_item
                    self.assets["sounds"]["menu_decision"].play()
                else:
                    self.assets["sounds"]["menu_decision"].play()
                    self.mode = 8
        
        
        self.display.blit(self.inv_img_top, (15, 15))
        self.display.blit(self.inv_img_bottom, (15, 94))
        desc = self.item_descs[self.player.inventory[self.player.highlighted_item]]
        self.display.blit(
            self.mainfont.render(desc, True, [255, 255, 255], [24, 12, 25]),
            (320 - self.mainfont.size(desc)[0] // 2, 35)
        )

        if self.player.highlighted_item % 2 == 0:
            self.display.blit(self.inv_sel, (
                31,
                (self.player.highlighted_item // 2) * 32 + 110
            ))
        else:
            self.display.blit(self.inv_sel, (
                332,
                (self.player.highlighted_item // 2) * 32 + 110
            ))
        
        for i in range(len(self.player.inventory)):
            if i == self.player.held_item:
                color = [222, 134, 0]
            else:
                color = [255, 255, 255]
            
            size = self.mainfont.size(self.player.inventory[i])[0]
            if i % 2 == 0:
                self.display.blit(
                    self.mainfont.render(self.player.inventory[i], True, color, [55, 18, 38]),
                    (165 - size // 2, (i // 2) * 35 + 115)
                )
                self.display.blit(
                    self.assets["items"][self.player.inventory[i]],
                    (31, (i // 2) * 35 + 110)
                )
            else:
                self.display.blit(
                    self.mainfont.render(self.player.inventory[i], True, color, [55, 18, 38]),
                    (460 - size // 2, (i // 2) * 35 + 115)
                )
                self.display.blit(
                    self.assets["items"][self.player.inventory[i]],
                    (332, (i // 2) * 35 + 110)
                )

        # print("Inventory state: not implemented")
        if self.mode == 0:
            if not (self.keys[pygame.K_x] or game.keys[pygame.K_s]):
                self.mode = 1

        elif self.mode == 1:
            if self.keys[pygame.K_x] or game.keys[pygame.K_s]:
                self.mode = 2

        elif self.mode == 2:
            if not (self.keys[pygame.K_x] or game.keys[pygame.K_s]):
                self.switch_state("Main game state")

        elif self.mode == 3:
            if not self.keys[pygame.K_RIGHT]:
                self.mode = 1

        elif self.mode == 4:
            if not self.keys[pygame.K_LEFT]:
                self.mode = 1

        elif self.mode == 5:
            if not self.keys[pygame.K_UP]:
                self.mode = 1

        elif self.mode == 6:
            if not self.keys[pygame.K_DOWN]:
                self.mode = 1

        elif self.mode == 7:
            if not self.keys[pygame.K_z]:
                self.mode = 1

        elif self.mode == 8:
            if not self.keys[pygame.K_z]:
                # self.mode = 1
                for i in self.objects:
                    if i.name == "merger":
                        i.trigger_input(
                            self.player.inventory[self.player.held_item],
                            self.player.inventory[self.player.highlighted_item], 
                        )

    def load_data_state(self):
        print("loading", self.level)
        self.load_level(self.level)
        for i in self.objects:
            if not i.started:
                i.trigger_input("Start", "")
                i.started = True
        self.switch_state("Main game state")

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        # pygame.mixer.music.set_volume(0)
        descs = open(r"Item Descriptions.txt", encoding="utf-8-sig").read().split("\n")
        config = open(r"config.txt", encoding="utf-8").read().split("\n") # No utf-8-sig as this file isn't shared with Scratch
        self.config = CaseInsensitiveDict({k: v for k, v in zip(config[::2], config[1::2])})
        
        self.item_descs = CaseInsensitiveDict({k: v for k, v in zip(descs[::2], descs[1::2])})
        x = open(r"LEVELS.txt", encoding="utf-8-sig").read()
        self.state_map = {
            "Main game state": self.main_game_state,
            "Textbox state":   self.textbox_state,
            "Inventory state": self.inventory_state,
            "Load data state": self.load_data_state,
            "Code state":      self.code_state,
        }
        self.state_frame = 0
        self.mode = 0
        self.player = Player()
        self.levels = [i[1:-1] if i[0:1] == "\"" else i for i in x.split("\n")]
        self.state_result = None
        self.state_args = []
        self.assets = {
            "tiles": {},
            "objects": {},
            "niko": {},
            "sounds": {},
            "music": {},
            "faces": {},
            "items": {},
            "items2x": {},
        }
        for i in os.listdir("tiles"):
            self.assets["tiles"][int(i.split(".")[0])] = pygame.image.load(os.path.join("tiles", i))
        for i in os.listdir("objects"):
            self.assets["objects"][i.split(".")[0]] = pygame.image.load(os.path.join("objects", i))
        for i in os.listdir("niko"):
            self.assets["niko"][i.split(".")[0]] = pygame.image.load(os.path.join("niko", i))
        for i in os.listdir("sounds"):
            self.assets["sounds"][i.split(".")[0]] = pygame.mixer.Sound(os.path.join("sounds", i))
        for i in os.listdir("music"):
            self.assets["music"][i.split(".")[0]] = os.path.join("music", i)
        for i in os.listdir("faces"):
            self.assets["faces"][i.split(".")[0]] = pygame.image.load(os.path.join("faces", i))
        for i in os.listdir("items"):
            self.assets["items"][i.split(".")[0]] = pygame.image.load(os.path.join("items", i))
        for i in os.listdir("items"):
            self.assets["items2x"][i.split(".")[0]] = pygame.transform.scale2x(pygame.image.load(os.path.join("items", i)))
        self.state = "Load data state"

        self.level = 0
        self.inv_img_top    = pygame.image.load("invtext1.png")
        self.inv_img_bottom = pygame.image.load("invtext2.png")
        self.inv_sel        = pygame.image.load("invsel.png")

        self.textboxfont = pygame.font.Font("main.ttf", 29)
        self.mainfont    = pygame.font.Font("main.ttf", 20)
        self.resolution = (640, 480)
        self.display = pygame.display.set_mode(self.resolution)
        pygame.display.set_caption(self.config["Name"])
        pygame.display.set_icon(pygame.image.load(self.config["Icon"]))
        self.time = 0.0
        self.keys = [0] * 255

        self.change_state_last = None
        self.changing_state = False
        tb = pygame.image.load("textbox.png")
        aspect = tb.get_size()[1] / tb.get_size()[0]
        self.textbox_img = pygame.transform.scale(tb, (self.resolution[0] - 20, int((self.resolution[0] - 20) * aspect)))

    def mainloop(self):
        self.clock = pygame.time.Clock()
        self.prev_frame_time = time.time()
        while 1:
            self.clock.tick(30)
            
            self.time = time.time()
            self.state_map[self.state]()
            if self.player.held_item != -1:
                self.display.blit(
                    self.assets["items2x"][self.player.inventory[self.player.held_item]],
                    (580, 420)
                )
            self.state_frame += 1
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.display.quit()
                    pygame.mixer.quit()
                    pygame.quit()
                    sys.exit(0)

            self.keys = pygame.key.get_pressed()
            pygame.display.flip()
            self.prev_frame_time = self.time

    def switch_state(self, name):
        if self.changing_state:
            self.change_state_last = name
        else:
            print("state changed to", name)
            self.state = name
            self.state_frame = 0
            self.mode = 0

            self.changing_state = True
            objs = self.objects.copy()
            for i in objs:
                i.game_state_changed(name, self.state_result)
            self.changing_state = False
            if self.change_state_last is not None:
                x = self.change_state_last
                self.change_state_last = None
                self.switch_state(x)
        
    def load_level(self, n):
        self.layer1, self.layer2, self.layer3, self.objects = self.decode(self.levels[n])

    def LogInfo(self, x):
        print(x)

    def LogWarning(self, x):
        print("Warning: ", x)

    def LogError(self, x):
        print(x, file=sys.stderr)

    def decode(game, level):
        try:
            lists_raw = level.split("°")

            list1_raw = lists_raw[0].split("÷")[:-1]
            list2_raw = lists_raw[1].split("÷")[:-1]
            list3_raw = lists_raw[2].split("÷")[:-1]
            list4_raw = lists_raw[3].split("÷")[:-1]

            objects = []
            i = 0
            while i < len(list4_raw):
                kvs = CaseInsensitiveDict()

                type  = list4_raw[i+0]
                name  = list4_raw[i+1]
                kvlen = int(list4_raw[i+2])
                i += 3
                for _ in range(kvlen):
                    kvs[list4_raw[i].lower()] = list4_raw[i+1]
                    i += 2
                objects.append(NAME2OBJTYPE[type](name, kvs, game))

            return Layer(list1_raw, game), Layer(list2_raw, game), Layer(list3_raw, game), set(objects)
        except IndexError:
            traceback.print_exc()
            return Layer([], game), Layer([], game), Layer([], game), set()

if __name__ == "__main__":
    game = Game()
    game.mainloop()
