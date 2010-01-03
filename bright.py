#!/usr/bin/env python

import curses

"""
      A program to adjust display brightness via ACPI from your terminal.
"""
__author__  = "Neil (mace033@gmail.com)"
__license__ = "GPLv2"

class Brightness:
   BRIGHTNESS_FN = '/proc/acpi/video/VGA/LCD/brightness'
   def __init__(self):
      #self.vals = [100, 87, 75, 50, 37, 25, 12, 0]
      self.vals = [0, 12, 25, 37, 50, 75, 87, 100]

      try:
         self.file = open(self.BRIGHTNESS_FN, 'r')
         s = self.file.readlines()
         self.file.close()
         v = int(s[1].split(' ')[1])

         self.idx = self.vals.index(v)
      except:
         self.idx = self.vals[len(self.vals)-1]
         self.set()

   def set(self):
      self.file = open(self.BRIGHTNESS_FN, 'w')
      n = str(self.vals[self.idx])
      s = self.file.write(n)
      self.file.close()

   def up(self):
      self.idx = self.idx + 1
      if self.idx >= len(self.vals):
         self.idx = len(self.vals) - 1
      self.set()

   def down(self):
      self.idx = self.idx - 1
      if self.idx <= 0:
         self.idx = 0
      self.set()

class CScreen:
   def __init__(self, title="Curses Screen"):
      self.stdscr = curses.initscr()
      self.stdscr.keypad(1)
      self.stdscr.addstr(title, curses.A_REVERSE)
      curses.noecho()
      curses.cbreak()

   def show_pct(self,n):
      self.stdscr.addstr(1,0,"[")
      for i in xrange(25):
         if i < n/4:
            self.stdscr.addstr("+")
         else:
            self.stdscr.addstr(" ")
      self.stdscr.addstr("]")
      if n != 0:
         pct = "%3.0d%%" % (n)
      else:
         pct = "  0%"
      self.stdscr.addstr(pct)

   def prints(self, s):
      s = str(s)
      self.stdscr.addstr(s)

   def getch(self):
      return self.stdscr.getch()

   def close(self):
      curses.echo()
      curses.nocbreak()
      self.stdscr.keypad(0)
      curses.endwin()

def main():
   b = Brightness()
   cs = CScreen('[Brightness v1.0] Use arrow keys to adjust brightness (q to quit)\n')
   n = b.vals[b.idx]
   cs.show_pct(n)
   err = False
   while 1:
      c = cs.getch()
      try:
         if c == curses.KEY_UP or c == curses.KEY_RIGHT or c == 106:
            b.up()
         elif c == curses.KEY_DOWN or c == curses.KEY_LEFT or c == 107:
            b.down()
         elif c == ord('q'):
            break
      except IOError:
         err = True
         break
      n = b.vals[b.idx]
      cs.show_pct(n)
   cs.close()
   if err:
      print("Error: Failed to write to brightness file '%s'.  Are you root?" % 
         (Brightness.BRIGHTNESS_FN))
      
if __name__ == "__main__":
   main()
