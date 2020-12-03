#Integration5.41

from pynq.lib import Wifi
from apscheduler.schedulers.blocking import BlockingScheduler

port = Wifi()
port.connect('T12503_4',"00T12503400", False, True)


import face_recognition
import cv2
import numpy as np
from firebase import firebase
import os, errno
import threading  
import imutils
import sys
import queue
from datetime import datetime
import tkinter as tk
from tkinter import *
from tkinter import font
import pickle
import pyaudio
import wave

global bQuit
global firsttime
global flag 
global aQuit
global stat

stat = 1
aQuit = False
flag = 0
firsttime = 0

path = r'images'
images = []
classNames = []
admin=[]
myList = os.listdir(path) 
sched = BlockingScheduler()
firebase=firebase.FirebaseApplication("https://test-4a3a3.firebaseio.com/",None)
data={
    'Name':'',
    'time':'',
    'admin':''
}

		

def DeleteData():
	now = datetime.now()
	dtString = now.strftime('%H:%M:%S')
	dtlimit = int(dtString[0:2])
	if (dtlimit<=20) and (dtlimit>=14):
		result=firebase.delete('DCS',None)
		data['Name']="dummy"
		data['time']="0000"
		data['admin']="0000"
		result=firebase.patch('/DCS', data)
	if (dtlimit<14) and (dtlimit>=8):
		result=firebase.delete('ACS',None)
		data['Name']="dummy"
		data['time']="0000"
		data['admin']="0000"
		result=firebase.patch('/ACS', data)  
	for cl in myList:
		curImg = cv2.imread(f'{path}/{cl}') 
		if not os.path.splitext(cl)[0].startswith("."):     
			images.append (curImg) 
			#classNames.append(os.path.splitext(cl)[0]) 
			cls=os.path.splitext(cl)[0]
			cls1=cls[0:4]
			cls2=cls[4:]
			admin.append(cls1)
			classNames.append(cls2) 
    
   scheduler = BlockingScheduler()
scheduler.add_job(some_job, 'interval', hours=10)
scheduler.start()

def taskCapture(inputId,queueIn):
	global bQuit

	print("[INFO] taskCapture : starting camera input ...")
	cam = cv2.VideoCapture(inputId)
	cam.set(cv2.CAP_PROP_FRAME_WIDTH,640)
	cam.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
	if not (cam.isOpened()):
		print("[ERROR] taskCapture : Failed to open camera " )
		exit()

	while not bQuit:
		print("[INFO] taskCapture : starting thread ...")
		ret,img = cam.read()

		queueIn.put(img)
		print("[INFO] taskCapture : exiting thread ...")

with open('dataset_faces.dat', 'rb') as f:
	encodeListKnown = pickle.load(f)
    
def taskWorker(worker,queueIn,queueOut):
	global bQuit
	global firsttime
	global flag
	global stat
	
	while not bQuit:
		print("[INFO] taskWorker[",worker,"] : starting thread ...")
		img = queueIn.get()

		imgS = cv2.resize(img, (0,0),None,0.25,0.25) 
		imgS = cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)
	  
		facesCurFrame = face_recognition.face_locations(imgS)
		encodeCurFrame = face_recognition.face_encodings(imgS,facesCurFrame)
	   
		for encodeFace,faceLoc in zip(encodeCurFrame,facesCurFrame):
			matches = face_recognition.compare_faces(encodeListKnown,encodeFace,tolerance = 0.53)
			name = "Unknown"
			adminnum = "Unknown"
			faceDis = face_recognition.face_distance(encodeListKnown,encodeFace)
			matchIndex = np.argmin(faceDis)
			  
			if matches[matchIndex]:
				name = classNames[matchIndex].upper()
				adminnum = admin[matchIndex]
			y1,x2,y2,x1 =faceLoc
			y1,x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
			cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
			cv2.rectangle(img,(x1,y2-35),(x2,y2),(0,255,0),cv2.FILLED)
			cv2.putText(img,name,(x1+6,y2-6),cv2.FONT_HERSHEY_COMPLEX,1,(255,0,0),2)

			if (firsttime == 0):
				firsttime = 1
				root = tk.Tk()
				root.resizable(0, 0) 
				HEIGHT=430
				WIDTH=830
				canvas =tk.Canvas(root,height=HEIGHT, width=WIDTH)
				canvas.pack()

				title = Label(root,text="Attendance Result", font=("Helvetica", 20))
				title.place(x=300, y=10)

				frame4 = tk.Frame(root, highlightbackground="gray", 
						  highlightcolor="white", 
						  highlightthickness=1.5, 
						  bd=10)
				frame4.place(x=400,y=60, width=700, 
						height=300, 
						anchor='n')
				if (name == "Unknown"):
					flag = 2                    
					print_result1 = Label(frame4, text="Unknown detected", font=("Helvetica", 10))
					print_result1.place(x=20,y=50)
					print_result1 = Label(frame4, text="Please try again", font=("Helvetica", 10))
					print_result1.place(x=20,y=80)
				else:
					flag = 1
					now = datetime.now()
					dtString = now.strftime('%H:%M:%S')
					dtString2 = now.strftime('%d %b %y')
					data['Name']=name
					data['time']=dtString
					data['admin']=adminnum
					dtlimit = int(dtString[0:2])
					uploadpath='/customer/'+name
                    
					if (dtlimit<=20) and (dtlimit>=14):
						dt=firebase.get("/ACS",None)
						for person in dt.values():
							if name == person["Name"]:
								stat=0
						if stat !=0 :
							result=firebase.patch(uploadpath, data)
							result=firebase.post("ACS", data)
							print_result = Label(frame4, text=str(name)+" Attendance is taken", font=("Helvetica", 10))
							print_result.place(x=20,y=20)
							print_result1 = Label(frame4, text="Day: " +str(dtString2), font=("Helvetica", 10))
							print_result1.place(x=20,y=50)
							print_result1 = Label(frame4, text="Time: " + str(dtString), font=("Helvetica", 10))
							print_result1.place(x=20,y=80)
							print_result1 = Label(frame4, text="Admin: " +str(adminnum), font=("Helvetica", 10))
							print_result1.place(x=20,y=110)
						else:
							print_result = Label(frame4, text=str(name)+" attendance is already taken.", font=("Helvetica", 10))
							print_result.place(x=20,y=20)
                            
					if (dtlimit<14) and (dtlimit>=8):
						dt=firebase.get("/DCS",None)
						for person in dt.values():
							if name == person["Name"]:
								stat=0
						if stat !=0 :
							result=firebase.patch(uploadpath, data)
							result=firebase.post('DCS', data)
							print_result = Label(frame4, text=str(name)+" Attendance is taken", font=("Helvetica", 10))
							print_result.place(x=20,y=20)
							print_result1 = Label(frame4, text="Day: " +str(dtString2), font=("Helvetica", 10))
							print_result1.place(x=20,y=50)
							print_result1 = Label(frame4, text="Time: " + str(dtString), font=("Helvetica", 10))
							print_result1.place(x=20,y=80)
							print_result1 = Label(frame4, text="Admin: " +str(adminnum), font=("Helvetica", 10))
							print_result1.place(x=20,y=110)
						else:
							print_result = Label(frame4, text=str(name)+" attendance is already taken.", font=("Helvetica", 10))
							print_result.place(x=20,y=20)


				root.after (5000, lambda: root.destroy())
				root.mainloop()
				bQuit = True
				
		queueOut.put(img)
		print("[INFO] taskWorker[",worker,"] : exiting thread ...")
        
	queueIn.put(img)

def taskDisplay(queueOut):
	global bQuit
	global aQuit

	while not bQuit:
		print("[INFO] taskDisplay : starting thread ...")
		img = queueOut.get()

		cv2.imshow("Webcam", img)

		print("[INFO] taskDisplay : exiting thread ...")

		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			bQuit = True
			aQuit = True
  
	cv2.destroyAllWindows()

def main(argv):
	global x
	global bQuit
	global aQuit
	global firsttime
	global flag
	global stat
    
	filename = r"audio9.wav"
	chunk = 512   
	wf = wave.open(filename, 'rb')
	p = pyaudio.PyAudio()
	stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),input=False,
                    channels = 2,
                    rate = wf.getframerate(), output_device_index = 4,
                    output = True)

	data = wf.readframes(chunk)
            
	while True:
		if data != '':
			stream.write(data)
			data = wf.readframes(chunk)
		if data == b'':
			break
            
	stream.close()
	p.terminate()
    
	while not aQuit:     
		stat = 1
		flag = 0 
		firsttime = 0
		bQuit = False
        
		inputId = 0
		threads = 4
       
		queueIn = queue.Queue()
		queueOut = queue.Queue() 
        
		threadAll = []
		tc = threading.Thread(target=taskCapture,args=(inputId,queueIn))
		threadAll.append(tc)
		for i in range(threads):
			tw = threading.Thread(target=taskWorker, args=(i,queueIn,queueOut))
			threadAll.append(tw)
		td = threading.Thread(target=taskDisplay, args=(queueOut,))
		threadAll.append(td)
        
		for x in threadAll:
			x.start()
            
		for x in threadAll:
			x.join()
        
		if (flag == 1):
			if (stat == 0):
				filename = r"audio6.wav"
			else:
				filename = r"audio1.wav"
		elif (flag == 2):
			filename = r"audio2.wav"
		else:
			filename = r"audio8.wav"
            
		chunk = 1024   
		wf = wave.open(filename, 'rb')
		p = pyaudio.PyAudio()
		stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),input=False,
                        channels = 2,
                        rate = wf.getframerate(), output_device_index = 4,
                        output = True)

		data = wf.readframes(chunk)
                
		while True:
			if data != '':
				stream.write(data)
				data = wf.readframes(chunk)
			if data == b'':
				break
                
		stream.close()
		p.terminate()

if __name__ == "__main__":
	main(sys.argv)
	
