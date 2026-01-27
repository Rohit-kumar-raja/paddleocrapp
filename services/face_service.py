import cv2
import numpy as np

class FaceService:
    def __init__(self):
        # Load pre-trained Haar Cascade classifier for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def detect_face(self, image_bytes: bytes):
        """
        Detects a face in the image and returns a confidence score.
        score is 1.0 if a face is detected, 0.0 otherwise.
        In a more advanced implementation, this could involve clarity/size metrics.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return 0.0, 0
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        num_faces = len(faces)
        # For simplicity, we define 'human face score' as 1.0 if at least one face is found
        # and 0.0 if no face is found.
        score = 1.0 if num_faces > 0 else 0.0
        
        return score, num_faces
