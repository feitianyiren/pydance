import os, random, pygame

from constants import *

class AbstractArrow(pygame.sprite.Sprite):

  # Assist mode sound samples
  samples = {}
  for d in ["u", "d", "l", "r"]:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-" + d + ".ogg"))

  def __init__(self, arrow, curtime, player, song):
    pygame.sprite.Sprite.__init__(self)

    self.dir = arrow.dir

    # NB - Making a new surface, then blitting the image in place, is 20%
    # slower than calling image.convert() (and is longer to type).
    self.image = arrow.image.convert()

    self.width = player.game.width
    self.battle = song.battle
    self.rect = self.image.get_rect()
    self.rect.left = arrow.left

    if mainconfig['assist'] and self.dir in ArrowSprite.samples:
      self.sample = ArrowSprite.samples[self.dir]
    else: self.sample = None

    if player.scrollstyle == 2:
      self.top = 240 - player.game.width / 2
      self.bottom = random.choice([748, -276])
      if self.top < self.bottom:
        self.suddenzone = 480 - int(64.0 * player.sudden)
        self.hiddenzone = 236 + int(64.0 * player.hidden)
      else:
        self.suddenzone = int(64.0 * player.sudden) 
        self.hiddenzone = 236 - int(64.0 * player.hidden)
    elif player.scrollstyle == 1:
      self.top = 352
      self.bottom = -128
      self.suddenzone = int(64.0 * player.sudden)
      self.hiddenzone = 352 - int(64.0 * player.hidden)
    else:
      self.top = 64
      self.bottom = 576
      self.suddenzone = 480 - int(64.0 * player.sudden)
      self.hiddenzone = 64 + int(64.0 * player.hidden)

    self.spin = player.spin
    self.scale = player.scale
    self.speed = player.speed
    self.accel = player.accel
    self.battle = song.battle

    self.diff = self.top - self.bottom
    self.baseimage = self.image

    self.goalcenterx = self.rect.centerx
    if self.battle:
      self.rect.left = 320 - int(player.game.width *
                                 (len(player.game.dirs) / 2.0 -
                                  player.game.dirs.index(self.dir)))
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  def calculate_beats(self, curtime, endtime, curbpm, lbct):
    beatsleft = 0
    if len(lbct) == 0:
      onebeat = 60.0 / curbpm
      doomtime = endtime - curtime
      beatsleft = doomtime / onebeat
    else:
      oldbpmsub = [curtime, curbpm]
      for bpmsub in lbct:
        if bpmsub[0] <= endtime:
          onefbeat = 60.0 / oldbpmsub[1]
          bpmdoom = bpmsub[0] - oldbpmsub[0]
          beatsleft += bpmdoom / onefbeat
          oldbpmsub = bpmsub
        else: break

      onefbeat = 60.0 / oldbpmsub[1]
      bpmdoom = endtime - oldbpmsub[0]
      beatsleft += bpmdoom / onefbeat

    return beatsleft

  def update(self, curtime, curbpm, lbct):
    if self.sample and curtime >= self.timef1:
      self.sample.play()
      self.sample = None

  def scale_spin_battle(self, image, top, pct):
    if self.scale != 1:
      if self.scale < 1: # Shrink
        new_size = [pct * i for i in self.image.get_size()]
      else: # Grow
        new_size = [i - pct * i for i in image.get_size()]
      new_size = [max(0, i) for i in new_size]
      image = pygame.transform.scale(image, new_size)
    
    if self.spin:
      image = pygame.transform.rotate(image, top - 64)

    rect = image.get_rect()
    rect.top = top

    if self.battle:
      if pct > 4.5 / 6: rect.centerx = self.origcenterx
      elif pct > 2.0 / 6:
        p = (pct - 2.0/6) / (2.5 / 6)
        rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: rect.centerx = self.goalcenterx
    else: rect.centerx = self.centerx

    if image.get_size() != (0, 0):
      image.set_colorkey(image.get_at([0, 0]))

    return rect, image

  def kill(self):
    pygame.sprite.Sprite.kill(self)
    if self.sample: self.sample.play()

class ArrowSprite(AbstractArrow):
  def __init__ (self, arrow, curtime, endtime, player, song):
    AbstractArrow.__init__(self, arrow, curtime, player, song)
    self.hold = False
    self.endtime = endtime

  def update(self, curtime, curbpm, lbct):
    AbstractArrow.update(self, curtime, curbpm, lbct)

    if curtime > self.endtime + (240.0/curbpm):
      self.kill()
      return

    if curbpm < 0.0001: return # We're stopped
    # We can't just keep going if we're stopped, because the bpm change to
    # 0 is out of lbct, and so we only use curbpm, which is 0, meaning
    # we always end up at the top.

    top = self.top

    beatsleft = self.calculate_beats(curtime, self.endtime, curbpm, lbct)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft * self.speed - 8)))
      speed = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed = self.speed

    top = top - int(beatsleft / 8.0 * speed * self.diff)

    self.image = self.baseimage
  
    if top > 480: top = 480

    pct = abs(float(top - self.top) / self.diff)

    self.rect, self.image = self.scale_spin_battle(self.baseimage, top, pct)

    alp = 256
    if self.top < self.bottom: 
      if self.rect.top > self.suddenzone:
        alp = 256 - 4 * (self.rect.top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - self.rect.top) / self.speed
    else:
      if self.rect.top < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - self.rect.top) / self.speed
      elif self.rect.top > self.hiddenzone:
        alp = 256 - 4 * (self.rect.top - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    self.image.set_alpha(alp)

class HoldArrowSprite(AbstractArrow):
  def __init__ (self, arrow, curtime, times, player, song):
    AbstractArrow.__init__(self, arrow, curtime, player, song)
    self.timef1 = self.endtime = times[1]
    self.hold = True
    self.timef2 = times[2]
    if self.timef2 is None: self.timef2 = self.timef1

    self.broken = True

    self.top_image = pygame.surface.Surface([self.width, self.width / 2])
    self.top_image.blit(self.image, [0, 0])
    self.top_image.set_colorkey(self.top_image.get_at([0, 0]), RLEACCEL)

    self.bottom_image = pygame.surface.Surface([self.width, self.width / 2])
    self.bottom_image.blit(self.image, [0, -self.width / 2])
    self.bottom_image.set_colorkey(self.bottom_image.get_at([0, 0]), RLEACCEL)

    self.center_image = pygame.surface.Surface([self.width, 1])
    self.center_image.blit(self.image, [0, -self.width / 2 + 1])

  def update(self, curtime, curbpm, lbct):
    AbstractArrow.update(self, curtime, curbpm, lbct)

    if curtime > self.timef2:
      self.kill()
      return

    if curbpm < 0.0001: return # We're stopped

    beatsleft_top = self.calculate_beats(curtime, self.timef1, curbpm, lbct)
    beatsleft_bot = self.calculate_beats(curtime, self.timef2, curbpm, lbct)

    if self.accel == 1:
      p = min(1, max(0, -0.125 * (beatsleft_top * self.speed - 8)))
      speed_top = 3 * p * self.speed + self.speed * (1 - p)
      p = min(1, max(0, -0.125 * (beatsleft_bottom * self.speed - 8)))
      speed_bottom = 3 * p * self.speed + self.speed * (1 - p)
    elif self.accel == 2:
      p = min(1, max(0, -0.125 * (beatsleft_top * self.speed - 8)))
      speed_top = p * self.speed / 2.0 + self.speed * (1 - p)
      p = min(1, max(0, -0.125 * (beatsleft_bottom * self.speed - 8)))
      speed_bottom = p * self.speed / 2.0 + self.speed * (1 - p)
    else: speed_top = speed_bottom = self.speed

    if self.bottom > self.top:
      top = self.top - int(beatsleft_top / 8.0 * self.diff * speed_top)
      bottom = self.top - int(beatsleft_bot / 8.0 * self.diff * speed_bottom)
    else:
      top = self.top - int(beatsleft_bot / 8.0 * self.diff * speed_top)
      bottom = self.top - int(beatsleft_top / 8.0 * self.diff * speed_bottom)

    if bottom > 480: bottom = 480
    if top > 480: top = 480

    if self.top < self.bottom:
      bottom = max(64, bottom)
      top = max(64, top)

    pct = abs(float(top - self.top) / self.diff)
    
    holdsize = abs(bottom - top)
    if holdsize < 0: holdsize = 0
    image = pygame.Surface([self.width, holdsize + 64])
    h_img = pygame.transform.scale(self.center_image, [self.width, holdsize])
    image.blit(h_img, [0, self.width / 2])
    image.blit(self.top_image, [0, 0])
    image.blit(self.bottom_image, [0, holdsize + self.width / 2])

    self.rect, self.image = self.scale_spin_battle(image, top, pct)

    alp = 256
    if self.top < self.bottom: 
      if self.rect.top > self.suddenzone:
        alp = 256 - 4 * (self.rect.top - self.suddenzone) / self.speed
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - self.rect.top) / self.speed
    else:
      if self.rect.bottom < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - self.rect.bottom) / self.speed
      elif self.rect.bottom > self.hiddenzone:
        alp = 256 - 4 * (self.rect.bottom - self.hiddenzone) / self.speed

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    if self.broken and (curtime > self.timef1+(0.00025*(60000.0/curbpm))):
      alp /= 2

    self.image.set_alpha(alp)