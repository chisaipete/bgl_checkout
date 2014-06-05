import sqlite3, urllib2, pyglet, Queue, threading
import xml.etree.cElementTree as et

import pprint
pp = pprint.PrettyPrinter()

def enum(**enums):
  '''Function to create an enumerated type object'''
  return type('Enum', (), enums)


class bgg_api():
  '''Represents a HTML based XML API for BoardGameGeek.com'''
  def __init__(self, username='ddg_or_bgl'):
    '''Set up instance variable username and selects which version of api's base url to use'''
    self.api_base_url = 'http://www.boardgamegeek.com/xmlapi/'
    # self.api_version2_base_url = 'http://www.boardgamegeek.com/xmlapi2/'
    self.username = username
    
  def search(self):
    '''Unimplemented'''
    pass
  
  def boardgame(self):
    '''Unimplemented'''
    pass
  
  def get_owned_collection(self):
    '''Returns all objects in the BGG collection associated with self.username that have the attribute owned'''
    request_url = '/'.join([self.api_base_url, 'collection', self.username+'?own=1'])
    xml = et.XML(urllib2.urlopen(request_url).read())
    return [(int(item.attrib['objectid']),item.find('name').text) for item in xml]
  
  def thread(self):
    '''Unimplemented'''
    pass
  
  def geeklist(self):
    '''Unimplemented'''
    pass
  

class game_db():
  '''Represents the database which contains inventory and check in/out history'''
  def __init__(self, name='bgl.db'):
    '''Create connection to sqlite database file on disk and initialize cursor to perform actions'''
    self.connection = sqlite3.connect(name, check_same_thread=False)
    #https://www.dropbox.com/s/6fcg3ketplcau2j/bgl.db
    self.cursor = self.connection.cursor()
    
  def execute(self, command=''):
    ''''''
    self.cursor.execute(command)
  
  def fetchone(self):
    ''''''
    return self.cursor.fetchone()

  def fetchall(self):
    ''''''
    return self.cursor.fetchall()
  
  def commit(self):
    ''''''
    self.connection.commit()
  
  def close(self):
    ''''''
    self.connection.close()
    
  def initialize_db(self):
    ''''''
    self.execute('''create table inventory (barcode integer, bgg_id integer)''')
    self.execute('''create table history (barcode integer, wwid integer, time_out datetime, time_in datetime, auto_in integer)''')
    self.commit()
  
  def destroy_db(self):
    '''Drop the tables for inventory and history to effectively clear/reset database'''
    try:
      self.execute('''drop table inventory''')
    except sqlite3.OperationalError:
      pass
    try:
      self.execute('''drop table history''')
    except sqlite3.OperationalError:
      pass
    self.commit()
    
  def populate_inventory(self, bgg): #TODO
    '''Download current inventory and register barcode for each game in turn'''
    result = bgg.get_owned_collection()
    for game in result:
      print 'scan barcode for ', game[1]
      self.execute('''insert into inventory values({}, {})'''.format(0, game[0]))
    self.commit()
      
  def add_inventory(self, barcode):
    '''Download current inventory and register new barcodes for each new game'''
    pass  
    
  def remove_inventory(self):
    '''Remove game from database and print reminder to remove from BGG.com'''
    pass 
  
  def dump_to_csv(self, table_name='history'):
    '''Write the contents of the specified table to a csv file'''
    pass
  
  def format_table(self, table_name='history'):
    '''return the contents of the specified table as a formatted string'''
    self.execute('''select * from {}'''.format(table_name))
    return pp.pformat(self.fetchall())
    
  def reset_table(self):
    '''Reset/clear the contents of the specified table'''
    pass
    
  def check_in(self, barcode=None):
    ''''''
    #only check in if there is a history item with a time_in == 0
    self.execute('''select * from history where barcode={} and time_in=datetime('0')'''.format(barcode))
    entries = self.fetchall()
    if len(entries) != 1:
      return False
    self.execute('''update history set time_in=datetime('NOW') where barcode={}'''.format(barcode))
    self.commit()
    return True
  
  def check_out(self, wwid=None, barcode=None):
    ''''''
    #only check out if there isn't a history item with a time_in == 0
    self.execute('''select * from history where barcode={} and time_in=datetime('0')'''.format(barcode))
    entries = self.fetchall()
    if len(entries) != 0:
      return False
    self.execute('''insert into history values({}, {}, datetime('NOW'), datetime('0'), {})'''.format(barcode, wwid, 0))
    self.commit()
    return True
    
  def get_history(self):
    ''''''
    return self.format_table('history')
  
  def get_inventory(self):
    ''''''
    return self.format_table('inventory')
    
  def check_db(self):
    '''Function to sanity check that tables exist in the database'''
    self.execute("""select name from sqlite_master where type = 'table'""")
    tables = self.fetchall()
    if tables:
      return True
    else:
      return False


BARCODE_TYPE = enum(WWID = 0, BARCODE = 1)

class barcode_scanner(threading.Thread):
  ''''''
  from pyglet.window import key
  start_bc_sequence = [key.LCTRL, key.B]
  end_bc_sequence =   [key.LCTRL, key.C, key.RETURN]
  
  def __init__(self, input_buffer, ui_callback):
    ''''''
    super(barcode_scanner, self).__init__()
    self._stop = threading.Event()
    self.buffer = input_buffer  
    self.buffer_ready_flag = threading.Event()
    self.ui_callback = ui_callback
    
  def stop(self):
    ''''''
    self._stop.set()
    
  def stopped(self):
    ''''''
    return self._stop.isSet()

  def run(self):
    ''''''
    value = []
    while not self._stop.isSet():
      if self.buffer_ready_flag.isSet():
#         print "buffer ready"
        self.buffer_ready_flag.clear()
        value.append(self.buffer.get())
#         print value
        if value[:2] == self.start_bc_sequence:
#           print 'valid start sequence'
#           print value[:2]
          if value[-3:] == self.end_bc_sequence:
#             print 'valid end sequence'
#             print value[-3:]
            seq = int(''.join([self.key.symbol_string(digit)[1] for digit in value[2:-3]]))
            if len(value[2:-3]) == 8:
              #Assume 8 char code is WWID
              self.ui_callback(BARCODE_TYPE.WWID, seq)
            else:
              self.ui_callback(BARCODE_TYPE.BARCODE, seq)            
            value = []
    

class user_interface():
  ''''''
  UI_STATE = enum(START=0, WAIT_FOR_CHECKOUT=1, CHECKOUT_SUCCESS=2, CHECKOUT_FAILURE=3, CHECKIN_SUCCESS=4, CHECKIN_FAILURE=5)
  def __init__(self, db):
    ''''''
    self.db = db

#     self.window = pyglet.window.Window(fullscreen=True)
    self.window = pyglet.window.Window(width=1000, height=240)
    self.labels = []
    self.title = ''
    self.message = ''
    self.help = ''
    self.status = ''
    
    self.input_buffer = Queue.Queue()  
   
    @self.window.event
    def on_draw():
      ''''''
      self.window.clear()
      for label in self.labels:
        label.delete()
      self.labels = []
      self.labels.append(pyglet.text.Label(self.title, font_name='Verdana', font_size=24, bold=True, italic=True, x=self.window.width/2, y=self.window.height-36, anchor_x='center', anchor_y='center'))
      self.labels.append(pyglet.text.Label(self.message, font_name='Verdana', font_size=24, x=self.window.width/2, y=self.window.height-72, anchor_x='center', anchor_y='center'))
      self.labels.append(pyglet.text.Label(self.help, font_name='Verdana', font_size=24, x=self.window.width/2, y=self.window.height-108, anchor_x='center', anchor_y='center'))
      self.labels.append(pyglet.text.Label(self.status, font_name='Verdana', font_size=24, x=self.window.width/2, y=self.window.height-144, anchor_x='center', anchor_y='center'))
      for label in self.labels:
        label.draw()
    
    @self.window.event
    def on_key_press(symbol, modifier):
      ''''''
#       print symbol,modifier,hex(symbol),key.symbol_string(symbol)
      self.input_buffer.put(symbol)
      self.barcode_scanner.buffer_ready_flag.set()
   
    self.wwid = 0

  def set_title(self, title=''):
    ''''''
    self.title = title
  
  def set_message(self, message=''):
    ''''''
    self.message = message
    
  def set_help(self, h=''):
    ''''''
    self.help = h
    
  def set_status(self, status=''):
    ''''''
    self.status = status
  
  def checkout(self, wwid, game):
    ''''''
    return(self.db.check_out(wwid, game))
  
  def checkin(self, game):
    ''''''
    return(self.db.check_in(game))    
  
  def scanner_callback(self, bcid, value):
    ''''''
    if bcid == BARCODE_TYPE.WWID:#TODO: checkin checkout logic is odd, I think it needs simplification
      if self.state == self.UI_STATE.START:
        self.wwid = value
        self.set_checkout_screen()
      else:
        pass
#       elif self.state == self.UI_STATE.WAIT_FOR_CHECKOUT:
#       elif self.state == self.UI_STATE.CHECKOUT_SUCCESS:
#       elif self.state == self.UI_STATE.CHECKOUT_FAILURE:
#       elif self.state == self.UI_STATE.CHECKIN_SUCCESS:
#       elif self.state == self.UI_STATE.CHECKIN_FAILURE:
    elif bcid == BARCODE_TYPE.BARCODE:
      if self.state == self.UI_STATE.START:
        self.game = value
        print "recieved: " + str(self.game)
        if self.checkin(self.game):
          self.set_ci_success_screen()
        else:
          self.set_ci_failure_screen()
      elif self.state == self.UI_STATE.WAIT_FOR_CHECKOUT:
        self.game = value
        print "recieved: " + str(self.game)
        if self.checkout(self.wwid, self.game):
          self.set_co_success_screen()
        else:
          self.set_co_failure_screen()
      else:
        pass
#       elif self.state == self.UI_STATE.CHECKOUT_SUCCESS:
#       elif self.state == self.UI_STATE.CHECKOUT_FAILURE:
#       elif self.state == self.UI_STATE.CHECKIN_SUCCESS:
#       elif self.state == self.UI_STATE.CHECKIN_FAILURE:
    
  def set_co_success_screen(self, *kargs):
    ''''''
    print "check out success"
    pyglet.clock.unschedule(self.set_start_screen)
    self.set_message('Game successfully checked out!')
    self.set_help('')
    self.set_status('')
    self.state = self.UI_STATE.CHECKOUT_SUCCESS
    pyglet.clock.schedule_once(self.set_start_screen, 2.0) #reset to start screen
    
  def set_co_failure_screen(self, *kargs):
    ''''''
    print "check out failure"
    pyglet.clock.unschedule(self.set_start_screen)
    self.set_message('Game already checked out!  Auto check-in and checking out to {}'.format(self.wwid))
    self.set_help('')
    self.set_status('')
    self.state = self.UI_STATE.CHECKOUT_FAILURE
    pyglet.clock.schedule_once(self.set_start_screen, 2.0) #reset to start screen
    
  def set_ci_success_screen(self, *kargs):
    ''''''
    print "check in success"
    pyglet.clock.unschedule(self.set_start_screen)
    self.set_message('Game successfully checked in!')
    self.set_help('')
    self.set_status('')
    self.state = self.UI_STATE.CHECKIN_SUCCESS
    pyglet.clock.schedule_once(self.set_start_screen, 2.0) #reset to start screen
    
  def set_ci_failure_screen(self, *kargs):
    ''''''
    print "check in failure"
    pyglet.clock.unschedule(self.set_start_screen)
    self.set_message('Game already checked in!')
    self.set_help('')
    self.set_status('')
    self.state = self.UI_STATE.CHECKIN_FAILURE
    pyglet.clock.schedule_once(self.set_start_screen, 2.0) #reset to start screen
    
  def set_checkout_screen(self, *kargs):
    ''''''
    print "waiting for game barcode"
    pyglet.clock.unschedule(self.set_start_screen)
    self.set_message('Scan game to check out to {}'.format(self.wwid))
    self.set_help('')
    self.set_status('Screen will timeout in 10 seconds')
    self.state = self.UI_STATE.WAIT_FOR_CHECKOUT
    pyglet.clock.schedule_once(self.set_start_screen, 10.0) #reset to start screen    

  def set_start_screen(self, *kargs):
    ''''''
    print "start screen, waiting for scan"
    self.set_title('DDG OR Board Game Library Checkout')
    self.set_message('Please scan the Barcode on your ID card')
    self.set_help('Or scan the Barcode of the game to check in')
    self.set_status('')
    self.wwid = 0
    self.game = 0
#     self.gameList_update()
    self.state = self.UI_STATE.START
    pp.pprint(self.db.get_history())  
  
  
if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Checkout System for DDG OR BGL, using BoardGameGeek')
  parser.add_argument('-i', '--init_db', help='reset the inventory and history db', action='store_true', default=False)
  parser.add_argument('-a', '--add_game', help='add games to inventory', action='store_true', default=False)
  parser.add_argument('-r', '--remove_game', help='remove games from inventory', action='store_true', default=False)
  parser.add_argument('-c', '--clear_history', help='reset history table', action='store_true', default=False)
  parser.add_argument('-d', '--dump_barcodes', help='dump barcodes of deleted games', action='store_true', default=False)
  args = parser.parse_args()
  
  bgg = bgg_api()
  
  if args.init_db:
    print 'initializing database'
    db = game_db()
    db.destroy_db()
    db.initialize_db()
    pp.pprint(db.get_inventory())
    pp.pprint(db.get_history())
    db.populate_inventory(bgg)
    db.close() 
       
  db = game_db()
  if db.check_db():
    print 'database ready' 
  
  print 'initializing ui'
  ui = user_interface(db)    
  ui.set_start_screen()

  print 'initializing barcode scanner'  
  bc_scanner = barcode_scanner(ui.input_buffer, ui.scanner_callback)
  ui.barcode_scanner = bc_scanner
  bc_scanner.start() #start BCS

  pyglet.app.run() #start GUI
  
  print "ui closed"
  
  bc_scanner.stop()
  bc_scanner.join()
  
  print "scanner closed"
      
  db.close()  

