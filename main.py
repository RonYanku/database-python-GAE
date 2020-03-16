# This project's readme file on github: https://github.com/RonYanku/database-python-GAE/blob/master/README.md
# contains an explanation of the logic in this database, and some color on the four Models used.

import webapp2

from google.appengine.ext import ndb

####################################    helper functions    ##########################################

# empties out the given model
def emptyModel(modelName):
    for entity in modelName.query().fetch():
        entity.key.delete()
        
# updates the occurence of a given value. also expects a num that is either 1 or -1,
# and either ups or lowers the occurence of the given value accordingly        
def updateOccurences(valueName,num):
    occ = ValueOccurence.query(ValueOccurence.value == valueName).get()
    if occ:
        occ.occurence=occ.occurence+num
        occ.put()    

# finds the request that has isLastRequest set to true in the given model, and change it to false, 
# due to a new request. updates seqId of the new entity and reutrns it.
def fixSettingOrder(modelName):
        priorReq = modelName.query(modelName.isLastRequest==True).get()
        if priorReq:
            newSeqId = priorReq.seqId + 1
            priorReq.isLastRequest = False
            priorReq.put()
#       if no prior request exists then this is the first one     
        else:
            newSeqId = 1
        return newSeqId                 

####################################    models    ##################################################
# More color on the models can be found at 
# https://github.com/RonYanku/database-python-GAE/blob/master/README.md

# This model contains the variables in the db
class Item(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.StringProperty()
  
# this model contains the values that have at least 1 occurence in the db  
class ValueOccurence(ndb.Model):
    value = ndb.StringProperty()
    occurence = ndb.IntegerProperty() 

# This model represents the history logs of the set/unset commands.
class SettingHistory(ndb.Model):
    seqId = ndb.IntegerProperty()
    name = ndb.StringProperty()
    value = ndb.StringProperty()
    priorValue = ndb.StringProperty()
    isLastRequest = ndb.BooleanProperty()

# This class entities would be set/unset commands that were undone
class PotentialRedos(ndb.Model):
    seqId = ndb.IntegerProperty()
    name = ndb.StringProperty()
    value = ndb.StringProperty()
    isLastRequest = ndb.BooleanProperty()    

##########################################    handlers    ##########################################



class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hi, how are you?')


# Handles the get requests. expects the name of te variable to get
class GetHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        name = self.request.get('name')
        result = Item.query(Item.name == name).get()
        if result:
            self.response.write(result.value)
        else:
            self.response.write('None')



# Handles the set requests, expects name and value        
class SetHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        itemName = self.request.get('name')
        itemValue = self.request.get('value')
        
#       empty PotentialRedos becuase we got a set command
        reqToDel = PotentialRedos.query(PotentialRedos.isLastRequest==True).get()
        if reqToDel:  
            emptyModel(PotentialRedos)
        
        newSeqId = fixSettingOrder(SettingHistory)
         
#       check if item with this name already exists in the Items model
        item = Item.query(Item.name == itemName).get()
        if item:
#           lower the occurnce of the previous value of this item
            oldValue = item.value
            updateOccurences(oldValue,-1)

            item.value=itemValue
#           put the variable in the Items model
            item.put()
            self.response.write(item.name + ' = ' + item.value)
           
#       item does not yet exist in the Items model    
        else:
            oldValue='None'
            newItem = Item(name=itemName,value=itemValue)
#           put the variable in the Items model    
            newItem.put()
            self.response.write(newItem.name + ' = ' + newItem.value)
            
#       updating the ValueOccurence model accordingly
        occ = ValueOccurence.query(ValueOccurence.value == itemValue).get()
        if occ:
#           value already exists in the ValueOccurence model
            occ.occurence=occ.occurence+1
            occ.put()
        else:
#           value doesn't exist in the ValueOccurence model yet
            occNew = ValueOccurence(value=itemValue,occurence=int(1))
            occNew.put()
            
#       enter the command into the history model      
        newSettingLog = SettingHistory(name=itemName, value=itemValue, priorValue=oldValue, 
                                       isLastRequest=True, seqId=newSeqId)
        newSettingLog.put()



# unsets a variable if exists in Item model. expects variable name
class UnsetHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        itemName = self.request.get('name')
#       empty PotentialRedos becuase we got a set command  
        reqToDel = PotentialRedos.query(PotentialRedos.isLastRequest==True).get()
        if reqToDel:  
            emptyModel(PotentialRedos)

        newSeqId = fixSettingOrder(SettingHistory)

        item = Item.query(Item.name == itemName).get()
        if item:
#           item found in the Item model, delete it, update occurences 
#           and enter the command into the history model      
            newSettingLog = SettingHistory(name=itemName, value='None', priorValue=item.value, 
                                           isLastRequest=True, seqId=newSeqId)
            newSettingLog.put()
#           lower the occurence by 1 in the ValueOccurence model
            updateOccurences(item.value,-1)
            item.key.delete()    
            self.response.write('None')
        else:
            self.response.write('CAN NOT UNSET VARIABLE THAT DOES NOT EXIST')



# expects a variable. prints the number of items in Item model with value equal to the variable
class NumEqualToHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        value = self.request.get('value')
        valOcc = ValueOccurence.query(ValueOccurence.value == value).get()
        if valOcc:
            self.response.write(str(valOcc.occurence))
        else:
            self.response.write(0) 
              
              
              
# Undo the most recent SET/UNSET command
class UndoHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
#       find the last set/unset request that is to be undone
        req = SettingHistory.query(SettingHistory.isLastRequest==True).get()
        if req:
            newSeqId = fixSettingOrder(PotentialRedos) 
            newPotentialRedo = PotentialRedos(name=req.name, value=req.value, seqId=newSeqId, isLastRequest=True)
            newPotentialRedo.put()
            
#           update the items model accordingly
            item = Item.query(Item.name == req.name).get()
#           if item was found then the command was a set command
            if item:
                if req.priorValue=='None':
                    item.key.delete()
                else:
                    item.value=req.priorValue
                    item.put()
#           item wasnot found in Item model, which means the command to be undone
#           was an unset command            
            else:
                newItem=Item(name=req.name,value=req.priorValue) 
                newItem.put()       
                    
#           update the ValueOccurence model accordingly
            if req.value=='None':     
#               command was an unset command
                updateOccurences(req.priorValue,1)
            else:
                updateOccurences(req.value,-1)
                if req.priorValue!='None': 
                    updateOccurences(req.priorValue,1)    
#           change the isLastRequest of the SettingHistory model to the
#           request before the one that is about to be deleted
            historyLastRequest = SettingHistory.query(SettingHistory.seqId==req.seqId-1).get()
            if historyLastRequest:
                historyLastRequest.isLastRequest=True
                historyLastRequest.put()
                
#           remove the request that was undone from the SettingHistory model  
            self.response.write(req.name + ' = ' + req.priorValue)  
            req.key.delete()
        else:
            self.response.write('NO COMMANDS')

class RedoHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        req = PotentialRedos.query(PotentialRedos.isLastRequest==True).get()
        if req:
#           change the isLastRequest of the PotentialRedos model to the
#           request before the one that is about to be deleted
            redoLastRequest = PotentialRedos.query(PotentialRedos.seqId==req.seqId-1).get()
            if redoLastRequest:
                redoLastRequest.isLastRequest=True
                redoLastRequest.put()
            
#           try and find the item in the items model
            item = Item.query(Item.name == req.name).get()
            if item:
#               add the command back to SettingHistory
                newSeqId = fixSettingOrder(SettingHistory) 
                newSettingHistory = SettingHistory(name=req.name, value=req.value, 
                                                   priorValue=item.value, isLastRequest=True, seqId=newSeqId)
                newSettingHistory.put()         
                
                if req.value=='None':
#               command was an unset command, update the relevent entities in their models accordingly
                    updateOccurences(item.value,-1)
                    item.key.delete()
                    
                else:
#               command was a set command.        
#               update the relevent entities in their models accordingly 
                    oldValue = item.value
                    item.value = req.value
                    item.put()
                    updateOccurences(req.value,1)
                    updateOccurences(oldValue,-1)
                 
#           item was not in Items model, update the relevent entities in their models accordingly
            else:
                updateOccurences(req.value,1)
                item=Item(value=req.value,name=req.name)
                item.put()
                
                newSeqId = fixSettingOrder(SettingHistory) 
                newSettingHistory = SettingHistory(name=req.name, value=req.value, 
                                                   priorValue='None', isLastRequest=True, seqId=newSeqId)
                newSettingHistory.put()     
            
            self.response.write(req.name + ' = ' + req.value)         
#           delete req from PotentialRedos    
            req.key.delete()
        else:
            self.response.write('NO COMMANDS')        

# cleans out the entire db
class EndHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        emptyModel(Item)
        emptyModel(ValueOccurence)
        emptyModel(SettingHistory)
        emptyModel(PotentialRedos)
        self.response.write('CLEANED')        
 
            
            
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/get', GetHandler),
    ('/set', SetHandler),
    ('/unset', UnsetHandler),
    ('/numequalto', NumEqualToHandler),
    ('/undo', UndoHandler),
    ('/redo', RedoHandler),
    ('/end', EndHandler),
    ], debug=False)
