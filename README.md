This database was implemented using **Python** and **Google App Engine**

The HTTP methods in this project are all of type GET.

**__Models__**  
The noSQL database used was Datasore. in order to make all data persistent the database has four models:  
1. **Item(name,value)**- This model contains the variables in the db, specifically their name and value.  
2. **ValueOccurence(value,occurence)** - this model contains the values that have at least 1 occurence in the db.    
3. **SettingHistory(seqId,name,value,priorValue,isLastRequest)** - This model represents the history logs of the   
   set/unset commands. We know whether a request is a set or an unset request by the value property, if value='None'  
   then it is an unset command, otherwise it's a set command.  
   as for the properties, they are:
   name - name of the variable  
   seqId - each order gets a sequential integer seqId that helps us keep track of   
   the order the requests were received at.  
   isLastRequest - Only one entity's isLastRequest would be set to true in this model at any given time, 
   it represents the most recent one.    
   it's goal is to let us know the most recent set/unset command, so that we could easily know the seqId    
   that should be given to the next set/unset request. and to know which command should be undone if we    
   get an undo request.    
   priorValue - points to the last value the entity with this name has had, before this last set/unset request.  
   SeqId - would help us keep these logs of set/unset commands in order.  
4. **PotentialRedos(seqId,name,value,isLastRequest)** -  This class entities would be set/unset commands   
   that were undone, they would leave the SettingHistory model and enter this one upon a successful undo.   
   When trying to redo, we would check to see whether this model has entities in it. and if a redo  
   is successful then the set/unset command would leave this model and return to the SettingHistory one.  
   the meaning of the properties is the same as in SettingHistory.  

__the nitty gritty behind the scenes:__ 
As entities are created in SettingHistory model as a result of set/unset, or moved from SettingHistory to PotentialRedos
and vice versa due to redo/undo commands, the isLastRequest property gets updated, acting as a sort of persistent pointer.  
so when a new set/unset request arrives, the command is also saved in SettingHistory and gets to be the one with   
isLastRequest = true.  
And when we make a successful undo, then the log of the set command leaves the SettingHistory model,  
and through seqId we change the value of the prior command's isLastRequest (the one with seqId-1) to true.  
the log of the set command that was removed from SettingHistory would enter PotentialRedos, and get to be the one  
with isLastRequest == True, since it is now the first command that would get redone if we get a redo request.  
similarly, on a successful redo command, the log of the command would leave PotentialRedos, letting the next command  
in line in PotentialRedos (we find it through seqId) become the one with a True value for isLastRequest.  
and the command that left PotentialRedos re-enters SettingHistory and gets to be the one with a True value for isLastRequest.  
of course other things change accordingly as well, like whether a variable is found in Item model, and occurences (in ValueOccurence).  

__Runtime:__  
The run time for all requests except /End is O(1) **on average**.  
This includes the /set and /unset requests that at times  
require emptying the PotentialRedos model.  

__The commands this database can handle are:__  
SET – [http://_your-app-id_.appspot.com/set?name= { variable_name } &value= { variable_value } ]  
Set the variable variable_name to the value variable_value , neither variable names nor values will contain  
spaces. Print the variable name and value after the change.

**GET – [http://_your-app-id_.appspot.com/get?name= { variable_name }**  
Print out the value of the variable name or "None" if the variable is not set  

**UNSET – [http://_your-app-id_.appspot.com/unset?name= { variable_name } ]**  
Unset the variable variable_name , making it just like the variable was never set.  

**NUMEQUALTO – [http://_your-app-id_.appspot.com/numequalto?value= { variable_value } ]**  
Print to the browser the number of variables that are currently set to variable_value . If no variables equal that
value, print 0.

**UNDO – [http://_your-app-id_.appspot.com/undo]**  
Undo the most recent SET/UNSET command. If more than one consecutive UNDO command is issued, the  
original commands should be undone in the reverse order of their execution. Print the name and value of the  
changed variable (after the undo) if successful, or print NO COMMANDS if no commands may be undone  
Example: If you set the variable name x to the value 13 via request, then you set the variable name x to the  
value 22 via request, the undo request will undo the assignment of the value 22 to the variable x and will revert  
it’s value to 13, if then another undo request will be issued it will unset the variable.  

**REDO – [http://_your-app-id_.appspot.com/redo]**  
Redo the most recent SET/UNSET command which was undone. If more than one consecutive REDO  
command is issued, the original commands should be redone in the original order of their execution. If another  
command was issued after an UNDO, the REDO command should do nothing. Print the name and value of the  
changed variable (after the redo) if successful, or print NO COMMANDS if no commands may be re-done.  

**END – [http://_your-app-id_.appspot.com/end]**  
Exit the program. Your program will always receive this as its last command. You need to remove all your data  
from the application (clean all the Datastore entities). Print CLEANED when done.  

__Some example sequences:__  
Sequence 1:  
1. Input: http://_your-app-id_.appspot.com/set?name=ex&value=10  
Output: ex = 10  
2. Input: http://_your-app-id_.appspot.com/get?name=ex  
Output: 10  
3. Input: http://_your-app-id_.appspot.com/unset?name=ex  
Output: ex = None  
4. Input: http://_your-app-id_.appspot.com/get?name=ex  
Output: None  
5. Input: http://_your-app-id_.appspot.com/end  
Output: CLEANED  

Sequence 2:  
1. Input: http://_your-app-id_.appspot.com/set?name=a&value=10  
Output: a = 10  
2. Input: http://_your-app-id_.appspot.com/set?name=b&value=10  
Output: b = 10  
3. Input: http://_your-app-id_.appspot.com/numequalto?value=10  
Output: 2  
4. Input: http://_your-app-id_.appspot.com/numequalto?value=20  
Output: 0  
5. Input: http://_your-app-id_.appspot.com/set?name=b&value=30  
Output: b = 30  
6. Input: http://_your-app-id_.appspot.com/numequalto?value=10  
Output: 1  
7. Input: http://_your-app-id_.appspot.com/end  
Output: CLEANED  

Sequence 3:  
1. Input: http://_your-app-id_.appspot.com/set?name=a&value=10  
Output: a = 10  
2. Input: http://_your-app-id_.appspot.com/set?name=b&value=20  
Output: b = 20  
3. Input: http://_your-app-id_.appspot.com/get?name=a  
Output: 10  
4. Input: http://_your-app-id_.appspot.com/get?name=b  
Output: 20  
5. Input: http://_your-app-id_.appspot.com/undo  
Output: b = None  
6. Input: http://_your-app-id_.appspot.com/get?name=a  
Output: 10  
7. Input: http://_your-app-id_.appspot.com/get?name=b  
Output: None  
8. Input: http://_your-app-id_.appspot.com/set?name=a&value=40  
Output:  
9. Input: http://_your-app-id_.appspot.com/get?name=a  
Output: 40  
10. Input: http://_your-app-id_.appspot.com/undo  
Output: a = 10  
11. Input: http://_your-app-id_.appspot.com/get?name=a  
Output: 10  
12. Input: http://_your-app-id_.appspot.com/undo  
Output: a = None  
13. Input: http://_your-app-id_.appspot.com/get?name=a  
Output: None  
14. Input: http://_your-app-id_.appspot.com/undo  
Output: NO COMMANDS  
15. INPUT: http://_your-app-id_.appspot.com/redo  
Output: a = 10  
16. INPUT: http://_your-app-id_.appspot.com/redo  
Output: a = 40  
15. Input: http://_your-app-id_.appspot.com/end  
Output: CLEANED  
