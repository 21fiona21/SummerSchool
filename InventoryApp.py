# Application for managing the SHSG inventory

import sqlite3
from datetime import datetime

# Superklasse für alle Inventargegenstände
class Inventory:
    VALID_DEPARTMENTS = ["ClubA", "ClubB", "ClubC", "General"]

    def __init__(self, name, department, quantity):
        self.name = name
        self.department = self.validate_department(department)
        self.quantity = quantity

    def validate_department(self, department):
        if department not in self.VALID_DEPARTMENTS:
            return None
        return department

    def create_item(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM inventory
            WHERE name = ? AND department = ?
        ''', (self.name, self.department))
        existing_item = cursor.fetchone()

        if existing_item:
            adjusted_quantity = existing_item[3] + self.quantity
            cursor.execute('''
                UPDATE inventory
                SET quantity = ?
                WHERE name = ? AND department = ?
            ''', (adjusted_quantity, self.name, self.department))
            conn.commit()
            print(f"Item '{self.name}' already exists in '{self.department}' department. Quantity updated.")
        else:
            cursor.execute('''
                INSERT INTO inventory (name, department, quantity)
                VALUES (?, ?, ?)
            ''', (self.name, self.department, self.quantity))
            conn.commit()
            print(f"Item '{self.name}' added to inventory.")

    def update_quantity(self, conn, quantity):
        # Retrieve the current quantity from the database
        cursor = conn.cursor()
        cursor.execute('''
            SELECT quantity FROM inventory
            WHERE name = ? AND department = ?
        ''', (self.name, self.department))
        result = cursor.fetchone()

        if result is None:
            print(f"Item '{self.name}' does not exist in department '{self.department}'. Cannot update quantity.")
            return

        current_quantity = result[0] 
        new_quantity = max(0, current_quantity + quantity)  # Adjust quantity, but not below 0
        cursor.execute('''
            UPDATE inventory
            SET quantity = ?
            WHERE name = ? AND department = ?
        ''', (new_quantity, self.name, self.department))  # corrected this line
        conn.commit()


    def remove_item(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM inventory
            WHERE name = ? AND department = ?
        ''', (self.name, self.department))
        conn.commit()

# Subklasse für verderbliche Gegenstände
class InventoryPerishable(Inventory):
    def __init__(self, name, department, quantity, expiry_date):
        super().__init__(name, department, quantity)
        self.expiry_date = expiry_date

    def create_item(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM inventory
            WHERE name = ? AND department = ? AND expiry_date = ?
        ''', (self.name, self.department, self.expiry_date))
        existing_item = cursor.fetchone()

        if existing_item:
            adjusted_quantity = existing_item[3] + self.quantity
            cursor.execute('''
                UPDATE inventory
                SET quantity = ?
                WHERE name = ? AND department = ? AND expiry_date = ?
            ''', (adjusted_quantity, self.name, self.department, self.expiry_date))
            conn.commit()
            print(f"Item '{self.name}' with expiry date '{self.expiry_date}' already exists in '{self.department}' department. Quantity updated.")
        else:
            cursor.execute('''
                INSERT INTO inventory (name, department, quantity, expiry_date)
                VALUES (?, ?, ?, ?)
            ''', (self.name, self.department, self.quantity, self.expiry_date))
            conn.commit()
            print(f"Item '{self.name}' added to inventory.")

# Datenbankmanager für die Interaktion mit SQLite
class InventoryDB:
    def __init__(self, db_name="inventory.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                expiry_date TEXT
            )
        ''')
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_all_items(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        return cursor.fetchall()

    def filter_by_date(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inventory WHERE expiry_date IS NOT NULL ORDER BY expiry_date')
        return cursor.fetchall()

    def filter_alphabetically(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inventory ORDER BY name')
        return cursor.fetchall()

    def filter_by_department(self, department):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inventory WHERE department = ?', (department,))
        return cursor.fetchall()

    def search_item(self, search_type, search_value):
        cursor = self.conn.cursor()
        if search_type == "name":
            cursor.execute('SELECT * FROM inventory WHERE name LIKE ?', ('%' + search_value + '%',))
        elif search_type == "expiry_date":
            cursor.execute('SELECT * FROM inventory WHERE expiry_date = ?', (search_value,))
        elif search_type == "department":
            cursor.execute('SELECT * FROM inventory WHERE department = ?', (search_value,))
        else:
            return None
        return cursor.fetchall()



# Interaktive Steuerung
class StorageInteractive:
    def __init__(self, db):
        self.db = db

    def get_valid_department(self):
        while True:
            department = input(f"Enter the department ({', '.join(Inventory.VALID_DEPARTMENTS)}): ")
            if department not in Inventory.VALID_DEPARTMENTS:
                print(f"Invalid department! Please enter one of the following: {', '.join(Inventory.VALID_DEPARTMENTS)}")
            else:
                return department

    def interact(self):
        while True:
            print("\n1. Add an item.")
            print("2. View all items.")
            print("3. View items by expiry date.")
            print("4. View items alphabetically.")
            print("5. View items by department.")
            print("6. Search for an item.")
            print("7. Delete an item.")
            print("8. Adjust item quantity.")
            print("9. Exit")

            user_choice = input("Please choose an option (1-9): ")

            if user_choice == "1":
                name = input("Enter the name of the item: ")
                
                # Ask the user until a valid department is provided
                while True:
                    department = input(f"Enter the department ({', '.join(Inventory.VALID_DEPARTMENTS)}): ")
                    if department not in Inventory.VALID_DEPARTMENTS:
                        print(f"Invalid department! Please enter one of the following: {', '.join(Inventory.VALID_DEPARTMENTS)}")
                    else:
                        break

                # Überprüfung auf negative quantity
                while True:
                    try:
                        quantity = int(input("Enter the quantity: "))
                        if quantity < 0:
                            print("You can't enter a negative quantity. Please try again.")
                        else:
                            break
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")

                is_perishable = input("Is this item perishable? (yes/no): ").lower()

                if is_perishable == "yes":
                    while True:
                        try:
                            expiry_date = input("Enter the expiry date (YYYY-MM-DD): ")
                            datetime.strptime(expiry_date, '%Y-%m-%d')
                            break
                        except ValueError:
                            print("This is the incorrect date format. It should be YYYY-MM-DD. Please try again.")
                    item = InventoryPerishable(name, department, quantity, expiry_date)
                else:
                    item = Inventory(name, department, quantity)

                item.create_item(self.db.conn)
                print(f"Item '{name}' added to the inventory.")


            elif user_choice == "2":
                items = self.db.get_all_items()
                for item in items:
                    print(item)

            elif user_choice == "3":
                items = self.db.filter_by_date()
                for item in items:
                    print(item)

            elif user_choice == "4":
                items = self.db.filter_alphabetically()
                for item in items:
                    print(item)

            elif user_choice == "5":
                department = input(f"Enter the department ({', '.join(Inventory.VALID_DEPARTMENTS)}): ")
                items = self.db.filter_by_department(department)
                for item in items:
                    print(item)

            elif user_choice == "6":
                # Schritt 1: Suche nach Namen
                search_type = 'name'
                search_value = input(f"Enter the {search_type}: ")
                items = self.db.search_item(search_type, search_value)

                if items:
                    # Alle Treffer für den Namen anzeigen
                    print("\nItems found:")
                    for item in items:
                        print(item)

                    # Schritt 2: Optional Suche nach Department in den bereits gefundenen Items
                    continue_search = input("Continue search by department? (y/n) ")
                    if continue_search.lower() == "y":
                        search_type = 'department'
                        search_value = input(f"Enter the {search_type} ({', '.join(Inventory.VALID_DEPARTMENTS)}): ")

                        if search_value in Inventory.VALID_DEPARTMENTS:
                            # Filtere nur die Treffer mit dem gesuchten Department
                            items = [item for item in items if item[2] == search_value]
                            if items:
                                print("\nItems filtered by department:")
                                for item in items:
                                    print(item)
                            else:
                                print(f"No items found in department '{search_value}' with the name '{search_value}'.")
                                continue

                    # Schritt 3: Optional Suche nach Expiry Date in den bereits gefilterten Items
                    continue_search = input("Continue search by expiry date? (y/n) ")
                    if continue_search.lower() == "y":
                        search_type = 'expiry_date'
                        search_value = input(f"Enter the {search_type} or 'none' if item does not have an expiry date: ")

                        # Fall 1: Suche nach Items ohne Ablaufdatum
                        if search_value.lower() == 'none':
                            items = [item for item in items if item[4] is None]
                            if items:
                                print("\nItems without expiry date:")
                                for item in items:
                                    print(item)
                            else:
                                print("No items found without an expiry date.")
                        # Fall 2: Suche nach Items mit einem bestimmten Ablaufdatum
                        else:
                            items = [item for item in items if item[4] == search_value]
                            if items:
                                print(f"\nItems expiring on {search_value}:")
                                for item in items:
                                    print(item)
                            else:
                                print(f"No items found with expiry date '{search_value}'.")

                else:
                    print("No items found with the specified name.")

            elif user_choice == "7":
                # ID des zu löschenden Items abfragen
                try:
                    item_id = int(input("Enter the ID of the item to delete: "))
                except ValueError:
                    print("Invalid ID. Please enter a numeric value.")
                    continue

                # Item mit dieser ID anzeigen
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
                item_data = cursor.fetchone()

                if item_data:
                    print(f"Item to delete: ID: {item_data[0]}, Name: {item_data[1]}, Department: {item_data[2]}, Quantity: {item_data[3]}, Expiry Date: {item_data[4]}")
                    confirm = input("Do you really want to delete this item? (y/n): ").lower()

                    if confirm == "y":
                        cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
                        self.db.conn.commit()
                        print(f"Item with ID {item_id} successfully deleted.")
                    else:
                        print("Deletion cancelled.")
                else:
                    print(f"No item found with ID {item_id}.")

            elif user_choice == "8":
                # ID des zu aktualisierenden Items abfragen
                try:
                    item_id = int(input("Enter the ID of the item to update the quantity: "))
                except ValueError:
                    print("Invalid ID. Please enter a numeric value.")
                    continue

                # Item mit dieser ID anzeigen
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
                item_data = cursor.fetchone()

                if item_data:
                    print(f"Item to update: ID: {item_data[0]}, Name: {item_data[1]}, Department: {item_data[2]}, Quantity: {item_data[3]}, Expiry Date: {item_data[4]}")
                    confirm = input("Do you want to update the quantity of this item? (y/n): ").lower()

                    if confirm == "y":
                        while True:
                            try:
                                quantity_adjustment = int(input("Enter the quantity to adjust (positive to add, negative to remove): "))
                                break
                            except ValueError:
                                print("Only numbers can be entered. Please try again.")

                        # Neue Überprüfung: Verhindern, dass die Menge negativ wird
                        if quantity_adjustment < 0 and abs(quantity_adjustment) > item_data[3]:
                            print("Removing more units than exist is not possible. No changes have been made.")
                        else:
                            new_quantity = max(0, item_data[3] + quantity_adjustment)
                            cursor.execute('UPDATE inventory SET quantity = ? WHERE id = ?', (new_quantity, item_id))
                            self.db.conn.commit()
                            print(f"Item with ID {item_id} quantity updated to {new_quantity}.")
                    else:
                        print("Quantity update cancelled.")
                else:
                    print(f"No item found with ID {item_id}.")



            elif user_choice == "9":
                break
            else:
                print("Invalid option. Please try again.")

        print("Thank you for using the Inventory Manager!")


if __name__ == "__main__":
    db = InventoryDB()
    interactive_storage = StorageInteractive(db)
    interactive_storage.interact()
    db.close()
