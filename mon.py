#!/usr/bin/env python
import sys
import optparse
import time
import signal
from datetime import datetime, timedelta

"""
   A system monitoring program for terminals.  Monitors:
      power usage
      cpu usage
      mem usage
      monitor temperature

   @TODO: 
      monitor networking usage
      remove hardcoded file names
      use signals or threads instead of sleep
      use classes?
"""
__author__  = "Neil (mace033@gmail.com)"
__license__ = "GPLv2"


TITLE_WIDTH = 17
CHART_WIDTH = 30

class TermColors:
   PURPLE = '\033[95m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   DEFAULT = '\033[0m'
   CLEAR_SCREEN = '\x1b[H\x1b[2J'

   def disable(self):
      self.PURPLE = ''
      self.BLUE = ''
      self.GREEN = ''
      self.YELLOW = ''
      self.RED = ''
      self.DEFAULT = ''
      self.CLEAR_SCREEN = ''

def getch():
   import tty, termios
   fd = sys.stdin.fileno()
   old_settings = termios.tcgetattr(fd)
   try:
      tty.setraw(sys.stdin.fileno())
      ch = sys.stdin.read(1)
   finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
   return ch

def get_stats(ifn):
   try:
      ilines = open(ifn, 'r').readlines()
   except IOError:
      return {}

   info_dict = dict()
   for l in ilines:
       if len(l) == 0:
         continue
       tmp = l.strip().split(":")
       if len(tmp) < 2:
          info_dict['foo'] = tmp[0].lstrip()
       else:
          info_dict[tmp[0].strip()] = tmp[1].lstrip()
       
   return info_dict

def dump_stats_dict(d):
   print '\n'.join([str(k) + ": " + str(v) for k,v in d.items()])

def do_every(secs, func, *args):
   while True:
      func(*args)
      time.sleep(secs)

def get_chart(curr, max=100):
   bars = int(float(curr) / max * CHART_WIDTH)
   bar = "[" + TermColors.GREEN + ''.join(['+' for i in range(bars)])
   bar += TermColors.RED + ''.join(['-' for i in range(CHART_WIDTH - bars)])\
      + TermColors.YELLOW +"]"
  
   return bar 

def print_pct(format, *args):
   print TermColors.YELLOW+format % (args)+TermColors.DEFAULT

def print_battery_stats(info_dict, verbose):
   if not info_dict:
      return
   
   if verbose:
      dump_stats_dict(info_dict)

   last_capacity = float(info_dict.get('last full capacity', 
      '0.0 mAh').split('mAh')[0])
   design_capacity = float(info_dict.get('design capacity', 
      '1.0 mAh').split('mAh')[0])
   remaining_capacity = float(info_dict.get('remaining capacity', 
      '0.0 mAh').split('mAh')[0])
   present_rate = float(info_dict.get('present rate', 
      '1.0 mA').split('mA')[0])

   pct_remain = remaining_capacity / last_capacity * 100.0
   pct_age = last_capacity / design_capacity * 100.0
   end_state = None
   if info_dict['charging state'] == 'discharging':
      # present rate is the drain rate
      end_state = "empty"
      try:
         secs_remain = remaining_capacity / present_rate * 3600
         secs_total = last_capacity / present_rate * 3600
      except ZeroDivisionError:
         secs_remain = 1.0
         secs_total = 1.0
   else:
      # present rate is the charge rate
      end_state = "full"
      try:
         secs_remain = (last_capacity - remaining_capacity) / present_rate * 3600
         secs_total = last_capacity / present_rate * 3600
      except ZeroDivisionError:
         secs_remain = 0.0
         secs_total = 105.0

   time_remain = timedelta(seconds=long(secs_remain)) 
   time_total = timedelta(seconds=long(secs_total)) 
   print_pct("%s %s %02.2f%%", "Power remaining:".ljust(TITLE_WIDTH), 
      get_chart(pct_remain, 100), pct_remain)
   print_pct("%s %s %s / %s", ("Time until " + end_state + ":").ljust(TITLE_WIDTH), 
      get_chart(secs_remain, secs_total), time_remain, time_total)
   print_pct("%s %s %02.2f%%", "Battery age:".ljust(TITLE_WIDTH), 
      get_chart(pct_age, 100), pct_age)

def get_mem_stats(ifn = "/proc/meminfo"):
   slines = open(ifn, 'r').readlines()

   stats_dict = dict()
   for l in slines:
       tmp = l.strip().split(":")
       stats_dict[tmp[0]] = tmp[1].lstrip()

   return stats_dict
 
def print_mem_stats(stats_dict, verbose=False):
   if verbose:
      dump_stats_dict(stats_dict)
   mem_total = int(stats_dict['MemTotal'].strip("kB")) / 1024
   mem_free = int(stats_dict['MemFree'].strip("kB")) / 1024
   swap_total = int(stats_dict['SwapTotal'].strip("kB")) / 1024
   swap_free = int(stats_dict['SwapFree'].strip("kB")) / 1024

   print_pct("%s %s %dmB / %dmB", "Free memory:".ljust(TITLE_WIDTH), 
      get_chart(mem_free, mem_total), mem_free, mem_total)
   print_pct("%s %s %dmB / %dmB", "Free swap:".ljust(TITLE_WIDTH), 
      get_chart(swap_free, swap_total), swap_free, swap_total)

def get_cpu_stats(ifn = "/proc/stat"):
   last_stats_dict = None
   while True:
      slines = open(ifn, 'r').readlines()
      stats_type_list = ['procs_running', 'procs_blocked',]
      stats_dict = dict()

      for l in slines:
         stats = l.split()
         stat_type = stats.pop(0)
         if l.startswith('cpu'):
            # cpu usage
            total_usage = long(stats[0]) + long(stats[1]) + long(stats[2])
            total = long(stats[0]) + long(stats[1]) + long(stats[2]) + long(stats[3])
            if last_stats_dict:
               last_stats = last_stats_dict[stat_type]
               stats_dict[stat_type] = ((total_usage, total), last_stats[0])
            else:
               stats_dict[stat_type] = ((total_usage, total), (0, 0))
         else:
            # other stats
            if stat_type in stats_type_list:
               stats_dict[stat_type] = int(stats[0])

      yield stats_dict
      last_stats_dict = stats_dict

def print_cpu_stats(stats_dict, verbose=False):
   if verbose:
      dump_stats_dict(stats_dict)
   for k,v in stats_dict.items():
      if k.startswith('cpu'):
         curr = stats_dict[k][0]
         prev = stats_dict[k][1]
         usage = curr[0] - prev[0]
         total = curr[1] - prev[1]
         usage_pct = float(usage)/total * 100
         print_pct("%s %s %d%%", (k + " usage:").ljust(TITLE_WIDTH), 
            get_chart(usage_pct, 100), usage_pct)

def print_header():
   now = datetime.now()
   print "%s[%s]%s" % (TermColors.BLUE, now.strftime('%a %Y-%m-%d %H:%M:%S'),
      TermColors.DEFAULT)

def pluralize(n, word):
   suffix = 's'
   if word[-1] == 'y':
      suffix = 'ies'
      word = word[:-1]
   if n > 1:
      return word + suffix
   return word

def print_proc_info(cpu_info_dict, verbose):
   if verbose:
      dump_stats_dict(cpu_info_dict)

   cpus = 1
   cores_per_cpu = 1
   if cpu_info_dict.get('physical id'):
      cpus = int(cpu_info_dict['physical id']) + 1
   if cpu_info_dict.get('cpu cores'):
      cores_per_cpu = int(cpu_info_dict['cpu cores'])

   total_cores = cpus * cores_per_cpu
   tmp = cpu_info_dict['model name'].split()
   if len(tmp) > 3:
      model_name = ' '.join(tmp[:4])
   else:
      model_name = cpu_info_dict['model name']

   print "%s[%s]%s" % (TermColors.BLUE, 
      "%s @ %dMHz | %d %s, %d cpu %s" % (model_name,
      float(cpu_info_dict['cpu MHz']), cpus, pluralize(cpus, 'proc'), 
      total_cores, pluralize(total_cores, 'core')), TermColors.DEFAULT)
   print "%s[Load: %s | Temp: %s]%s" % (TermColors.BLUE, 
      cpu_info_dict['loadavg'], cpu_info_dict['temperature'],
      TermColors.DEFAULT)
   
def print_stats(verbose=False, cpu_stats_gen=get_cpu_stats()):
   batt_info_dict = get_stats("/proc/acpi/battery/BAT1/info") 
   batt_info_dict.update(get_stats("/proc/acpi/battery/BAT1/state"))

   cpu_info_dict = get_stats("/proc/cpuinfo") 
   cpu_info_dict.update(get_stats("/proc/acpi/thermal_zone/THRM/temperature"))
   try:
      load_avg = ' '.join(open("/proc/loadavg", 'r').readlines()[0].split()[:3])
   except IOError:
      load_avg = "n/a n/a n/a"
   cpu_info_dict['loadavg'] = load_avg

   cpu_stats_dict = cpu_stats_gen.next()
   mem_stats_dict = get_mem_stats()

   print TermColors.CLEAR_SCREEN
   print_header()
   print_proc_info(cpu_info_dict, verbose)
   print_battery_stats(batt_info_dict, verbose)
   print_cpu_stats(cpu_stats_dict, verbose)
   print_mem_stats(mem_stats_dict, verbose)

   print "\nCtrl-C to exit..."

def handle_break(signum, frame):
   print "Monitoring interrupted, exiting..."
   sys.exit(0)

def main():
   parser = optparse.OptionParser()
   parser.add_option("-v", "--verbose", help="Turn on verbosity.", 
      action="store_true")
   parser.add_option("-s", "--seconds", help="Get stats every N seconds.", 
      default=float(5))
   parser.add_option("-o", "--once", help="Run once and exit, do not loop.", 
      action="store_true")
   opts, args = parser.parse_args()
   verbose = opts.verbose

   signal.signal(signal.SIGINT, handle_break)

   if not opts.once:
      do_every(float(opts.seconds), print_stats, verbose)
   else:
      print_stats(verbose)

if __name__ == "__main__":
   main()
