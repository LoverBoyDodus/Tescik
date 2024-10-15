import cv2
import numpy as np
import mss
import pyautogui
import pygetwindow as gw
import time
import os
import requests

# Define the color range for player detection (in HSV color space)
lower_color = np.array([50, 100, 100])  # Lower HSV bound (example for green)
upper_color = np.array([70, 255, 255])  # Upper HSV bound (example for green)

# Define the center of the screen (crosshair position)
crosshair_center = (960, 540)  # Center position of the crosshair (for a 1920x1080 screen)
crosshair_radius = 1  # Radius within which to consider an opponent as being on the crosshair

# Speed of mouse movement towards the target
mouse_move_speed = 10

# Dead zone radius (how close the mouse must be to the target to click)
dead_zone_radius = 10

# Directory to save recorded frames
output_dir = "recorded_frames"
os.makedirs(output_dir, exist_ok=True)

# Discord webhook URL
webhook_url = "https://discord.com/api/webhooks/1295071677734191195/ZMzLti1qw2lQOzhN3nX9B6jh5vAosmAiOkzxRtc0d7R1sBBTZCsCH-l3Tw4nzkCYMIVb"  # Use your actual webhook URL

# Frame counter for saved frames
frame_counter = 0

while True:
    # Get the Fortnite window
    try:
        fortnite_window = gw.getWindowsWithTitle('Fortnite')[0]
        left, top, width, height = fortnite_window.left, fortnite_window.top, fortnite_window.width, fortnite_window.height
    except IndexError:
        print("Fortnite window not found. Please ensure it is open.")
        time.sleep(1)  # Wait a moment before retrying
        continue

    # Screen capture object using mss
    with mss.mss() as sct:
        # Define screen capture dimensions (Fortnite window)
        screen_region = {"top": top, "left": left, "width": width, "height": height}

        # Capture the screen
        screen_shot = sct.grab(screen_region)

        # Convert to a NumPy array (OpenCV image format)
        img = np.array(screen_shot)

        # Convert the image from BGRA to BGR (since OpenCV uses BGR format)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Save the frame for later sending to Discord
        frame_filename = os.path.join(output_dir, f"frame_{frame_counter}.png")
        cv2.imwrite(frame_filename, img_bgr)
        frame_counter += 1

        # Convert the image to HSV color space for color detection
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Create a mask for the color range
        mask = cv2.inRange(img_hsv, lower_color, upper_color)

        # Find contours of the detected areas
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Variable to store the closest opponent's center
        closest_opponent_center = None
        closest_distance = float('inf')

        # Draw contours and check for players
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum area threshold to avoid noise
                # Draw a rectangle around detected player
                x, y, w, h = cv2.boundingRect(contour)
                # Calculate the center of the detected player
                player_center = (x + w // 2, y + h // 2)

                # Calculate the distance from the crosshair center to the player's center
                distance_to_crosshair = np.sqrt((player_center[0] - crosshair_center[0]) ** 2 + 
                                                  (player_center[1] - crosshair_center[1]) ** 2)

                # Check if this opponent is the closest one detected
                if distance_to_crosshair < closest_distance:
                    closest_distance = distance_to_crosshair
                    closest_opponent_center = player_center

        # If there is a closest opponent, aim and shoot
        if closest_opponent_center:
            target_x, target_y = closest_opponent_center
            current_x, current_y = pyautogui.position()  # Get current mouse position
            
            # Calculate the difference in position
            delta_x = target_x - current_x
            delta_y = target_y - current_y
            
            print(f"Delta X: {delta_x}, Delta Y: {delta_y}, Mouse Move Speed: {mouse_move_speed}")

            # Check if the opponent is outside the dead zone
            if closest_distance > dead_zone_radius:  
                if abs(delta_x) > mouse_move_speed or abs(delta_y) > mouse_move_speed:
                    # Move the mouse towards the opponent in small increments
                    move_x = int(np.sign(delta_x) * mouse_move_speed)
                    move_y = int(np.sign(delta_y) * mouse_move_speed)
                    pyautogui.move(move_x, move_y)  # Move mouse in small increments
                else:
                    # Click if within range
                    pyautogui.click()  # Simulate left mouse button click
                    print("Opponent aimed at and clicked!")

        # Send recorded frames to Discord after every 10 frames
        if frame_counter % 1000 == 0:
            with open(frame_filename, 'rb') as f:
                requests.post(webhook_url, files={"file": f})

        # Display the image in a window (optional for debugging)
        cv2.imshow("Screen Capture", img_bgr)

        # Break the loop if '.' is pressed
        if cv2.waitKey(1) == ord('.'):
            break

# Clean up when done
cv2.destroyAllWindows()

