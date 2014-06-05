import unittest
from checkout import game_db
from checkout import barcode_scanner, BARCODE_TYPE
import Queue
from pyglet.window import key

class checkoutTest(unittest.TestCase): 
  
  def setUp(self):
    print "creating database"
    self.db = game_db('test.db')
    self.db.destroy_db()
    self.db.initialize_db()
    print "starting barcode scanner"
    self.buffer = Queue.Queue()
    self.bcs = barcode_scanner(self.buffer, self.bcs_callback)
    self.bcs.start()
    self.bc_id = None
    self.bc_value = None
    
  def bcs_callback(self, barcode_id, value):
    self.bc_id = barcode_id
    self.bc_value = value
    
  def tearDown(self):
    self.bc_id = None
    self.bc_value = None
    print "stopping barcode scanner"
    self.bcs.stop()
    self.bcs.join()
    print "clearing database"
    self.db.destroy_db()
    self.db.close()
    
    
  def test_db_checkNoDuplicateCO(self):
    #history is empty
    self.assertTrue(self.db.check_out('11340223', '000000000001'))
    self.assertFalse(self.db.check_out('11340223', '000000000001'))
    
  def test_db_checkNoDuplcateCI(self):
    #history is empty
    self.assertFalse(self.db.check_in('000000000001'))
    self.assertTrue(self.db.check_out('11340223', '000000000001'))
    self.assertTrue(self.db.check_in('000000000001'))
    
  def test_db_historyValid(self):
    self.assertEqual('[]', self.db.get_history())
    self.db.check_out('11340223', '000000000001')
    self.assertNotEqual('[]', self.db.get_history())
    split_history = self.db.get_history().split("u'")
    history = "u'".join([split_history[0], split_history[-1]])
    self.assertEqual("[(1, 11340223, u'-4713-11-24 12:00:00', 0)]", history)
    
#   def test_db_inventoryValid(self):
#     raise NotImplementedError
  
  def test_bcs_detectWWID(self):
    for k in [key.LCTRL, key.B, key._1, key._1, key._3, key._4, key._0, key._2, key._2, key._3, key.LCTRL, key.C, key.RETURN]:
      self.buffer.put(k)
      self.bcs.buffer_ready_flag.set()
      while self.bcs.buffer_ready_flag.isSet():
        pass      
    while self.bc_id == None:
      pass
    self.assertEqual(BARCODE_TYPE.WWID, self.bc_id)
    self.assertEqual(11340223, self.bc_value)
  
  def test_bcs_detectBARCODE(self):
    for k in [key.LCTRL, key.B, key._0, key._0, key._0, key._0, key._0, key._0, key._0, key._0, key._1, key._3, key._3, key._7, key.LCTRL, key.C, key.RETURN]:
      self.buffer.put(k)
      self.bcs.buffer_ready_flag.set()
      while self.bcs.buffer_ready_flag.isSet():
        pass      
    while self.bc_id == None:
      pass
    self.assertEqual(BARCODE_TYPE.BARCODE, self.bc_id)
    self.assertEqual(1337, self.bc_value)
  
  def test_bcs_detectOTHER(self):
    for k in [key._0, key._0, key._0, key._0, key._0, key._0, key._0, key._0, key._1, key._3, key._3, key._7, key.RETURN]:
      self.buffer.put(k)
      self.bcs.buffer_ready_flag.set()
      while self.bcs.buffer_ready_flag.isSet():
        pass      
    self.assertEqual(None, self.bc_id)
    self.assertEqual(None, self.bc_value)
  
if __name__ == '__main__':
  unittest.main()