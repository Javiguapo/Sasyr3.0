import cv2
import dlib
import tkinter as tk
from PIL import ImageTk, Image
from functools import partial
import time

class Person:
    def __init__(self, id, initial_time):
        self.id = id
        self.initial_time = initial_time
        self.current_time = initial_time
        self.tracker = dlib.correlation_tracker()
        self.alert_sent = False
        self.alert_shown = False
        self.danger_alert = False

def detect_persons(frame, persons, alert_duration, danger_duration):
    hog = dlib.get_frontal_face_detector()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = hog(gray)

    threat_faces = []

    for face in faces:
        (x, y, w, h) = (face.left(), face.top(), face.width(), face.height())
        person_found = False

        for person in persons:
            person_pos = person.tracker.get_position()
            person_x = int(person_pos.left())
            person_y = int(person_pos.top())
            person_w = int(person_pos.width())
            person_h = int(person_pos.height())

            if (x < person_x + person_w and x + w > person_x and
                    y < person_y + person_h and y + h > person_y):
                person.current_time = time.time()
                person_found = True
                break

        if not person_found:
            new_person = Person(id=len(persons), initial_time=time.time())
            new_person.tracker.start_track(frame, dlib.rectangle(x, y, x + w, y + h))
            persons.append(new_person)

        threat_faces.append((x, y, w, h))

    return frame, threat_faces

def update_frame(label, cap, persons, alert_duration, danger_duration):
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame, threat_faces = detect_persons(frame, persons, alert_duration, danger_duration)

        for face_id in threat_faces:
            (x, y, w, h) = face_id
            person = None
            for p in persons:
                if p.id == face_id[0]:
                    person = p
                    break
            if person and not person.danger_alert:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, f"Person {person.id}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                cv2.putText(frame, f"Time: {round(time.time() - person.initial_time, 2)}s", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        current_time = time.time()
        for person in persons:
            if not person.alert_sent and current_time - person.initial_time >= alert_duration:
                person.alert_sent = True
                person.alert_shown = True

                possible_threat_window = tk.Toplevel()
                possible_threat_window.title("Posibles amenazas")
                possible_threat_label = tk.Label(possible_threat_window, text="Posibles amenazas")
                possible_threat_label.pack()

                for p in persons:
                    if current_time - p.initial_time >= alert_duration:
                        face_image = Image.fromarray(frame[int(p.tracker.get_position().top()):int(p.tracker.get_position().bottom()), int(p.tracker.get_position().left()):int(p.tracker.get_position().right())])
                        face_image = ImageTk.PhotoImage(face_image)
                        face_label = tk.Label(possible_threat_window, image=face_image)
                        face_label.image = face_image
                        face_label.pack()

            if person.alert_shown and not person.danger_alert and current_time - person.initial_time >= danger_duration:
                person.danger_alert = True

                danger_window = tk.Toplevel()
                danger_window.title("Riesgo LATENTE")
                danger_label = tk.Label(danger_window, text="Riesgo LATENTE", font=("Helvetica", 24), fg="red")
                danger_label.pack()

                def handle_falsa_alarma():
                    person.danger_alert = False
                    danger_window.destroy()

                falsa_alarma_button = tk.Button(danger_window, text="Falsa alarma", command=handle_falsa_alarma)
                falsa_alarma_button.pack()

                def handle_autoridades():
                    autoridades_window = tk.Toplevel()
                    autoridades_window.title("Modo AUXILIO")
                    autoridades_label = tk.Label(autoridades_window, text="Autoridades en camino", font=("Helvetica", 24), fg="red")
                    autoridades_label.pack()

                danger_label.after(10000, handle_autoridades)

        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image)
        label.configure(image=photo)
        label.image = photo

    label.after(10, update_frame, label, cap, persons, alert_duration, danger_duration)

def start_camera(alert_duration=20, danger_duration=40):
    cap = cv2.VideoCapture(0)
    persons = []
    root = tk.Tk()
    root.title("SASYR")
    label = tk.Label(root)
    label.pack()
    root.protocol("WM_DELETE_WINDOW", partial(stop_camera, root, cap))
    update_frame(label, cap, persons, alert_duration, danger_duration)
    root.mainloop()

def stop_camera(root, cap):
    cap.release()
    root.destroy()

start_camera()
