import cv2

# Your IP Webcam MJPEG URL
url = "http://192.168.0.105:8080/video"

cap = cv2.VideoCapture(url)

# Optional: Set OpenCV capture resolution (may or may not be supported by IP Webcam)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Cannot open camera. Check URL and network.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Resize frame manually (works regardless of original stream size)
    frame_resized = cv2.resize(frame, (640, 480))

    cv2.imshow("IP Webcam Feed", frame_resized)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
