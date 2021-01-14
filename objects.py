import time
import math
import pygame
import traceback

class Object():
    def __init__(self, name, keyvalues, game):
        self.keyvalues = keyvalues
        self.name = name
        # self.outputs_triggered = []
        self.game = game
        self.started = False
        self.game.LogInfo("Created %s" % (self.name))
        self.x = float(self.keyvalues.get("Position X", "0.0"))
        self.y = float(self.keyvalues.get("Position Y", "0.0"))

        self._current_input = "<Not in input>"

    # async def input_kill(self, arg):
    #     self.game.LogInfo("Killed %s %s" % (self.name, self))
    #     self.game.objects.remove(self)

    def trigger_input(self, input, argument):
        self._current_input = input
        
        if input.lower() == "kill":
            try:
                self.game.objects.remove(self)
            except KeyError:
                self.game.LogWarning("Cannot remove self")
            return
        if not hasattr(self, "input_" + input.lower()):
            m = {v: k for k, v in NAME2OBJTYPE.items()}
            self.game.LogWarning("[%s;%s] Unknown input %s" % (m[self.__class__], self.name, input.lower()))
            return []
        if 1: # try:
            getattr(self, "input_" + input.lower())(argument)
        # except Exception as e:
            # self.game.LogError("In %s" % (self.name))
            # self.game.LogError(traceback.format_exc())
        
        self._current_input = "<Not in input>"

    def trigger_output(self, a, b=None, c=None):
        if b == None:
            try:
                target, input, arg = self.decode_output(self.keyvalues[a])
                self.trigger_output(target, input, arg)
            except KeyError:
                m = {v: k for k, v in NAME2OBJTYPE.items()}
                # self.game.LogWarning("[%s;%s] Unknown output %s" % (m[self.__class__], self.name, a.lower()))
        else:
            if c == None:
                raise TypeError("Either (a, b, c) or just a have to be set")
            if a.lower() == "niko":
                # Player
                if b.lower() == "teleport":
                    self.game.player.pos = [int(c[:3]), int(c[3:])]
            else:
                objs = self.game.objects.copy()
                for obj in objs:
                    if obj.name == a:
                        self.game.LogInfo("%s %s => %s   %s(%s)" % (self.name, self._current_input, a, b, c))
                        self.game.schedule_input(obj, b, c)

    def decode_output(self, output, delim=":"):
        return output.split(delim)[:-1]

    def game_state_changed(self, to, res):
        if to == "Load data state":
            # self.game.objects.remove(self)
            self.trigger_output(self.name, "Kill", "")
            self.game.LogInfo("Killed %s" % (self.name))

    def update(self):
        ...

    def render(self):
        ...

class Music(Object):

    def input_start(self, arg):
        if self.game.music_persistent:
            self.game.objects.remove(self)
        else:
            self.game.music_persistent = int(self.keyvalues["Persistent"]) > 0
    
    def update(self):
        if not hasattr(self, "last_time"):
            self.reload_song()
        
        if (self.game.time - self.last_time) > float(self.keyvalues["length"]):
            self.last_time = self.game.time

            self.reload_song()
            
            pygame.mixer.music.rewind()
            pygame.mixer.music.play()

    def reload_song(self):
        track = self.keyvalues["track"]
        if track in self.game.assets["music"]:
            pygame.mixer.music.load(self.game.assets["music"][track])
            pygame.mixer.music.play()
        else:
            self.game.LogError("Couldn't load resource music/%s" % (track))
        self.last_time = self.game.time

    def game_state_changed(self, to, res):
        if not (to == "Load data state" and self.game.music_persistent):
            super().game_state_changed(to, res)

class TriggerOnce(Object):

    def update(self):
        self.keyvalues["Position X"] = float(self.keyvalues["Position X"])
        self.keyvalues["Position Y"] = float(self.keyvalues["Position Y"])
        if round(self.game.player.pos[0]) == self.keyvalues["Position X"]:
            if round(self.game.player.pos[1]) == self.keyvalues["Position Y"]:
                self.trigger_output("Touched")
                self.trigger_output(self.name, "Kill", "")

class TriggerMultiple(Object):

    def input_start(self, arg):
        self.triggered = False
    
    def update(self):
        self.keyvalues["Position X"] = float(self.keyvalues["Position X"])
        self.keyvalues["Position Y"] = float(self.keyvalues["Position Y"])
        if round(self.game.player.pos[0]) == self.keyvalues["Position X"]:
            if round(self.game.player.pos[1]) == self.keyvalues["Position Y"]:
                if not self.triggered:
                    self.trigger_output("Touched")
                    self.triggered = True
            else:
                self.triggered = False
        else:
            self.triggered = False

class Textbox(Object):

    def input_start(self, a):
        self.waiting = False
        self.trigger_done = False

    def input_show(self, a):
        self.game.state_args = self.keyvalues["Content"].replace("▒", self.game.player.name).split("█")[:-1]
        self.game.switch_state("Textbox state")
        self.waiting = True

    def update(self):
        if self.trigger_done:
            self.trigger_output("Done")
            self.trigger_done = False

    def game_state_changed(self, to, res):
        if not hasattr(self, "waiting"):
            self.waiting = False
        if to == "Main game state":
            if self.waiting:
                print(self, to)
                self.waiting = False
                try:
                    self.trigger_done = True
                except KeyError:
                    pass
        
        elif to == "Load data state":
            self.game.objects.remove(self)
            self.game.LogInfo("Killed %s" % (self.name))

class Equip(Object):

    def input_start(self, a):
        self.sound = self.game.assets["sounds"].get("item_get", None)
        if self.sound is None:
            self.game.LogError("Couldn't load resource sounds/item_get")

    def input_equip(self, a):
        self.game.player.inventory.append(a)
        if self.keyvalues.get("sound?", 0) == 1:
            if self.sound is not None:
                self.sound.play()

class Broadcaster(Object):

    def input_fire(self, a):
        self.trigger_output("OnFire1")
        self.trigger_output("OnFire2")
        self.trigger_output("OnFire3")
        self.trigger_output("OnFire4")
        self.trigger_output("OnFire5")
        self.trigger_output("OnFire6")
        self.trigger_output("OnFire7")
        self.trigger_output("OnFire8")

class Merge(Object):

    def trigger_input(self, item1, item2):
        if item1.lower() == "start":
            return
        if item1.lower() == "kill":
            return
        if (item1 + "+" + item2) not in self.keyvalues:
            self.game.state_args = ["niko", "I can't combine these."]
            self.game.switch_state("Textbox state")
        else:
            self.game.state_args = []
            self.game.switch_state("Main game state")
            self.trigger_output(item1 + "+" + item2)

class PlayerMove(Object):

    def input_start(self, a):
        self.trigger_output("start")

    def input_enablemovement(self, a):
        self.game.player.locked = False

    def input_disablemovement(self, a):
        self.game.player.locked = True

class Sound(Object):

    def input_start(self, arg):
        self.fading_i = -1
        self.currently_playing = None

    def input_play(self, arg):
        self.fading_i = 20
        self.currently_playing = self.game.assets["sounds"][arg]
        self.playing = False
        self.time = 0
        self.last_decrease = self.game.time

    def update(self):
        if not hasattr(self, "currently_playing"):
            self.currently_playing = None
            self.fading_i = -1
        
        if self.currently_playing:
            if self.playing:
                if (self.game.time - self.time) > self.currently_playing.get_length():
                    self.playing = False
            if self.fading_i == 10:
                self.currently_playing.play()
                if not self.playing:
                    self.time = self.game.time
                    self.playing = True
                    self.fading_i -= 1
            if self.fading_i > 10:
                if self.game.time - self.last_decrease > 0.04:
                    self.last_decrease = self.game.time
                    pygame.mixer.music.set_volume((self.fading_i - 10) / 10)
                    self.fading_i -= 1
            else:
                if self.game.time - self.last_decrease > 0.04:
                    self.last_decrease = self.game.time
                    pygame.mixer.music.set_volume((10 - self.fading_i) / 10)
                    self.fading_i -= 1
            if self.fading_i == -1:
                self.currently_playing = None
                self.trigger_output("Done")

class Interactible(Object):

    def input_start(self, a):
        self.lastmove = 0
        self.to = None
        if self.keyvalues["sprite"] in self.game.assets["objects"]:
            self.sprite = self.game.assets["objects"][self.keyvalues["sprite"]]
        else:
            self.game.LogError("Couldn't load resource objects/%s" % (self.keyvalues["sprite"]))
            self.sprite = None

    def input_use(self, a):
        self.trigger_output("OnUse")
        if self.game.player.held_item != -1:
            self.trigger_output("OnUse-" + self.game.player.inventory[self.game.player.held_item])
        else:
            self.trigger_output("OnUse-NothingHeld")

    def input_moveto(self, a):
        self.lastmove = 0
        self.glidei = 0
        self.to = int(a[:3]), int(a[3:])
        self.mode = ""

    def update(self):
        if self.keyvalues["sprite"] in self.game.assets["objects"]:
            self.sprite = self.game.assets["objects"][self.keyvalues["sprite"]]
        else:
            self.sprite = None
        
        if not hasattr(self, "mode"):
            self.mode = ""
            self.to = None
            self.lastmove = 0
        
        if self.mode == "":
            self.mode = "moveto"
            if self.game.keys[pygame.K_z]:
                if self.game.state == "Main game state":
                    self.mode = "wait_z"

        elif self.mode == "wait_z":
            if not self.game.keys[pygame.K_z]:
                if math.dist((self.game.player.pos[0] * 32, self.game.player.pos[1] * 32), (self.x * 32, self.y * 32)) < 33:
                    self.trigger_output(self.name, "Use", "")
                
                self.mode = "moveto"

        elif self.mode == "moveto":
            self.mode = ""
            if self.to:
                if math.dist(self.to, (self.x, self.y)) < 1:
                    self.to = None
                self.mode = "moveto"
                if self.game.time - self.lastmove > float(self.keyvalues["MoveDelay"]):
                    coords = ((self.x-1, self.y), (self.x+1, self.y), (self.x, self.y+1), (self.x,self.y-1))
                    coords2 = ((-1,  0), (+1,  0), ( 0, +1), ( 0, -1))
                    
                    self.lastmove = self.game.time

                    left_dist  = math.dist(self.to, coords[0])
                    right_dist = math.dist(self.to, coords[1])
                    up_dist    = math.dist(self.to, coords[2])
                    down_dist  = math.dist(self.to, coords[3])
                    self.glide = coords[mini(left_dist, right_dist, up_dist, down_dist)]
                    self.glidei = 0
                    self.mode = "glideto"

        elif self.mode == "glideto":
            if self.glide[0] > 0:
                self.x += 0.2
            if self.glide[0] < 0:
                self.x -= 0.2
            if self.glide[1] > 0:
                self.y += 0.2
            if self.glide[1] < 0:
                self.y -= 0.2
            
            self.glidei += 1
            if self.glidei == 4:
                self.mode = ""

    def render(self):
        if self.sprite is not None:
            x2 = self.x
            y2 = self.y
            x2 -= self.game.player.pos[0]
            y2 -= self.game.player.pos[1]
            x2 *= 32
            y2 *= 32
            x2 += self.game.resolution[0] // 2
            y2 += self.game.resolution[1] // 2

            x2 -= 16
            y2 += 32
            # x2 += 16
            # y2 += 16

            y2 = self.game.resolution[1] - y2
            self.game.display.blit(self.sprite, (x2, y2))

class Mode(Object):

    def input_start(self, arg):
        self.output = None

    def input_changemode(self, arg):
        self.game.state_args = []
        self.game.switch_state(self.keyvalues["Mode"])
        self.output = arg

    def game_state_changed(self, to, res):
        if not hasattr(self, "output"):
            self.output = None
        if to == "Load data state":
            self.game.objects.remove(self)
            self.game.LogInfo("Killed %s" % (self.name))
        
        elif to == "Main game state":
            if self.output:
                target, input, _ = self.decode_output(self.output, ";")
                arg = self.game.state_result
                self.trigger_output(target, input, arg)
                self.output = None

class Equal(Object):

    def input_check(self, arg):
        if arg == self.keyvalues["value"]:
            self.trigger_output("OnTrue")
        else:
            self.trigger_output("OnFalse")

class ChangeLevel(Object):

    def input_start(self, arg):
        self.arg = None

    def input_change(self, arg):
        self.arg = arg
        self.game.level = int(self.keyvalues["level"]) - 1
        
        self.game.switch_state("Load data state")
        # self.game.player.pos = [float(arg[0:3].strip('0')), float(arg[3:6].strip('0'))]
        # print("ChangeLevel input_change!!! ============", self.name, arg)

    def game_state_changed(self, to, res):
        # print("ChangeLevel game_state_changed!!! ============== ", self.name, self.arg, to)
        if to == "Load data state":
            if self.arg is not None:
                # My time has come
                self.game.player.pos = [int(self.arg[:3]), int(self.arg[3:])]
                self.game.objects.remove(self)

class Persistent(Object):

    def input_set(self, arg):
        self.game.persistent_values[int(self.keyvalues["variable"])] = arg

    def input_checkequal(self, arg):
        if self.game.persistent_values[int(self.keyvalues["variable"])] == arg:
            self.trigger_output("Equal")
        else:
            self.trigger_output("NotEqual")

def mini(*a):
    best = float("+inf")
    besti = None
    for i in range(len(a)):
        if a[i] < best:
            besti = i
            best = a[i]
    return besti

NAME2OBJTYPE = {
    "<none>": Object, "music": Music, "trigger_once": TriggerOnce, "textbox": Textbox, "player_move": PlayerMove,
    "trigger_multiple": TriggerMultiple, "equip": Equip, "broadcaster": Broadcaster, "merge": Merge, "sound": Sound,
    "interactible": Interactible, "mode": Mode, "equal": Equal, "changelevel": ChangeLevel, "persistent": Persistent
}
