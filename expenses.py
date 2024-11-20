import csv

USER_FILE = "users.csv"
GROUP_FILE = "groups.csv"
EXPENSE_FILE = "expenses.csv"


def initialize_files():
    files_headers = {
        USER_FILE: ["email", "name", "groups"],
        GROUP_FILE: ["group_name", "members"],
        EXPENSE_FILE: ["group_name", "expense_name", "amount", "payer", "split"],
    }

    for file, headers in files_headers.items():
        with open(file, "a+", newline="") as f:
            f.seek(0)
            if f.read().strip() == "":
                writer = csv.writer(f)
                writer.writerow(headers)


def register_user():
    name = input("Enter your name: ")
    email = input("Enter your email: ")

    with open(USER_FILE, "r") as file:
        reader = csv.DictReader(file)
        if any(row["email"] == email for row in reader):
            print("User already exists!")
            return

    with open(USER_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([email, name, "", ""])
    print(f"User {name} registered successfully!")


def create_group():
    group_name = input("Enter group name: ")
    members = input("Enter group members' emails (comma-separated): ").split(",")
    members = [email.strip() for email in members]

    with open(GROUP_FILE, "r") as file:
        reader = csv.DictReader(file)
        if any(row["group_name"] == group_name for row in reader):
            print("Group already exists!")
            return

    with open(GROUP_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([group_name, ",".join(members)])

    update_user_groups(members, group_name)
    print(f"Group {group_name} created successfully!")


def update_user_groups(members, group_name):
    with open(USER_FILE, "r") as file:
        users = list(csv.DictReader(file))

    with open(USER_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["email", "name", "groups"])
        writer.writeheader()
        for user in users:
            if user["email"] in members:
                groups = user["groups"] + "," + group_name if user["groups"] else group_name
                user["groups"] = groups
            writer.writerow(user)


def add_expense():
    group_name = input("Enter group name: ")
    expense_name = input("Enter expense name: ")
    amount = float(input("Enter amount: "))
    payer = input("Who paid? Enter email: ")

    with open(GROUP_FILE, "r") as file:
        reader = csv.DictReader(file)
        group = next((row for row in reader if row["group_name"] == group_name), None)
    if not group:
        print("Group not found!")
        return

    members = group["members"].split(",")
    if payer not in members:
        print("Payer not in group!")
        return

    split = calculate_split(amount, members)
    if not split:
        return

    with open(EXPENSE_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([group_name, expense_name, amount, payer, str(split)])
    print(f"Expense '{expense_name}' added successfully!")


def calculate_split(amount, members):
    split_method = input("Split equally? (yes/no): ").lower()
    if split_method == "yes":
        return {member: amount / len(members) for member in members}
    else:
        split = {}
        for member in members:
            try:
                split[member] = float(input(f"Enter amount for {member}: "))
            except ValueError:
                print("Invalid input. Aborting.")
                return None
        return split


def view_balances():
    group_name = input("Enter group name: ")

    balances = calculate_group_balances(group_name)
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


def calculate_group_balances(group_name):
    balances = {}
    details = {}
    with open(EXPENSE_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["group_name"] == group_name:
                split = eval(row["split"])
                payer = row["payer"]
                amount_paid = float(row["amount"])

                for member, amount in split.items():
                    balances[member] = balances.get(member, 0) + amount
                    balances[payer] = balances.get(payer, 0) - amount

                    if member != payer:
                        if member not in details:
                            details[member] = {}
                        details[member][payer] = details[member].get(payer, 0) + amount

    balances["details"] = details
    return balances



def view_personal_balance():
    user_name = input("Enter your name to view your personal balance details: ")

    with open(USER_FILE, "r") as file:
        reader = csv.DictReader(file)
        user = next((row for row in reader if row["name"] == user_name), None)
    if not user:
        print(f"User '{user_name}' not found!")
        return

    user_email = user["email"]
    owes_to_others, owed_by_others = 0, 0

    with open(EXPENSE_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            split = eval(row["split"])
            payer = row["payer"]

            if user_email in split and user_email != payer:
                owes_to_others += split[user_email]

            if payer == user_email:
                owed_by_others += sum(
                    amount for member, amount in split.items() if member != user_email
                )

    net_balance = owed_by_others - owes_to_others

    print(f"\nPersonal Balance Details for {user_name} ({user_email}):")
    print(f"Expenses you owe to others: {owes_to_others:.2f}")
    print(f"Expenses others owe to you: {owed_by_others:.2f}")
    print(f"Your net balance: {'Owe' if net_balance < 0 else 'to Receive'} {abs(net_balance):.2f}")



def settle_balance():
    payer = input("Enter your email: ")
    payee = input("Enter the email of the person you settled with: ")
    amount = float(input("Enter the amount settled: "))

    with open(EXPENSE_FILE, "r") as file:
        expenses = list(csv.DictReader(file))

    with open(EXPENSE_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["group_name", "expense_name", "amount", "payer", "split"])
        writer.writeheader()
        for row in expenses:
            split = eval(row["split"])
            if payer in split and payee in split:
                split[payee] -= amount
                split[payer] += amount
            row["split"] = str(split)
            writer.writerow(row)
    print(f"Balance of {amount:.2f} settled between {payer} and {payee}!")


def main():
    initialize_files()
    while True:
        print("\nOptions:")
        print("1. Register User")
        print("2. Create Group")
        print("3. Add Expense")
        print("4. View Group Balances")
        print("5. View Personal Balance")
        print("6. Settle Balance")
        print("7. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            register_user()
        elif choice == "2":
            create_group()
        elif choice == "3":
            add_expense()
        elif choice == "4":
            view_balances()
        elif choice == "5":
            view_personal_balance()
        elif choice == "6":
            settle_balance()
        elif choice == "7":
            print("Exiting!")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
