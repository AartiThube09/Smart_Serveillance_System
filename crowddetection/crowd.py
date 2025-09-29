from ultralytics import YOLO
import cv2
import datetime
import winsound  


def alert_authority(human_count, threshold):
    """Trigger alert message for authority"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🚨 ALERT: Overcrowding Detected!\nPeople Count: {human_count}\nThreshold: {threshold}\nTime: {timestamp}"


    print(message)


    # buzzer
    winsound.Beep(1200, 700)  

    return message


def main():
    model = YOLO("yolov8s.pt") 
    
    url = "http://192.0.0.4:8080/video"  
    
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("❌ Error: Could not open mobile camera. Check URL and network.")
        return

    crowd_threshold = 2  
    
    frames_above_threshold = 0
    alert_active = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Failed to grab frame. Retrying...")
            continue

        frame = cv2.resize(frame, (480, 320))
        results = model(frame, conf=0.5, verbose=False)

        human_count = 0
        for result in results:
            for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                if int(cls) == 0: 
                    human_count += 1
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Show live count
        cv2.putText(frame, f"People: {human_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Alert system
        if human_count > crowd_threshold:
            frames_above_threshold += 1
            if frames_above_threshold > 5 and not alert_active:  
                # alert_msg = alert_authority(human_count, crowd_threshold)
                cv2.putText(frame, "🚨 ALERT: Crowd Detected!", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                alert_active = True
        else:
            frames_above_threshold = 0
            alert_active = False
            print("✅ No crowd detected")
            # Show "No crowd" message on screen
            cv2.putText(frame, "✅ No crowd detected", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Display feed
        cv2.imshow("Real-Time Crowd Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
