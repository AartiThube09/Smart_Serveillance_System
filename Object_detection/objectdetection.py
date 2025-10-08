# import cv2
# from ultralytics import YOLO
# model = YOLO("yolov8n.pt") 


# # Load YOLO model
# model = YOLO("best.pt")

# # Mobile IP Webcam URL
# url = "http://192.168.0.102:8080/video"  

# cap = cv2.VideoCapture(url)

# if not cap.isOpened():
#     print("Cannot open camera. Check URL and network.")
#     exit()

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to grab frame. Retrying...")
#         continue  

#     # Optional: resize frame for faster processing
#     frame = cv2.resize(frame, (640, 480))

#     # Run YOLO detection
#     results = model(frame)

#     # Count objects
#     num_objects = len(results[0].boxes)

#     # Draw detection boxes
#     annotated_frame = results[0].plot()

#     # Show frame
#     cv2.imshow("YOLO - Mobile Camera", annotated_frame)

#     # Optional: print number of detected objects
#     print(f"Objects detected: {num_objects}")


#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()




from ultralytics import YOLO
import cv2

#Path to your trained model
MODEL_PATH = r"C:\\Users\\Aarti Thube\\OneDrive\\Desktop\\Smart_Servellance_System\\Object_detection\\best.pt"

#Load YOLO model
model = YOLO(MODEL_PATH)

#IP Webcam stream URL (change the IP if your phone shows a different one)
url = "http://192.168.0.107:8080/video"

#Open video stream
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("❌ Error: Could not open IP Webcam stream. Check your phone's IP and port.")
    exit()

#Set window name
window_name = "Smart Surveillance - Live Feed"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

#Resize display window (adjust as needed)
cv2.resizeWindow(window_name, 900, 600)  # you can change 900x600 to any size

print("Streaming started... Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to grab frame. Reconnecting...")
        continue

    #Run YOLO inference
    results = model.predict(frame, conf=0.4, verbose=False)

    #Get annotated frame
    annotated_frame = results[0].plot()

    #Resize frame to fit your window (optional)
    display_frame = cv2.resize(annotated_frame, (900, 600))  # same as window size above

    # ✅ Show live feed
    cv2.imshow(window_name, display_frame)

    # ✅ Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("🛑 Exiting...")
        break

# ✅ Release resources
cap.release()
cv2.destroyAllWindows()
