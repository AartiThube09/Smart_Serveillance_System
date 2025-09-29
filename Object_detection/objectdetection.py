import cv2
from ultralytics import YOLO
model = YOLO("yolov8n.pt") 


# Load YOLO model
model = YOLO("best.pt")

# Mobile IP Webcam URL
url = "http://192.168.0.102:8080/video"  

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Cannot open camera. Check URL and network.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Retrying...")
        continue  

    # Optional: resize frame for faster processing
    frame = cv2.resize(frame, (640, 480))

    # Run YOLO detection
    results = model(frame)

    # Count objects
    num_objects = len(results[0].boxes)

    # Draw detection boxes
    annotated_frame = results[0].plot()

    # Show frame
    cv2.imshow("YOLO - Mobile Camera", annotated_frame)

    # Optional: print number of detected objects
    print(f"Objects detected: {num_objects}")


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
