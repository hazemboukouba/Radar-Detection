import tkinter as tk
from tkinter import ttk, messagebox
import math
import serial
import threading
import winsound

def check_serial_connection():
    try:
        ser = serial.Serial('COM8', baudrate=115200, timeout=1)
        return ser
    except serial.SerialException as e:
        messagebox.showerror("Erreur", f"Impossible de se connecter au port série: {e}")
        return None

# Connexion série
ser = check_serial_connection()
if not ser:
    exit()

# - PARAMÈTRES GLOBAUX -
radar_radius = 250  # Rayon du radar en pixels
max_distance = 20   # Distance maximale affichée en cm
detected_objects = 0  # Compteur d'objets détectés

# - INTERFACE GRAPHIQUE -
root = tk.Tk()
root.title("Radar Ultrasonique")
root.geometry("900x600")
root.config(bg="#2f2f2f")

# Création du canvas pour le radar
canvas = tk.Canvas(root, width=radar_radius * 2 + 50, height=radar_radius * 2 + 50, bg="#1e1e2f")
canvas.pack(pady=20)

# Tableau de bord
dashboard_frame = tk.Frame(root, bg="#1e1e2f", relief="solid", bd=2)
dashboard_frame.pack(fill="x", pady=20, padx=20)

# Titre du projet et nom de l'auteur
title_label = tk.Label(root, text="Projet : Radar Ultrasonique ", fg="white", bg="#2f2f2f", font=("Arial", 18, "bold"))
title_label.pack(pady=10)

author_label = tk.Label(root, text="By: hazem Boukouba ", fg="white", bg="#2f2f2f", font=("Arial", 14, "italic"))
author_label.pack(pady=5)


distance_label = tk.Label(dashboard_frame, text="Distance : 0 cm", fg="white", bg="#1e1e2f", font=("Arial", 14, "bold"))
distance_label.pack(side="left", padx=20)

angle_label = tk.Label(dashboard_frame, text="Angle : 0°", fg="white", bg="#1e1e2f", font=("Arial", 14, "bold"))
angle_label.pack(side="left", padx=20)

progress = ttk.Progressbar(dashboard_frame, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
progress.pack(side="right", padx=20)

# Style du progrès
style = ttk.Style()
style.configure("TProgressbar", thickness=25, background="#4caf50", troughcolor="#ccc")



def draw_radar_grid():
    """Dessine la grille du radar."""
    for i in range(1, 6):
        radius = (radar_radius // 5) * i
        canvas.create_oval(
            radar_radius - radius + 25,
            radar_radius - radius + 25,
            radar_radius + radius + 25,
            radar_radius + radius + 25,
            outline="green"
        )
    for angle in range(0, 360, 15):  # De 0° à 180° par pas de 30°
        angle_rad = math.radians(angle)
        x_end = radar_radius + radar_radius * math.cos(angle_rad) + 25
        y_end = radar_radius - radar_radius * math.sin(angle_rad) + 25

        canvas.create_line(
            radar_radius + 25, radar_radius + 25, x_end, y_end,
            fill="green", dash=(3, 3)  # Ligne pointillée pour effet radar
        )

# - COMMUNICATION SÉRIE -
def read_serial_data():
    """Lit les données du port série en arrière-plan."""
    global detected_objects

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if "Angle:" in line and "Distance:" in line:
                parts = line.split(",")
                angle = int(parts[0].split(":")[1].strip())
                distance = int(parts[1].split(":")[1].strip())

                # Mettre à jour l'interface graphique
                root.after(0, update_radar, angle, distance)
        except Exception as e:
            print(f"Erreur lors de la lecture du port série : {e}")

# - MISE À JOUR DU RADAR -
def update_radar(angle, distance):
    """Met à jour l'affichage du radar."""
    global detected_objects

    canvas.delete("needle")
    canvas.delete("object")

    angle_rad = math.radians(angle)
    x_end = radar_radius + radar_radius * math.cos(angle_rad) + 25
    y_end = radar_radius - radar_radius * math.sin(angle_rad) + 25

    # Balayage du radar (aiguille)
    canvas.create_line(
        radar_radius + 25, radar_radius + 25, x_end, y_end,
        fill="green", width=3, tags="needle"
    )

    # Détection d’objet
    if 0 < distance <= max_distance:
        obj_radius = (distance / max_distance) * radar_radius
        x_obj = radar_radius + obj_radius * math.cos(angle_rad) + 25
        y_obj = radar_radius - obj_radius * math.sin(angle_rad) + 25

        # Effet glow
        for i in range(3):
            canvas.create_oval(
                x_obj - (8 + i), y_obj - (8 + i), x_obj + (8 + i), y_obj + (8 + i),
                outline="red", width=1, tags="object"
            )

        # Cercle de détection
        canvas.create_oval(
            x_obj - 8, y_obj - 8, x_obj + 8, y_obj + 8,
            fill="red", tags="object"
        )

        detected_objects += 1

        # Alerte sonore avec intensité en fonction de la distance
        beep_freq = max(500, 2000 - (distance * 100))
        beep_duration = max(50, 300 - (distance * 10))
        winsound.Beep(beep_freq, beep_duration)

    # Mise à jour des labels
    distance_label.config(text=f"Distance : {distance} cm")
    angle_label.config(text=f"Angle : {angle}°")
    progress['value'] = (angle / 180) * 100

# -DÉMARRER LE RADAR
def start_radar():
    """Démarre la lecture série en arrière-plan."""
    if not ser:
        messagebox.showerror("Erreur", "Port série non disponible.")
        return
    threading.Thread(target=read_serial_data, daemon=True).start()

# - BOUTON POUR LANCER LE RADAR -
start_button = tk.Button(root, text="Lancer Radar", command=start_radar, bg="#4caf50", fg="white",
                         font=("Arial", 16, "bold"), relief="raised", bd=3)
start_button.pack(pady=5)

# Dessiner la grille
draw_radar_grid()

# Lancer l'interface
root.mainloop()

# Fermer le port série à la fermeture du programme
ser.close()
