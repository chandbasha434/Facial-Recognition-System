import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime


path= 'imagesattendence'
images = []
classnames=[]
mylist=os.listdir(path)
print(mylist)

for cl in mylist:
	curimg=cv2.imread(f'{path}/{cl}')
	images.append(curimg)
	classnames.append(os.path.splitext(cl)[0])
print(classnames)

def findencodings(images):
    encodelistknown = []
    for img in images:
        try:
            face_encodings = face_recognition.face_encodings(img)
            if len(face_encodings) > 0:
                encode = face_encodings[0]
                encodelistknown.append(encode)
        except Exception as e:
            print(f"Error processing image {img}: {e}")
    return encodelistknown

encodelistknown=findencodings(images)
print('encoding completed')


def markattendence(name):
	now=datetime.now()
	current_date = now.strftime('%d:%m:%y')
	file_name = f"{current_date}.csv"
	with open(file_name,'a+') as f:
		f.seek(0)
		mydatalist=f.readlines()
		namelist=[]
		for line in mydatalist:
			entry=line.split(',')
			namelist.append(entry[0])
		if name not in namelist:
			now=datetime.now()
			dtString=now.strftime('%H:%M:%S')
			dtdate=now.strftime('%d:%m:%y')
			f.writelines(f'\n{name},{dtString},{dtdate}')




cap=cv2.VideoCapture(0)
while True:
	success,img=cap.read()
	imgs=cv2.resize(img,(0,0),None,0.25,0.25)
	imgs=cv2.cvtColor(imgs,cv2.COLOR_BGR2RGB)

	facescurframe=face_recognition.face_locations(imgs,model="hog")
	encodescurframe=face_recognition.face_encodings(imgs,facescurframe)

	for encodeface,faceloc in zip(encodescurframe,facescurframe):
		matches=face_recognition.compare_faces(encodelistknown,encodeface)
		facedis=face_recognition.face_distance(encodelistknown,encodeface)
		min_distance=min(facedis)
		matching_percent=(1-min_distance)*100

		matchindex=np.argmin(facedis)
		if matching_percent >45:

			if matches[matchindex]:
				name=classnames[matchindex].upper()
				print(name)
				y1,x2,y2,x1=faceloc
				y1,x2,y2,x1=y1*4,x2*4,y2*4,x1*4
				cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
				cv2.rectangle(img,(x1,y2-30),(x2,y2),(0,255,0),cv2.FILLED)
				cv2.putText(img,name,(x1+6,y2-6),cv2.FONT_HERSHEY_COMPLEX,1,(255,0,0),2)
				markattendence(name)

		else:
			print("you are not registered")

	cv2.imshow('Attendance_Marking',img)
	if(cv2.waitKey(1) == ord("q")):
				break
