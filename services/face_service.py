import cv2
import numpy as np


class FaceService:
    def __init__(self):
        # Load pre-trained Haar Cascade classifier for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def _decode_image(self, image_bytes: bytes):
        """Decode image bytes to a cv2 image."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def _detect_faces(self, img):
        """Detect faces in a cv2 image. Returns list of (x, y, w, h) rects."""
        if img is None:
            return []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return faces if len(faces) > 0 else []

    def detect_face(self, image_bytes: bytes):
        """
        Detects a face in the image and returns (score, num_faces).
        score is 1.0 if a face is detected, 0.0 otherwise.
        """
        img = self._decode_image(image_bytes)
        faces = self._detect_faces(img)

        num_faces = len(faces)
        score = 1.0 if num_faces > 0 else 0.0
        return score, num_faces

    def compare_faces(self, doc_image_bytes: bytes, selfie_bytes: bytes) -> float:
        """
        Compare the face on a document with a selfie photo.
        Uses histogram correlation on the face ROIs.
        Returns a similarity score between 0.0 and 1.0.
        """
        doc_img = self._decode_image(doc_image_bytes)
        selfie_img = self._decode_image(selfie_bytes)

        if doc_img is None or selfie_img is None:
            return 0.0

        doc_faces = self._detect_faces(doc_img)
        selfie_faces = self._detect_faces(selfie_img)

        if len(doc_faces) == 0 or len(selfie_faces) == 0:
            return 0.0

        # Extract the largest face from each image
        doc_face = max(doc_faces, key=lambda f: f[2] * f[3])
        selfie_face = max(selfie_faces, key=lambda f: f[2] * f[3])

        # Crop face ROIs
        dx, dy, dw, dh = doc_face
        doc_roi = doc_img[dy:dy + dh, dx:dx + dw]

        sx, sy, sw, sh = selfie_face
        selfie_roi = selfie_img[sy:sy + sh, sx:sx + sw]

        # Resize both to a standard size for comparison
        size = (128, 128)
        doc_roi = cv2.resize(doc_roi, size)
        selfie_roi = cv2.resize(selfie_roi, size)

        # Convert to HSV for histogram comparison
        doc_hsv = cv2.cvtColor(doc_roi, cv2.COLOR_BGR2HSV)
        selfie_hsv = cv2.cvtColor(selfie_roi, cv2.COLOR_BGR2HSV)

        # Calculate histograms
        h_bins, s_bins = 50, 60
        hist_size = [h_bins, s_bins]
        ranges = [0, 180, 0, 256]
        channels = [0, 1]

        doc_hist = cv2.calcHist([doc_hsv], channels, None, hist_size, ranges)
        cv2.normalize(doc_hist, doc_hist, 0, 1, cv2.NORM_MINMAX)

        selfie_hist = cv2.calcHist([selfie_hsv], channels, None, hist_size, ranges)
        cv2.normalize(selfie_hist, selfie_hist, 0, 1, cv2.NORM_MINMAX)

        # Compare using correlation (higher = more similar, range -1 to 1)
        similarity = cv2.compareHist(doc_hist, selfie_hist, cv2.HISTCMP_CORREL)

        # Normalize to 0.0–1.0 range
        score = max(0.0, min(1.0, (similarity + 1) / 2))
        return round(score, 2)
