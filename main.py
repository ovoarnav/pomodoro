import tkinter as tk
from tkinter import messagebox
from UX import main_window  # The main task and Pomodoro setup window
from Base Function.py import pomodoro, show_final_congratulations  # Core timer functions
from AIFeatures import initialize_ai, classify_task_type, track_screen_activity  # AI features
import datetime

# Initialize any AI components
initialize_ai()

# Function to start the Pomodoro timer with AI-enhanced insights and tracking
def start_pomodoro_with_ai(study_time, short_break, long_break, cycles, tasks):
    # Initialize data storage for analytics
    analytics_data = []
    time_adjustments = []

    root = tk.Tk()  # Pomodoro timer window
    root.title("AI-Enhanced Pomodoro Timer")

    session_label = tk.Label(root, text="", font=("Arial", 20))
    session_label.pack(pady=5)
    label = tk.Label(root, text="", font=("Arial", 60))
    label.pack(pady=5)
    task_label = tk.Label(root, text="Task: None", font=("Arial", 20))
    task_label.pack(pady=5)

    current_task_index = 0
    while current_task_index < len(tasks):
        task_name = tasks[current_task_index]
        task_type = classify_task_type(task_name)  # Classify task type
        ai_recommendation = messagebox.askyesno(
            "AI Timer Suggestion",
            f"The task '{task_name}' is classified as '{task_type}'. Use AI to set timer?"
        )
        if ai_recommendation:
            # Adjust study time based on task type
            study_time = 1800 if task_type == "Learning" else 1200  # Example AI-based suggestion

        task_label.config(text=f"Task: {task_name}")

        # Run each Pomodoro cycle
        for i in range(1, cycles + 1):
            # Countdown for study time
            time_spent = pomodoro(study_time, short_break, long_break, cycles, tasks, label, task_label, session_label, root, None)
            # Screen tracking during the Pomodoro session
            screen_data = track_screen_activity(time_spent)

            # Survey after each cycle
            task_completed = fullscreen_alert(root, task_name)
            adjusted_time = adjust_time_based_on_performance(time_spent, study_time)

            if task_completed == "Extend":
                study_time += 5  # Extend for testing purposes
            elif task_completed:
                # Record session data
                analytics_data.append({
                    'task': task_name,
                    'time_spent': time_spent,
                    'completed': True,
                    'screen_activity': screen_data
                })
                time_adjustments.append({
                    'task': task_name,
                    'previous_time': study_time,
                    'new_time': adjusted_time
                })

                # Increment task index to move to the next task
                current_task_index += 1
                if current_task_index >= len(tasks):
                    show_final_congratulations(root, analytics_data, time_adjustments)
                    root.destroy()
                    return  # End Pomodoro session if all tasks are complete
            else:
                # Save data if task was incomplete
                analytics_data.append({
                    'task': task_name,
                    'time_spent': time_spent,
                    'completed': False,
                    'screen_activity': screen_data
                })
                break

            # Handle short or long breaks
            if i == cycles:
                countdown(long_break, label, session_label, "Long Break", root)
            else:
                countdown(short_break, label, session_label, "Short Break", root)

    label.config(text="Pomodoro session complete!")
    session_label.config(text="Well done!")
    root.update()

# Main control to open the primary interface and manage the AI-enhanced Pomodoro timer
def main():
    # Open the task management window
    main_window()

    # Sample tasks and Pomodoro settings for testing
    tasks = ["Study for math", "Write report", "Research project"]
    study_time = 25  # minutes
    short_break = 5  # minutes
    long_break = 15  # minutes
    cycles = 4  # Number of cycles before a long break

    # Start the Pomodoro with AI features
    start_pomodoro_with_ai(study_time, short_break, long_break, cycles, tasks)

if __name__ == "__main__":
    main()
