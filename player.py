import time
import math
import pygame
import getpass

class Player():

    def __init__(self):
        self.pos = [9, 9]
        self.inventory = []
        self.name = getpass.getuser()  # (:
        self.lastdir = 0
        self.animation_frame = 0
        self.last_animation_update = 0
        self.lastpos = None
        self.highlighted_item = 0
        self.held_item = -1

    def update(self, game):
        if self.lastpos is not None:
            if math.dist(self.lastpos, self.pos) >= 0.8:
                self.lastpos = None
            if (time.time() - self.last_animation_update) > .11:
                self.last_animation_update = time.time()
                self.animation_frame += 1
                if self.animation_frame > 3:
                    self.animation_frame = 0
            if self.lastdir == 0:
                self.pos[1] -= 2* (time.time() - game.prev_frame_time)
            if self.lastdir == 3:
                self.pos[1] += 2 * (time.time() - game.prev_frame_time)
            if self.lastdir == 1:
                self.pos[0] -= 2 * (time.time() - game.prev_frame_time)
            if self.lastdir == 2:
                self.pos[0] += 2 * (time.time() - game.prev_frame_time)
        else:
            self.pos[0] = int(round(self.pos[0]))
            self.pos[1] = int(round(self.pos[1]))
            
            posx = int(self.pos[0] + 1.5)
            posy = int(self.pos[1] + 0.5)

            if posy < len(game.layer1.layer):
                if posx < len(game.layer1.layer[posy]):
                    self.last_animation_update = time.time()
                    self.animation_frame = 0
                    if game.keys[pygame.K_UP]:
                        self.lastdir = 3
                        if game.layer1.layer[posy+1][posx+0] == 99999:
                            self.animation_frame = 0
                            self.lastpos = self.pos[:]
                    elif game.keys[pygame.K_DOWN]:
                        self.lastdir = 0
                        if game.layer1.layer[posy-1][posx+0] == 99999:
                            self.animation_frame = 0
                            self.lastpos = self.pos[:]
                    elif game.keys[pygame.K_LEFT]:
                        self.lastdir = 1
                        if game.layer1.layer[posy+0][posx-1] == 99999:
                            self.animation_frame = 0
                            self.lastpos = self.pos[:]
                    elif game.keys[pygame.K_RIGHT]:
                        self.lastdir = 2
                        if game.layer1.layer[posy+0][posx+1] == 99999:
                            self.animation_frame = 0
                            self.lastpos = self.pos[:] 

            if game.keys[pygame.K_s]:
                game.switch_state("Inventory state")

    def render(self, game):
        if "lightbulb" in self.inventory:
            asset = game.assets["niko"]["b" + str(self.lastdir) + str(self.animation_frame)]
        else:
            asset = game.assets["niko"]["nb" + str(self.lastdir) + str(self.animation_frame)]
        game.display.blit(asset, (game.resolution[0] // 2 - asset.get_size()[0] // 2, game.resolution[1] // 2 - asset.get_size()[1] // 2))
