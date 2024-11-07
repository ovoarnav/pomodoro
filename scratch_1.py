import time
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import pickle
import pytesseract
import pyautogui
import numpy as np
from PIL import Image
from threading import Thread
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import spacy
import re  # Import for cleaning OCR output
import nltk
from nltk.corpus import words


# ========================== SETUP AND INITIALIZATION ==========================

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    print(f"Error loading NLP model: {e}")

# Set Tesseract path (update this path as necessary for Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Create directory for screenshots
if not os.path.exists('screenshots'):
    os.makedirs('screenshots')

# Placeholder for current tasks and screen activity log
active_tasks = []
screen_activity_log = []


# ========================== TASK MANAGEMENT FUNCTIONS ==========================

# Load saved task times from file (not visible on UI)
def load_task_times():
    try:
        with open("task_times.pkl", "rb") as f:
            task_times = pickle.load(f)
    except (FileNotFoundError, EOFError):
        task_times = {}
    return task_times


# Save task times to file
def save_task_times(task_times):
    with open("task_times.pkl", "wb") as f:
        pickle.dump(task_times, f)


# Add a new task, with task times saved locally but not displayed on UI
def add_task(tasks_menu, recommendation_label):
    task_name = simpledialog.askstring("New Task", "Enter task name:")
    if task_name:
        task_type = classify_task_type(task_name)
        recommended_time = predict_time(task_type)
        active_tasks.append((task_name, task_type, recommended_time))
        tasks_menu['values'] = [task[0] for task in active_tasks]
        recommendation_label.config(text=f"Recommended time for '{task_type}' task: {display_time(recommended_time)}")
        messagebox.showinfo("Task Added",
                            f"Task '{task_name}' ({task_type}) added with recommended time: {display_time(recommended_time)}")


# NLP-based task classification
def classify_task_type(task_name):
    doc = nlp(task_name)
    for token in doc:
        if token.lemma_ in ["study", "learn", "research", "read"]:
            return "Learning"
        elif token.lemma_ in ["build", "write", "create", "design"]:
            return "Creative"
    return "Administrative"


# ========================== DEEP LEARNING MODEL FOR TIME PREDICTIONS ==========================

# Build recommendation model
def build_recommendation_model():
    model = Sequential([
        Dense(64, activation='relu', input_shape=(1,)),
        Dense(32, activation='relu'),
        Dense(1, activation='linear')
    ])
    model.compile(optimizer=Adam(), loss='mse')
    return model


recommendation_model = build_recommendation_model()


# Predict time for task type using the deep learning model
def predict_time(task_type):
    task_data = {"Learning": [(1, 1800)], "Creative": [(1, 2400)], "Administrative": [(1, 1200)]}
    X = np.array([x[0] for x in task_data[task_type]])
    y = np.array([x[1] for x in task_data[task_type]])
    recommendation_model.fit(X, y, epochs=10, verbose=0)  # Train model with dummy data
    return int(recommendation_model.predict(np.array([[len(active_tasks)]])).flatten()[0])


# ========================== COUNTDOWN TIMER AND POMODORO FUNCTION ==========================

# Display time in MM:SS format
def display_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{int(mins):02d}:{int(secs):02d}"


# Countdown function for each session
def countdown(duration, timer_label, session_label, root, end_callback):
    if duration > 0:
        timer_label.config(text=display_time(duration))
        root.after(1000, countdown, duration - 1, timer_label, session_label, root, end_callback)
    else:
        timer_label.config(text="00:00")
        end_callback()


# Start the Pomodoro session
def start_pomodoro(root, study_time, short_break_time, long_break_time, cycles, selected_task, timer_label,
                   session_label, tasks_menu, task_label):
    session_data = []
    current_task = selected_task.get()
    completed_tasks = set()
    cycle_count = 0
    is_break = False
    task_times = load_task_times()

    # Capture screen activity every 30 seconds during the session
    def capture_screen_activity():
        while not is_break:
            screenshot = pyautogui.screenshot()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            screenshot_path = f'screenshots/screen_{timestamp}.png'
            screenshot.save(screenshot_path)
            analyze_screenshot(screenshot_path, screen_activity_log)
            time.sleep(30)

    def end_study_session():
        nonlocal cycle_count, is_break
        is_break = True
        task_completed = messagebox.askyesno("Session Complete", f"Did you complete the task '{current_task}'?")
        if task_completed:
            task_info = next((task for task in active_tasks if task[0] == current_task), None)
            if task_info:
                active_tasks.remove(task_info)
            completed_tasks.add(current_task)
            tasks_menu['values'] = [task[0] for task in active_tasks]
            task_times[current_task] = task_times.get(current_task, 0) + study_time

        save_task_times(task_times)

        if not active_tasks:
            show_summary(session_data, screen_activity_log)
        else:
            cycle_count += 1
            next_duration = short_break_time if cycle_count < cycles else long_break_time
            session_label.config(text="Break Time" if cycle_count < cycles else "Long Break")
            countdown(next_duration, timer_label, session_label, root, start_study_session)

    def start_study_session():
        nonlocal is_break
        is_break = False
        session_label.config(text="Study Time")

        screen_thread = Thread(target=capture_screen_activity)
        screen_thread.daemon = True
        screen_thread.start()

        countdown(study_time, timer_label, session_label, root, end_study_session)

    start_study_session()


# ========================== SCREEN TRACKING AND SUMMARY GENERATION ==========================

import nltk
from nltk.corpus import words

# Download the words corpus if not already available
nltk.download('words')
english_words = set(words.words())


# Clean and filter OCR text for readability, focusing on relevant info
def clean_ocr_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove excessive whitespace
    text = re.sub(r'[^\w\s.,!?-]', '', text)  # Remove special characters
    return text.strip()


# Function to determine if text is comprehensible (contains English words)
def is_comprehensible(text):
    words_in_text = text.split()
    word_count = sum(1 for word in words_in_text if word.lower() in english_words)
    return word_count / len(words_in_text) > 0.5 if words_in_text else False  # At least 50% of words should be valid


# Analyze screenshot and log activity if text is comprehensible
def analyze_screenshot(image_path, screen_activity_log):
    image = Image.open(image_path).convert("L")  # Convert to grayscale for faster OCR
    text = pytesseract.image_to_string(image)
    cleaned_text = clean_ocr_text(text)

    # Check if cleaned text is comprehensible
    if is_comprehensible(cleaned_text):
        # Get focused window title for coherence in activity logging
        window_title = pyautogui.getActiveWindowTitle() if hasattr(pyautogui, 'getActiveWindowTitle') else "Unknown"
        typing_detected = "Typing detected" if pyautogui.typewrite else "No typing detected"

        # Log screen activity if text is relevant
        screen_activity_log.append({
            "timestamp": datetime.datetime.now(),
            "window_title": window_title,
            "content": cleaned_text,
            "typing_activity": typing_detected
        })


# Generate structured summary based on session data and screen activity log
def generate_structured_summary(session_data, screen_activity_log):
    task_time_summary = {entry['task_type']: entry['time_spent'] for entry in session_data}

    # Summarize time and interactions per page/application
    page_durations = {}
    for entry in screen_activity_log:
        page = entry["window_title"]
        page_durations[page] = page_durations.get(page, 0) + 1  # Increment by 1 for each capture cycle

    summary = "Session Summary:\n\nTask Time Breakdown:\n"
    for task_type, total_time in task_time_summary.items():
        summary += f" - {task_type}: {display_time(total_time)}\n"

    # Screen Activity Highlights
    summary += "\nDetailed Screen Activity Highlights:\n"
    for entry in screen_activity_log:
        timestamp = entry["timestamp"].strftime("%H:%M:%S")
        page = entry["window_title"]
        activity = entry["content"]
        typing = entry["typing_activity"]

        summary += (f"At {timestamp} on '{page}':\n"
                    f" {activity[:100]}{'...' if len(activity) > 100 else ''}\n"
                    f" - Typing Status: {typing}\n\n")

    # Add information on time spent per page/application
    summary += "\nPage/Application Focus Summary:\n"
    for page, duration in page_durations.items():
        time_spent = display_time(duration * 30)  # Assuming 30 seconds per capture interval
        summary += f" - {page}: Focused for {time_spent}\n"

    return summary


# Show summary at the end of all sessions
def show_summary(session_data, screen_activity_log):
    summary_text = generate_structured_summary(session_data, screen_activity_log)
    summary_window = tk.Toplevel()
    summary_window.title("Session Summary")
    label = tk.Label(summary_window, text=summary_text, font=("Arial", 12), justify="left", wraplength=380)
    label.pack(padx=10, pady=10)


# ========================== MAIN APPLICATION INTERFACE ==========================

def main_window():
    root = tk.Tk()
    root.title("Task and Pomodoro Manager")
    root.wm_attributes("-topmost", 1)

    # Timer settings and other UI elements
    timer_settings_frame = tk.Frame(root)
    timer_settings_frame.pack(pady=20)

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

    selected_task = tk.StringVar()
    tasks_menu = ttk.Combobox(root, textvariable=selected_task, font=("Arial", 12), width=20)
    tasks_menu['values'] = [task[0] for task in active_tasks]
    tk.Label(timer_settings_frame, text="Select Task:", font=("Arial", 12)).grid(row=4, column=0, padx=5, pady=5)

    recommendation_label = tk.Label(root, text="", font=("Arial", 10), fg="blue")
    recommendation_label.pack(pady=5)

    add_task_button = tk.Button(root, text="Add Task", command=lambda: add_task(tasks_menu, recommendation_label),
                                font=("Arial", 14), width=20)
    add_task_button.pack(pady=5)
    session_label = tk.Label(root, text="", font=("Arial", 16))
    timer_label = tk.Label(root, text="00:00", font=("Arial", 48))
    task_label = tk.Label(root, text="", font=("Arial", 14))

    task_label.pack(pady=5)
    tasks_menu.pack(pady=10)

    def start_pomodoro_action():
        try:
            study_time = int(study_time_entry.get()) * 60
            short_break = int(short_break_entry.get()) * 60
            long_break = int(long_break_entry.get()) * 60
            cycles = int(cycles_entry.get())
            if not selected_task.get():
                messagebox.showwarning("No Task Selected", "Please select a task to start.")
                return

            timer_settings_frame.pack_forget()
            start_pomodoro_button.pack_forget()
            add_task_button.pack_forget()
            session_label.config(text="Study Time")
            session_label.pack(pady=10)
            timer_label.config(text="00:00")
            timer_label.pack(pady=20)
            task_label.config(text=f"Task: {selected_task.get()}")
            start_pomodoro(root, study_time, short_break, long_break, cycles, selected_task, timer_label, session_label,
                           tasks_menu, task_label)

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for all Pomodoro settings.")

    start_pomodoro_button = tk.Button(root, text="Start Pomodoro", command=start_pomodoro_action, font=("Arial", 14),
                                      width=20)
    start_pomodoro_button.pack(pady=10)
    root.geometry("400x500")
    root.mainloop()


# Run the main application
if __name__ == "__main__":
    main_window()