# This contains a bunch of information describing the different
# game types pydance supports.

class GameType:
  def __init__(self, **args):
    self.width = 64
    self.dirs = ["l", "d", "u", "r"]
    self.players = 2
    self.couple = False
    self.double = False
    self.__dict__.update(args)
    self.left_off = (640 / self.players - self.width * len(self.dirs)) / 2
    self.sprite_center = 320 / self.players
    self.player_offset = 640 / self.players

GAMES = {
  "SINGLE": GameType(),
  "COUPLE": GameType(couple = True),
  "6PANEL": GameType(players = 1, dirs = ["l", "k", "d", "u", "z", "r"]),
  "8PANEL": GameType(players = 1, dirs = ["w", "l", "k", "d", "u", "z", "r", "g"]),
  }

COUPLE = [mode for mode in GAMES if GAMES[mode].couple]
DOUBLE = [mode for mode in GAMES if GAMES[mode].double]
