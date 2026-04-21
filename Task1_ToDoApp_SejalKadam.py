class Task:
    def __init__(self, description):
        self.description = description
        self.completed = False

    def __str__(self):
        status = "✔" if self.completed else "✘"
        return f"[{status}] {self.description}"

class ToDoList:
    def __init__(self):
        self.tasks = []

    def add_task(self, description):
        new_task = Task(description)
        self.tasks.append(new_task)
        print("Task added successfully!")

    def show_tasks(self):
        if not self.tasks:
            print("\nYour list is empty.")
        else:
            print("\n--- Your To-Do List ---")
            for index, task in enumerate(self.tasks, start=1):
                print(f"{index}. {task}")

    def mark_done(self, task_number):
        try:
            self.tasks[task_number - 1].completed = True
            print("Task marked as completed!")
        except IndexError:
            print("Invalid task number.")

# Simple User Interface Loop
my_list = ToDoList()
while True:
    print("\n1. Add Task | 2. View Tasks | 3. Complete Task | 4. Exit")
    choice = input("Select an option: ")

    if choice == '1':
        desc = input("Enter task description: ")
        my_list.add_task(desc)
    elif choice == '2':
        my_list.show_tasks()
    elif choice == '3':
        num = int(input("Enter task number to complete: "))
        my_list.mark_done(num)
    elif choice == '4':
        break