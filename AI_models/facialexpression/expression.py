import cv2
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from fer import FER

# Initialize FER detector
detector = FER(mtcnn=True)

cap = cv2.VideoCapture("http://192.0.0.4:8080/video")  

# Optional: request frame size (network streams may ignore this)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 320)

if not cap.isOpened():
    print("❌ Cannot open mobile camera. Check URL and network.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠ Failed to grab frame. Retrying...")
        continue

    # Resize frame to smaller size for faster processing
    frame = cv2.resize(frame, (480, 320))

    # Detect emotions
    results = detector.detect_emotions(frame)

    for result in results:
        (x, y, w, h) = result['box']
        emotions = result['emotions']
        dominant_emotion = max(emotions, key=emotions.get)

        # Draw face box and emotion
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, dominant_emotion, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Show the frame
    cv2.imshow("Facial Expression Recognition", frame)

    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
