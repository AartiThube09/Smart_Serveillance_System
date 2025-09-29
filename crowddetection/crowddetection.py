from ultralytics import YOLO
import cv2

def main():
    # Load YOLOv8 model (pre-trained on COCO dataset)
    model = YOLO("yolov8n.pt")  # Nano model for real-time CPU detection

    # Mobile IP Webcam URL (replace with your phone's IP)
    url = "http://192.0.0.4:8080/video"  # <-- change this to your phone's IP

    cap = cv2.VideoCapture(url)

    # Optional: request frame size from OpenCV (may not always work for network streams)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("❌ Error: Could not open mobile camera. Check URL and network.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Failed to grab frame. Retrying...")
            continue  # Skip frame if grab fails

        # Resize frame to fixed size (ensures consistent processing)
        frame = cv2.resize(frame, (640, 480))

        # Run YOLOv8 detection (confidence threshold = 0.5)
        results = model(frame, conf=0.5)

        # Count number of people detected
        human_count = 0
        for result in results:
            for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                if int(cls) == 0:  # Class 0 = 'person' in COCO dataset
                    human_count += 1
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Show people count on screen
        cv2.putText(frame, f"People: {human_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display the annotated frame
        cv2.imshow("Real-Time Crowd Detection - Mobile Camera", frame)

        # Exit manually with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
