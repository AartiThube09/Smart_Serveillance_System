from ultralytics import YOLO
import cv2
import datetime
import winsound  # For buzzer (Windows)

def alert_authority(human_count, threshold):
    """Trigger alert message for authority"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🚨 ALERT: Overcrowding Detected!\nPeople Count: {human_count}\nThreshold: {threshold}\nTime: {timestamp}"

    # Console log (can be redirected to monitoring system)
    print(message)

    # Play buzzer
    winsound.Beep(1200, 700)  

    return message


def main():
    model = YOLO("yolov8s.pt")  # use small model for accuracy
    url = "http://192.0.0.4:8080/video"  # your IP webcam link
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("❌ Error: Could not open mobile camera. Check URL and network.")
        return

    crowd_threshold = 2  # ⚡ TEST: trigger alert if more than 2 people
    frames_above_threshold = 0
    alert_active = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Failed to grab frame. Retrying...")
            continue

        frame = cv2.resize(frame, (640, 480))
        results = model(frame, conf=0.5, verbose=False)

        human_count = 0
        for result in results:
            for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                if int(cls) == 0:  # person class
                    human_count += 1
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Show live count
        cv2.putText(frame, f"People: {human_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Alert system
        if human_count > crowd_threshold:
            frames_above_threshold += 1
            if frames_above_threshold > 5 and not alert_active:  # lower for testing
                # alert_msg = alert_authority(human_count, crowd_threshold)
                cv2.putText(frame, "⚠ CROWD ALERT!", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                alert_active = True
        else:
            frames_above_threshold = 0
            alert_active = False

        # Display feed
        cv2.imshow("Real-Time Crowd Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
