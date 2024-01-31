from PIL import Image, ImageDraw

# Create a new image
image = Image.new("RGB", (400, 400), (255, 255, 255))

# Create an ImageDraw object
draw = ImageDraw.Draw(image)

# Draw a rectangle
draw.rectangle((100, 100, 300, 300), fill=(0, 0, 255))

# Draw an ellipse
draw.ellipse((150, 150, 250, 250), fill=(255, 0, 0))

draw.line([(150, 200), (143, 254), (28, 300)], fill=(0, 255, 0), width=5)

# Save the image to the computer
image.save("image.png")