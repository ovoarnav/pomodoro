import time
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import spacy

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# List of keywords for learning and doing tasks
learning_keywords = ['study', 'learn', 'research', 'read']
doing_keywords = ['build', 'write', 'create', 'finish', 'develop', 'complete']

# Function to classify tasks based on keywords (Learning or Doing)
def classify_task(task_description):
    doc = nlp(task_description)
    for token in doc:
        if token.lemma_ in learning_keywords:
            return "Learning"
        elif token.lemma_ in doing_keywords:
            return "Doing"
    return "Doing"  # Default to "Doing" if no learning words are found

# Function to format time for display
def display_time(seconds):
    mins, secs = divmod(seconds, 60)
    return '{:02d}:{:02d}'.format(mins, secs)

# Countdown function for study/break sessions
def countdown(duration, label, session_label, session_type, root):
    session_label.config(text=f"{session_type}")  # Set session type (Study, Short Break, etc.)
    start_time = datetime.datetime.now()
    while duration > 0:
        label.config(text=display_time(duration))  # Show remaining time as the main focus
        root.update()
        time.sleep(1)
        duration -= 1
    label.config(text="00:00")
    end_time = datetime.datetime.now()
    return (end_time - start_time).total_seconds()  # Return total time spent

# Function to handle fullscreen alert when a session ends
def fullscreen_alert(root, task):
    alert_window = tk.Toplevel()
    alert_window.attributes("-fullscreen", True)
    alert_window.configure(bg="green")
    alert_window.lift()  # Bring to the front
    alert_window.focus_force()  # Make sure it gains focus
    label = tk.Label(alert_window, text="Timer Done!", font=("Arial", 50), bg="green", fg="white")
    label.pack(expand=True)

    # Productivity Survey
    def productivity_survey():
        finished = messagebox.askyesno("Productivity Survey", f"Did you finish the task '{task}'?")
        if finished:
            return True
        else:
            more_time = messagebox.askyesno("Need More Time?", "Would you like more time to complete this task?")
            return "Extend" if more_time else False

    result = productivity_survey()
    alert_window.destroy()
    return result

# Analytics data storage
analytics_data = []

# Track if task was switched
task_switch_data = []

# Function to display final congratulations and analytics
def show_final_congratulations(root, analytics_data):
    congrats_window = tk.Toplevel()
    congrats_window.attributes("-fullscreen", True)
    congrats_window.configure(bg="blue")
    congrats_window.lift()
    congrats_window.focus_force()

    # Display summary of analytics
    summary = "\n".join([f"Task: {data['task']} | Time Spent: {data['time_spent']} seconds | Completed: {data['completed']}"
                         for data in analytics_data])
    label = tk.Label(congrats_window, text=f"Congratulations on not being a piece of shit!\n\nAnalytics Summary:\n{summary}",
                     font=("Arial", 20), bg="blue", fg="white")
    label.pack(expand=True)
    congrats_window.after(10000, congrats_window.destroy)  # Close after 10 seconds

# Pomodoro timer function with cycle logic and task tracking
def pomodoro(study_time, short_break_time, long_break_time, cycles, tasks, label, task_label, session_label, root, task_dropdown):
    current_cycle = 0
    task_index = 0
    total_tasks = len(tasks)

    while task_index < total_tasks:
        task_description = tasks[task_index]
        task_type = classify_task(task_description)

        # Ask if user wants AI to set the timer
        use_ai = messagebox.askyesno("Timer Suggestion", f"The task '{task_description}' is classified as {task_type}. Would you like me to set the timer for you?")
        if use_ai:
            study_time = 30 * 60 if task_type == "Learning" else 20 * 60  # Example time suggestions

        for i in range(1, cycles + 1):
            current_cycle += 1

            # Update task label
            task_label.config(text=f"Task: {tasks[task_index]}")

            # Run the study session
            time_spent = countdown(study_time, label, session_label, "Study Time", root)

            # Show fullscreen alert and handle task completion
            task_completed = fullscreen_alert(root, tasks[task_index])

            if task_completed == "Extend":
                study_time += 10 * 60  # Extend by 10 minutes
            elif task_completed:
                # Mark task as completed and strike through in dropdown
                tasks[task_index] = f"~~{tasks[task_index]}~~"
                task_dropdown['values'] = tasks  # Update dropdown values
                task_dropdown.update()

                # Track analytics data
                analytics_data.append({
                    'task': task_description,
                    'time_spent': time_spent,
                    'completed': True
                })
                task_index += 1  # Move to the next task only if the current one is completed
                if task_index >= total_tasks:
                    show_final_congratulations(root, analytics_data)  # Show congratulations when all tasks are done
                    break
            else:
                # Record unfinished task in analytics
                analytics_data.append({
                    'task': task_description,
                    'time_spent': time_spent,
                    'completed': False
                })
                break

            # Break session logic (short break vs long break)
            if i == cycles:
                countdown(long_break_time, label, session_label, "Long Break", root)
            else:
                countdown(short_break_time, label, session_label, "Short Break", root)

        if task_index >= total_tasks:
            break

    label.config(text="Pomodoro session complete!")
    session_label.config(text="Well done!")
    root.update()

# GUI window to run the Pomodoro timer
def run_pomodoro_gui():
    root = tk.Tk()
    root.title("Pomodoro Timer")

    # Input tasks from the user
    tasks = input("Enter your tasks, separated by commas: ").split(',')

    # Create a dropdown for task selection as a clickable circle
    selected_task = tk.StringVar(root)
    selected_task.set(tasks[0])  # Set default task

    # Session label to display session type (Study, Short Break, Long Break)
    session_label = tk.Label(root, text="", font=("Arial", 20))
    session_label.pack(pady=5)

    # Timer label to display countdown time (Main Focus)
    label = tk.Label(root, text="", font=("Arial", 60))
    label.pack(pady=5)

    # Task label to display the current task
    task_label = tk.Label(root, text=f"Task: {selected_task.get()}", font=("Arial", 20))
    task_label.pack(pady=5)

    # Create a small circle button for dropdown
    def show_dropdown(event):
        task_dropdown.place(x=circle_button.winfo_x(), y=circle_button.winfo_y() + 30)

    def hide_dropdown(event):
        root.after(500, lambda: task_dropdown.place_forget())

    circle_button = tk.Label(root, text="◯", font=("Arial", 20))
    circle_button.place(x=20, y=20)  # Position the circle button next to the timer
    circle_button.bind("<Enter>", show_dropdown)  # Show dropdown on hover
    task_dropdown = ttk.Combobox(root, textvariable=selected_task, values=tasks)
    task_dropdown.place_forget()  # Initially hidden

    # Set window size and position to fit all elements
    root.geometry("400x300")
    screen_width = root.winfo_screenwidth()
    window_width = 400
    x_position = int((screen_width / 2) - (window_width / 2))
    root.geometry(f"400x300+{x_position}+0")

    # Update task label when dropdown selection changes
    task_dropdown.bind("<<ComboboxSelected>>", lambda e: task_label.config(text=f"Task: {selected_task.get()}"))
    task_dropdown.bind("<Leave>", hide_dropdown)  # Hide when mouse leaves dropdown

    # User input for study, short break, long break, and cycles (in minutes)
    study_minutes = float(input("Enter study time in minutes: "))
    short_break_minutes = float(input("Enter short break time in minutes: "))
    long_break_minutes = float(input("Enter long break time in minutes: "))
    cycles = int(input("Enter number of study/rest cycles before a long break: "))

    # Convert minutes to seconds
    study_seconds = int(study_minutes * 60)
    short_break_seconds = int(short_break_minutes * 60)
    long_break_seconds = int(long_break_minutes * 60)

    # Start the Pomodoro timer
    root.after(1000, lambda: pomodoro(study_seconds, short_break_seconds, long_break_seconds, cycles,
                                      tasks, label, task_label, session_label, root, task_dropdown))

    root.mainloop()

# Run the app
if __name__ == "__main__":
    run_pomodoro_gui()
