import csv
from abc import ABC, abstractmethod

# Define constants for file names
USER_FILE = "users.csv"
GROUP_FILE = "groups.csv"
EXPENSE_FILE = "expenses.csv"


# Abstract Base Class for common file handling operations
class FileHandler(ABC):
    # Base class to handle file operations

    def __init__(self, file_name, headers):
        # File name and headers are hidden inside the class
        self.file_name = file_name
        self.headers = headers
        self.initialize_file()

    def initialize_file(self):
        # Create the file with headers if it doesn't exist
        with open(self.file_name, "a+", newline="") as file:
            file.seek(0)
            if file.read().strip() == "":
                writer = csv.writer(file)
                writer.writerow(self.headers)

    def read_file(self):
        # Read the file and return the rows
        with open(self.file_name, "r") as file:
            return list(csv.DictReader(file))

    def write_file(self, rows):
        with open(self.file_name, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writeheader()
            # Filter rows to include only keys in headers
            filtered_rows = [{key: row.get(key, "") for key in self.headers} for row in rows]
            writer.writerows(filtered_rows)


# UserManager handles all user-related operations
class UserManager(FileHandler):
    # Handles user-related operations

    def __init__(self):
        # Reuse file handling logic from FileHandler
        super().__init__(USER_FILE, ["email", "name", "groups"])

    def register_user(self):
        # Registers a new user by taking their name and email
        name = input("Enter your name: ")
        email = input("Enter your email: ")

        # Check if the user already exists
        users = self.read_file()
        if any(user["email"] == email for user in users):
            print("User already exists!")
            return

        # Add new user to the file
        users.append({"email": email, "name": name, "groups": ""})
        self.write_file(users)
        print(f"User {name} registered successfully!")

    def update_user_groups(self, members, group_name):
        # Updates the group memberships of users
        users = self.read_file()
        for user in users:
            if user["email"] in members:
                # Update the groups field of the user
                user["groups"] = (
                    f"{user['groups']},{group_name}"
                    if user["groups"]
                    else group_name
                )
        self.write_file(users)


# GroupManager handles group creation and management
class GroupManager(FileHandler):
    # Handles group-related operations

    def __init__(self, user_manager):
        # UserManager is passed to manage user-group relationships
        super().__init__(GROUP_FILE, ["group_name", "members"])
        self.user_manager = user_manager

    def create_group(self):
        # Creates a new group with members
        group_name = input("Enter group name: ")
        members = input("Enter group members' emails (comma-separated): ").split(",")
        members = [email.strip() for email in members]

        # Check if the group already exists
        groups = self.read_file()
        if any(group["group_name"] == group_name for group in groups):
            print("Group already exists!")
            return

        # Add new group and update users' group memberships
        groups.append({"group_name": group_name, "members": ",".join(members)})
        self.write_file(groups)
        self.user_manager.update_user_groups(members, group_name)
        print(f"Group {group_name} created successfully!")


# ExpenseManager handles expense-related operations
class ExpenseManager(FileHandler):
    # Handles expense-related operations

    def __init__(self, group_manager):
        # GroupManager is passed to manage group-expense relationships
        super().__init__(EXPENSE_FILE, ["group_name", "expense_name", "amount", "payer", "split"])
        self.group_manager = group_manager

    def add_expense(self):
        # Adds a new expense for a group
        group_name = input("Enter group name: ")
        expense_name = input("Enter expense name: ")
        amount = float(input("Enter amount: "))
        payer = input("Who paid? Enter email: ")

        # Validate group existence and payer membership
        groups = self.group_manager.read_file()
        group = next((g for g in groups if g["group_name"] == group_name), None)
        if not group:
            print("Group not found!")
            return

        members = group["members"].split(",")
        if payer not in members:
            print("Payer not in group!")
            return

        # Calculate the expense split
        split = self.calculate_split(amount, members)
        if not split:
            return

        # Record the expense
        expenses = self.read_file()
        expenses.append({
            "group_name": group_name,
            "expense_name": expense_name,
            "amount": amount,
            "payer": payer,
            "split": str(split),
        })
        self.write_file(expenses)
        print(f"Expense '{expense_name}' added successfully!")

    # Calculates the split of the expense
    def calculate_split(self, amount, members):
        split_method = input("Split equally? (yes/no): ").lower()
        if split_method == "yes":
            # Equal split among members
            return {member: amount / len(members) for member in members}
        else:
            # Custom split for each member
            split = {}
            for member in members:
                try:
                    split[member] = float(input(f"Enter amount for {member}: "))
                except ValueError:
                    print("Invalid input. Aborting.")
                    return None
            return split


# BalanceViewer handles viewing of balances (Polymorphism)
class BalanceViewer:
    # Handles viewing balances

    def __init__(self, expense_manager):
        self.expense_manager = expense_manager

    def view_group_balances(self):
        # Displays the balances of a specific group
        group_name = input("Enter group name: ")

        balances = self.calculate_group_balances(group_name)
        if balances:
            print("\nBalances:")
            for member, balance in balances.items():
                if member != "details":
                    print(f"{member}: {'Owes' if balance > 0 else 'to Receive'} {abs(balance):.2f}")
            print("\nWho owes whom:")
            for payer, amounts in balances["details"].items():
                for payee, amount in amounts.items():
                    print(f"{payer} owes {payee}: {amount:.2f}")
        else:
            print("No balances to display!")

    def calculate_group_balances(self, group_name):
        # Calculates balances for a specific group
        balances = {}
        details = {}
        expenses = self.expense_manager.read_file()
        for row in expenses:
            if row["group_name"] == group_name:
                split = eval(row["split"])
                payer = row["payer"]

                for member, amount in split.items():
                    balances[member] = balances.get(member, 0) + amount
                    balances[payer] = balances.get(payer, 0) - amount

                    if member != payer:
                        if member not in details:
                            details[member] = {}
                        details[member][payer] = details[member].get(payer, 0) + amount

        balances["details"] = details
        return balances


# Main Application Class
class Application:
    # Main application class to arrange operations

    def __init__(self):
        # Pass dependencies between components
        self.user_manager = UserManager()
        self.group_manager = GroupManager(self.user_manager)
        self.expense_manager = ExpenseManager(self.group_manager)
        self.balance_viewer = BalanceViewer(self.expense_manager)

    def run(self):
        # Runs the main application through loop
        while True:
            print("\nOptions:")
            print("1. Register User")
            print("2. Create Group")
            print("3. Add Expense")
            print("4. View Group Balances")
            print("5. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                self.user_manager.register_user()
            elif choice == "2":
                self.group_manager.create_group()
            elif choice == "3":
                self.expense_manager.add_expense()
            elif choice == "4":
                self.balance_viewer.view_group_balances()
            elif choice == "5":
                print("Exiting!")
                break
            else:
                print("Invalid choice!")


# Run the application
if __name__ == "__main__":
    app = Application()
    app.run()
