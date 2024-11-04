import time
import datetime
import psutil  # For tracking active application usage
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image
import os
import pandas as pd
import threading
import matplotlib.pyplot as plt
import pytesseract
from transformers import pipeline
import numpy as np
import pickle  # For saving and loading tasks

# Ensure pytesseract is installed and configured
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# Load spaCy NLP model and initialize Hugging Face generator
text_generator = pipeline("text-generation", model="gpt2")

# Global list to store tasks
tasks = []

# Load saved tasks if available
def load_tasks():
    global tasks
    try:
        with open("tasks.pkl", "rb") as f:
            tasks = pickle.load(f)
    except (FileNotFoundError, EOFError):
        tasks = []  # Start with an empty list if file not found or empty

# Save tasks to file
def save_tasks():
    with open("tasks.pkl", "wb") as f:
        pickle.dump(tasks, f)

# Directory to save screenshots
if not os.path.exists('screenshots'):
    os.makedirs('screenshots')

# Global variable to control recording state
recording = True

# Function to take and save a screenshot
def capture_screenshot(interval, duration, screen_activity_log):
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < duration:
        if recording:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            screenshot = pyautogui.screenshot()
            screenshot_path = f'screenshots/screen_{timestamp}.png'
            screenshot.save(screenshot_path)
            print(f"Captured screenshot at {timestamp}")
            analyze_screenshot(screenshot_path, screen_activity_log)
        time.sleep(interval)  # Adjust interval for more or less frequent captures

# Function to analyze a screenshot using OCR
def analyze_screenshot(image_path, screen_activity_log):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    screen_activity_log.append((datetime.datetime.now(), text))

# Function to generate a descriptive summary using generative AI
def generate_ai_summary(session_data):
    prompt = "Summarize the user's productivity session based on the following data:\n\n"
    for entry in session_data:
        prompt += f"Task: {entry['task']}, Time Spent: {int(entry['time_spent'] // 60)} min {int(entry['time_spent'] % 60)} sec, "
        prompt += "Screen Activity:\n"
        for timestamp, text in entry["screen_activity"]:
            prompt += f"  - {timestamp.strftime('%H:%M:%S')}: {text}\n"
        prompt += "\n"

    prompt += "\nProvide insights on productivity and any potential areas for improvement.\n"
    ai_summary = text_generator(prompt, max_length=250, num_return_sequences=1)[0]["generated_text"]
    return ai_summary

# Function to show a summary of time and screen activity
def show_summary(session_data):
    ai_summary = generate_ai_summary(session_data)
    summary_window = tk.Toplevel()
    summary_window.title("Session Summary")
    label = tk.Label(summary_window, text=f"AI Summary:\n\n{ai_summary}", font=("Arial", 12), justify="left",
                     wraplength=380)
    label.pack(padx=10, pady=10)

# Main Pomodoro function with cycle logic and task tracking
def start_pomodoro(root, study_time, short_break_time, long_break_time, cycles, selected_task, timer_label,
                   session_label):
    # Update the UI to display timer and task info
    session_data = []  # Store data for each session
    screen_activity_log = []

    def end_cycle():
        summary_data = {
            "task": selected_task.get(),
            "time_spent": study_time,
            "screen_activity": screen_activity_log.copy()
        }
        session_data.append(summary_data)
        screen_activity_log.clear()

        if messagebox.askyesno("Session Complete", "Do you want more time?"):
            countdown(study_time, timer_label, session_label, "Study Time", root, screen_activity_log, session_data,
                      selected_task.get(), "Study", end_cycle)
        else:
            if len(session_data) >= cycles:
                show_summary(session_data)
            else:
                countdown(short_break_time if (len(session_data) % cycles) else long_break_time, timer_label,
                          session_label, "Break Time", root, screen_activity_log, session_data, selected_task.get(),
                          "Break", end_cycle)

    # Start the screen tracking in a separate thread
    tracking_thread = threading.Thread(target=capture_screenshot, args=(5, study_time, screen_activity_log), daemon=True)
    tracking_thread.start()

    # Start the countdown
    countdown(study_time, timer_label, session_label, "Study Time", root, screen_activity_log, session_data,
              selected_task.get(), "Study", end_cycle)

# Function to display time in a readable format
def display_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"

# Main window for task and time management
def main_window():
    root = tk.Tk()
    root.title("Task and Pomodoro Manager")

    # Load tasks initially
    load_tasks()

    # Timer settings frame
    timer_settings_frame = tk.Frame(root)
    timer_settings_frame.pack(pady=20)

    # Input fields
    tk.Label(timer_settings_frame, text="Study Time (min):", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
    study_time_entry = tk.Entry(timer_settings_frame, font=("Arial", 12), width=5)
    study_time_entry.grid(row=0, column=1, padx=5)

    tk.Label(timer_settings_frame, text="Short Break (min):", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5)
    short_break_entry = tk.Entry(timer_settings_frame, font=("Arial", 12), width=5)
    short_break_entry.grid(row=1, column=1, padx=5)

    tk.Label(timer_settings_frame, text="Long Break (min):", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=5)
    long_break_entry = tk.Entry(timer_settings_frame, font=("Arial", 12), width=5)
    long_break_entry.grid(row=2, column=1, padx=5)

    tk.Label(timer_settings_frame, text="Cycles:", font=("Arial", 12)).grid(row=3, column=0, padx=5, pady=5)
    cycles_entry = tk.Entry(timer_settings_frame, font=("Arial", 12), width=5)
    cycles_entry.grid(row=3, column=1, padx=5)

    # Task selection dropdown
    task_label = tk.Label(root, text="Select Task:", font=("Arial", 14))
    task_label.pack(pady=5)
    selected_task = tk.StringVar()
    tasks_menu = ttk.Combobox(root, textvariable=selected_task, values=[task[0] for task in tasks], font=("Arial", 14))
    tasks_menu.pack(pady=5)

    # Button to add tasks
    add_task_button = tk.Button(root, text="Add Task", command=lambda: add_task(tasks_menu), font=("Arial", 14),
                                width=20)
    add_task_button.pack(pady=5)

    # Session and Timer labels for countdown
    session_label = tk.Label(root, text="Session Type", font=("Arial", 16))
    session_label.pack(pady=10)
    timer_label = tk.Label(root, text="00:00", font=("Arial", 48))
    timer_label.pack(pady=20)

    # Start Pomodoro button
    def start_pomodoro_action():
        try:
            study_time = int(study_time_entry.get()) * 60
            short_break = int(short_break_entry.get()) * 60
            long_break = int(long_break_entry.get()) * 60
            cycles = int(cycles_entry.get())
            if not selected_task.get():
                messagebox.showwarning("No Task Selected", "Please select a task to start.")
                return
            start_pomodoro(root, study_time, short_break, long_break, cycles, selected_task, timer_label, session_label)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for all Pomodoro settings.")

    start_pomodoro_button = tk.Button(root, text="Start Pomodoro", command=start_pomodoro_action, font=("Arial", 14),
                                      width=20)
    start_pomodoro_button.pack(pady=10)

    # Set window size
    root.geometry("400x500")
    root.mainloop()

# Run the main window
if __name__ == "__main__":
    main_window()
