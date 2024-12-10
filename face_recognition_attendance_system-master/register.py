import cv2

while(True):
    vid = cv2.VideoCapture(0)
    name = input("Enter the name: ")

    if(name == ""):
        print("\nPlease enter the name\n")
        vid.release()
        cv2.destroyAllWindows()
        continue

    while(True):
        success, frame = vid.read()
        cv2.imshow(name, frame)
        cv2.imwrite("./imagesattendence/"+name+'.jpg', frame)
        print("image takenn, press 'q' to stop capture")

        if(cv2.waitKey(1) == ord("q")):
            break

    vid.release()
    cv2.destroyAllWindows()

    next = input("Do you want to enter the next student registration? press ( y / n ): ")

    if(next == 'y'):
       continue
    else:
        break
    
