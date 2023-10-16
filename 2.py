from PIL import Image
import cv2

def resize_image(image_path, new_width, new_height):
    image = Image.open(image_path)
    resized_image = image.resize((new_width, new_height))
    resized_image.save(image_path)
    
def rotate_image(image_path, angle):
    image = Image.open(image_path)
    rotated_image = image.rotate(angle)
    rotated_image.save(image_path)
    
def adjust_brightness(image_path, brightness):
    image = cv2.imread(image_path)
    adjusted_image = cv2.convertScaleAbs(image, beta=brightness)
    cv2.imwrite(image_path, adjusted_image)
    
resize_image("user_image.jpg", 100, 200)
# rotate_image("user_image.jpg", 45)
# adjust_brightness("user_image.jpg", 45)