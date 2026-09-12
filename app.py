from flask import Flask, render_template, request, send_from_directory
import cv2
import os

app = Flask(__name__)

# Folder to store images
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/count", methods=["POST"])
def count_bubbles():

    # Get uploaded image
    file = request.files.get("tea_image")

    # Also support "image" if the HTML uses that name
    if file is None:
        file = request.files.get("image")

    if file is None or file.filename == "":
        return "Please upload a tea image."

    # Save uploaded image
    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "tea.jpg"
    )

    file.save(image_path)

    # Read image
    image = cv2.imread(image_path)

    if image is None:
        return "Could not read the image."

    # Make copy for drawing
    result = image.copy()

    # -----------------------------------------
    # Convert to grayscale
    # -----------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Smooth image
    gray = cv2.GaussianBlur(
        gray,
        (7, 7),
        1
    )

    height, width = gray.shape

    # -----------------------------------------
    # Define central tea region
    # -----------------------------------------

    center_x = width // 2
    center_y = height // 2

    tea_radius = int(
        min(width, height) * 0.40
    )

    # Create black mask
    mask = cv2.Mat if False else None
    mask = gray.copy()
    mask[:] = 0

    # White circle = tea area
    cv2.circle(
        mask,
        (center_x, center_y),
        tea_radius,
        255,
        -1
    )

    # -----------------------------------------
    # Apply mask
    # -----------------------------------------

    tea_area = cv2.bitwise_and(
        gray,
        gray,
        mask=mask
    )

    # -----------------------------------------
    # Detect bubbles using Hough Circles
    # -----------------------------------------

    circles = cv2.HoughCircles(
        tea_area,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=15,
        param1=80,
        param2=30,
        minRadius=2,
        maxRadius=40
    )

    final_bubbles = []

    if circles is not None:

        circles = circles[0]

        for circle in circles:

            x = int(circle[0])
            y = int(circle[1])
            r = int(circle[2])

            # ---------------------------------
            # Check if circle is inside tea area
            # ---------------------------------

            distance = (
                (x - center_x) ** 2 +
                (y - center_y) ** 2
            ) ** 0.5

            if distance + r > tea_radius:
                continue

            # ---------------------------------
            # Remove duplicate/overlapping circles
            # ---------------------------------

            duplicate = False

            for fx, fy, fr in final_bubbles:

                distance2 = (
                    (x - fx) ** 2 +
                    (y - fy) ** 2
                ) ** 0.5

                if distance2 < min(r, fr) * 0.8:
                    duplicate = True
                    break

            if duplicate:
                continue

            final_bubbles.append(
                (x, y, r)
            )

    # -----------------------------------------
    # Count bubbles
    # -----------------------------------------

    count = len(final_bubbles)

    # -----------------------------------------
    # Draw detected bubbles
    # -----------------------------------------

    for x, y, r in final_bubbles:

        # Green circle
        cv2.circle(
            result,
            (x, y),
            r,
            (0, 255, 0),
            2
        )

        # Red center
        cv2.circle(
            result,
            (x, y),
            3,
            (0, 0, 255),
            -1
        )

    # -----------------------------------------
    # Save result
    # -----------------------------------------

    result_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        "result.jpg"
    )

    cv2.imwrite(
        result_path,
        result
    )

    # -----------------------------------------
    # Show result
    # -----------------------------------------
# -----------------------------------------
    # Bubble level
    # -----------------------------------------

    if count == 0:
        bubble_level = "No Bubbles 😶"
        message = "This tea needs some bubbles!"
    elif count <= 10:
        bubble_level = "Low Bubble Level 🫧"
        message = "A calm and peaceful cup of tea."
    elif count <= 30:
        bubble_level = "Medium Bubble Level 🫧🫧"
        message = "Nice! Your tea has some bubbles."
    elif count <= 50:
        bubble_level = "Very Bubbly! 🫧🫧🫧"
        message = "Your tea is having a bubbly day! 😂"
    else:
        bubble_level = "EXTREMELY BUBBLY! 🤯🫧"
        message = "Okay... this tea is VERY bubbly!"
    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>Tea Bubble Counter</title>

        <style>

            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                background: #f8eeee;
                padding: 40px;
            }}
           

            .card {{
                background: white;
                padding: 30px;
                border-radius: 20px;
                max-width: 850px;
                margin: auto;
                box-shadow:
                    0 5px 20px
                    rgba(0,0,0,0.15);
            }}

            h1 {{
                color: #6b3030;
            }}

            .count {{
                font-size: 60px;
                font-weight: bold;
                color: #8e44ad;
            }}
            .message{{
             font-size:20px;
             color:#555;
             margin-top:10px;
            }}

            img {{
                max-width: 100%;
                border-radius: 15px;
                margin-top: 20px;
            }}

            a {{
                display: inline-block;
                margin-top: 25px;
                padding: 12px 20px;
                background: #6b3030;
                color: white;
                text-decoration: none;
                border-radius: 10px;
            }}

        </style>

    </head>

    <body>

        <div class="card">

            <h1>🧋 Tea Bubble Counter</h1>

            <h2>🫧 Bubbles Detected</h2>

<div class="count">
    {count}
</div>

<h2>{bubble_level}</h2>

<p class="message">
    {message}
</p>

            <img
                src="/uploads/result.jpg"
                alt="Bubble detection result"
            >

            <br>

            <a href="/">
                Count Another Image
            </a>
            <a href="/uploads/result.jpg"download>
            ⬇️ Download Result
            </a>
        </div>

    </body>

    </html>
    """


@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


if __name__ == "__main__":
    app.run(debug=True)