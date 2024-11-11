import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json
import tensorflow as tf
import numpy as np
from datetime import datetime
import os

# Load or initialize task data
if os.path.exists("tasks.json"):
    with open("tasks.json", "r") as file:
        tasks_data = json.load(file)
else:
    tasks_data = {}


def save_tasks():
    """Saves tasks data to tasks.json"""
    with open("tasks.json", "w") as file:
        json.dump(tasks_data, file, indent=4)


# Create or load the deep learning model for recommending time
def create_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(32, activation='relu', input_shape=(3,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='linear')
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


model = create_model()
if os.path.exists("trained_model_weights.weights.h5"):
    model.load_weights("trained_model_weights.weights.h5")


class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Clock")
        self.root.attributes('-topmost', True)

        # Initialize model as a class attribute
        self.model = model

        # Initialize variables
        self.break_time = tk.IntVar()
        self.long_break_time = tk.IntVar()
        self.cycles = tk.IntVar()
        self.current_task = tk.StringVar()
        self.timer_label = tk.StringVar(value="00:00")
        self.task_list = []  # List to hold all tasks with time
        self.active_tasks = []  # List to hold active tasks for dropdown
        self.completed_tasks = []  # Track completed tasks for analytics
        self.timer = None
        self.time_left = 0
        self.current_cycle = 1
        self.session_type = tk.StringVar(value="Study")
        self.start_time = None

        # Initial setup menu
        self.setup_menu()

    def setup_menu(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Initial menu layout without the redundant Study Time input
        tk.Label(self.root, text="Enter Short Break (min):").pack()
        tk.Entry(self.root, textvariable=self.break_time).pack()

        tk.Label(self.root, text="Enter Long Break (min):").pack()
        tk.Entry(self.root, textvariable=self.long_break_time).pack()

        tk.Label(self.root, text="Cycles before Long Break:").pack()
        tk.Entry(self.root, textvariable=self.cycles).pack()

        tk.Label(self.root, text="Add Task:").pack()
        self.task_entry = tk.Entry(self.root)
        self.task_entry.pack()
        tk.Button(self.root, text="Add Task with Custom Time", command=self.add_task).pack()
        tk.Button(self.root, text="Add Task with AI-Recommended Time", command=self.add_task_with_ai).pack()

        tk.Button(self.root, text="Start Pomodoro", command=self.start_pomodoro).pack()

    def add_task(self):
        task_name = self.task_entry.get()
        if task_name:
            task_time = simpledialog.askinteger("Task Study Time", f"Enter study time for '{task_name}' in minutes:",
                                                parent=self.root)
            if task_time:
                self.task_list.append((task_name, task_time))
                self.active_tasks.append((task_name, task_time))
                messagebox.showinfo("Task Added", f"Task '{task_name}' added with {task_time} minutes.")
                self.task_entry.delete(0, tk.END)

    def add_task_with_ai(self):
        task_name = self.task_entry.get()
        if task_name:
            recommended_time = self.recommend_time(task_name)
            self.task_list.append((task_name, recommended_time))
            self.active_tasks.append((task_name, recommended_time))
            messagebox.showinfo("Task Added",
                                f"Task '{task_name}' added with AI-recommended time of {recommended_time} minutes.")
            self.task_entry.delete(0, tk.END)

    def recommend_time(self, task_name):
        """Recommend time for a task based on past data using AI model."""
        if task_name in tasks_data:
            # Scale input features to match training scale (e.g., convert to minutes if needed)
            study_time = tasks_data[task_name]["study_time"] / 60
            break_time = tasks_data[task_name]["break_time"] / 60
            long_break_time = tasks_data[task_name]["long_break_time"] / 60
            features = np.array([[study_time, break_time, long_break_time]])

            # Model prediction and scaling to get output in minutes
            recommended_time = model.predict(features).item() * 60  # Scale up if needed

            # Ensure the recommended time is reasonable (e.g., at least 1 minute)
            recommended_time = max(1, int(recommended_time))

            # Show the recommended time in a message box
            messagebox.showinfo("Recommendation",
                                f"Recommended time for '{task_name}': {recommended_time} minutes.")

            return recommended_time
        else:
            # Notify if no data available
            messagebox.showinfo("No Data Available",
                                f"No data available for '{task_name}'. Please use a customized timer.")
            return None

    def start_pomodoro(self):
        if not self.active_tasks:
            messagebox.showwarning("No Tasks", "Please add at least one task before starting.")
            return
        if self.break_time.get() == 0 or self.long_break_time.get() == 0:
            messagebox.showwarning("Incomplete Setup", "Please enter break times.")
            return

        self.load_next_task()

    def load_next_task(self):
        """Load the next task from the active tasks list."""
        if not self.active_tasks:
            self.show_analytics()
            return

        task_name, task_time = self.active_tasks[0]  # Keep task in list until marked as complete
        self.current_task.set(task_name)
        self.time_left = task_time * 60  # Convert minutes to seconds
        self.current_cycle = 1
        self.session_type.set("Study")
        self.start_time = datetime.now()
        self.timer_screen()
        self.update_timer()

    def timer_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, textvariable=self.session_type, font=("Helvetica", 16)).pack()
        tk.Label(self.root, textvariable=self.timer_label, font=("Helvetica", 36)).pack()

        # Dropdown menu for active tasks
        task_menu = ttk.OptionMenu(self.root, self.current_task, self.current_task.get(),
                                   *[task[0] for task in self.active_tasks], command=self.change_task)
        task_menu.pack()

        tk.Button(self.root, text="End Task", command=self.end_task).pack()

    def change_task(self, selected_task):
        """Handle task change mid-session without removing from active list."""
        for task_name, task_time in self.task_list:
            if task_name == selected_task:
                self.current_task.set(task_name)
                self.time_left = task_time * 60  # Update time with task's study time
                self.start_time = datetime.now()  # Reset start time for new task
                break

    def end_task(self):
        if self.timer:
            self.root.after_cancel(self.timer)
            self.timer = None

        end_time = datetime.now()
        actual_duration = int((end_time - self.start_time).total_seconds())

        if messagebox.askyesno("End Task", f"Did you complete the task '{self.current_task.get()}'?"):
            self.completed_tasks.append(self.current_task.get())
            self.log_task(self.current_task.get(), "completed", actual_duration)
            self.active_tasks = [task for task in self.active_tasks if task[0] != self.current_task.get()]
        else:
            self.log_task(self.current_task.get(), "not_completed", actual_duration)

        if self.active_tasks:
            self.load_next_task()
        else:
            messagebox.showinfo("Pomodoro", "All tasks completed!")
            self.show_analytics()
            self.reset_timer()

    def reset_timer(self):
        self.timer_label.set("00:00")
        self.setup_menu()

    def update_timer(self):
        if self.time_left <= 0:
            self.switch_sessions()
        else:
            minutes, seconds = divmod(self.time_left, 60)
            self.timer_label.set(f"{minutes:02}:{seconds:02}")
            self.time_left -= 1
            self.timer = self.root.after(1000, self.update_timer)

    def switch_sessions(self):
        if self.session_type.get() == "Study":
            if self.current_cycle < self.cycles.get():
                self.time_left = self.break_time.get() * 60
                self.session_type.set("Short Break")
                self.current_cycle += 1
            else:
                self.time_left = self.long_break_time.get() * 60
                self.session_type.set("Long Break")
                self.current_cycle = 1
        else:
            self.time_left = self.get_study_time(self.current_task.get()) * 60
            self.session_type.set("Study")
        self.update_timer()

    def retrain_model(self):
        X = []
        y = []

        # Prepare data for training from tasks_data
        for task_name, data in tasks_data.items():
            # Ensure we have the necessary data
            if "time_adjustments" in data and "study_time" in data:
                # Scale input features for the model
                features = [data["study_time"] / 60, data["break_time"] / 60, data["long_break_time"] / 60]

                # Add each time adjustment as a separate training example
                for adjustment in data["time_adjustments"]:
                    X.append(features)  # Input features
                    y.append(adjustment / 60)  # Target output (scaled)

        # Train the model if there's enough data
        if X and y:
            X = np.array(X)
            y = np.array(y)

            # Train the model on the prepared data
            self.model.fit(X, y, epochs=5, verbose=1)  # Set verbose=1 for progress output

            # Save the trained weights to a file
            self.model.save_weights("trained_model_weights.h5")
            print("Model weights saved to 'trained_model_weights.h5'")
        else:
            print("Not enough data to retrain the model.")

    def log_task(self, task_name, status, actual_duration):
        if task_name not in tasks_data:
            tasks_data[task_name] = {
                "study_time": self.get_study_time(task_name),
                "break_time": self.break_time.get(),
                "long_break_time": self.long_break_time.get(),
                "cycles": self.cycles.get(),
                "completed": 0,
                "attempts": 0,
                "time_adjustments": []  # Ensure time_adjustments is initialized here
            }

        # Ensure 'time_adjustments' exists for tasks that might not have it
        if "time_adjustments" not in tasks_data[task_name]:
            tasks_data[task_name]["time_adjustments"] = []

        tasks_data[task_name]["attempts"] += 1
        if status == "completed":
            tasks_data[task_name]["completed"] += 1
            tasks_data[task_name]["time_adjustments"].append(actual_duration)  # Log actual time spent
        tasks_data[task_name]["last_completed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_tasks()

    def get_study_time(self, task_name):
        return tasks_data.get(task_name, {}).get("study_time", 25)

    def show_analytics(self):
        analytics = "Task Time Changes:\n"
        for task, data in tasks_data.items():
            if task in self.completed_tasks:
                analytics += f"\n{task}:\n"
                analytics += f"  Study Time: {data['study_time']} min\n"
                analytics += f"  Break Time: {data['break_time']} min\n"
                analytics += f"  Long Break Time: {data['long_break_time']} min\n"
                analytics += f"  Total Attempts: {data['attempts']}\n"
                analytics += f"  Completed: {data['completed']} times\n"
                analytics += f"  Last Completed: {data.get('last_completed', 'N/A')}\n"
                if "time_adjustments" in data:
                    analytics += f"  Time Adjustments: {data['time_adjustments']} seconds\n"
                else:
                    analytics += "  No Time Adjustments Recorded\n"
        messagebox.showinfo("Analytics", analytics)


# Run the app
root = tk.Tk()
app = PomodoroApp(root)
root.mainloop()
