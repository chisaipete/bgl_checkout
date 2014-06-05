
class game_db():
  def __init__(self):
    self.connection = sqlite3.connect('bgl.db', check_same_thread=False)
    #https://www.dropbox.com/s/6fcg3ketplcau2j/bgl.db
    self.cursor = self.connection.cursor()
    
  def execute(self, command=''):
    self.cursor.execute(command)
    
  def get_history(self):
    self.execute("""select * from history""")
    return self.fetchall()
  
  def get_inventory(self):
    self.execute("""select * from inventory""")
    return self.fetchall()
  
  def close(self):
    self.connection.close()
    
  
if __name__ == '__main__':
  db = game_db()
  if db.check_db():
    print 'database ready'
    
  print 'grabbing table contents'
  history = db.get_history()
  inventory = db.get_inventory()
  db.close()
  