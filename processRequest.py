from UC_rest import *
from collections import defaultdict
import json
from datetime import datetime

class processRequestError(Exception):
   def __init__(self, *status_code):
      self.status_code = status_code[0]
      self.url         = status_code[1]

class processRequest(object):
   def __init__(self, req):
      try:
         self.resp=getApplicationRunDetail(request=req)
      except UCrestError as e:
         raise processRequestError, (e.status_code, e.url)
         

      self.data = self.resp.json()
      self.id = self.data['id']
      self.name = self.data['name']

   def formatLog(self,request):
	final_dict={}

	role=[]
        response=getApplicationRunDetail(request=request).json()
	role_step_dict = defaultdict(list)

	for i in response['children']:
		if i['result'] == "NONE":
			i['result']='Not_Started'
			i['startDate']=int(0000000000000)
			i['endDate']=int(0000000000000)
			i['duration']=int(0)
			
		i['displayName']=i['displayName'].replace(':','_')
		try:
			i['notNeeded']
			i['result']='Not_Mapped'
		except:
			print ""

		if i['result']=='CANCELED':
			i['startDate']=i['endDate']	
		role_string=i['displayName'] + ":" + str(i['startDate']) + ":" + str(i['endDate']) + ":" + str(i['duration']) + ":" + i['result']
		role_name=role_string.split(" ",1)[0]
		if len(role_string.split(" ",1)) > 1:
			step=role_string.split(" ",1)[1] 
			step=step[1:] if step.startswith('-') else step
			step=step[1:] if step.startswith(' ') else step
			role_step_dict[role_name].append(step)

	for d1,e1 in role_step_dict.items():
		e={}
		e['name']=d1
		steps=[]
		for t1 in e1:
			dd1={}
			dd1['name']=t1.split(":",)[0]
			dd1['startDate']=datetime.fromtimestamp(int(t1.split(":",)[1])//1000)
			dd1['endDate']=datetime.fromtimestamp(int(t1.split(":",)[2])//1000)
			dd1['duration']=int(t1.split(":",)[3])
			dd1['status']=t1.split(":",)[4]
			steps.append(dd1)
			e['steps']=steps
		role.append(e)
	
	response_1=getAppProcessReqProp(request=request).json()
	
	final_dict['application']= response_1['application']['name']
        final_dict['environment']=response_1['environment']['name']
	final_dict['process']=response_1['applicationProcess']['name']
	try:
		response_1['snapshot']['name']
		final_dict['snapshot']=response_1['snapshot']['name']
	except:
		final_dict['snapshot']='No_SnapShot_Selected'
 	final_dict['userName']=response_1['userName']		
	final_dict['role']=role
	final_dict['id']=request
	final_dict['startDate']=datetime.fromtimestamp(response['startDate']//1000)
	final_dict['endDate']=datetime.fromtimestamp(response['endDate']//1000)
	final_dict['duration']=response['duration']
	final_dict['status']=response['result']
	return final_dict
		
#***  MAIN  ***

if __name__ == "__main__":
   import argparse

   parser = argparse.ArgumentParser(description='Process Request class')
   parser.add_argument('-p', help='process request id', required=True)
   args = parser.parse_args()

   try:
      p = processRequest(args.p)
      print  p.name + " => " + str(p.id)
      p.formatLog(args.p)
   except processRequestError as e:
      print "Error: Bad application [{}] Status Code: {}".format(args.p, e.status_code)
      print "Error:   url -> {}".format(e.url)


