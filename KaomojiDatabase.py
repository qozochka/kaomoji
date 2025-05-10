import sqlite3
import sys


class KaomojiDatabase:
    def __init__(self, db_name="kaomoji.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.upgrade_table()
        self.create_table()
        self.create_tags_table()
        self.create_favorites_table() #NEW

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print("Connected to the database successfully!")
        except sqlite3.Error as e:
            print(f"Error connecting to the database: {e}")
            sys.exit(1)

    def create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kaomoji (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            print("Table 'kaomoji' created or already exists.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def upgrade_table(self):
        try:
            self.cursor.execute("ALTER TABLE kaomoji ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            self.conn.commit()
            print("Successfully added 'created_at' column to table.")

            self.cursor.execute("UPDATE kaomoji SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            self.conn.commit()
            print("Successfully updated 'created_at' for existing rows.")

        except sqlite3.OperationalError as e:
            if "duplicate column name: created_at" in str(e):
                print("Column 'created_at' already exists. Skipping.")
            else:
                print(f"Error upgrading table: {e}")
        except sqlite3.Error as e:
            print(f"Error upgrading table: {e}")

    def create_tags_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kaomoji_id INTEGER NOT NULL,
                    tag_name TEXT NOT NULL,
                    FOREIGN KEY (kaomoji_id) REFERENCES kaomoji(id),
                    UNIQUE (kaomoji_id, tag_name)  -- Prevent duplicate tags for a kaomoji
                )
            """)
            self.conn.commit()
            print("Table 'tags' created or already exists.")
        except sqlite3.Error as e:
            print(f"Error creating tags table: {e}")

    def create_favorites_table(self): #NEW
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    kaomoji_id INTEGER PRIMARY KEY,
                    FOREIGN KEY (kaomoji_id) REFERENCES kaomoji(id)
                )
            """)
            self.conn.commit()
            print("Table 'favorites' created or already exists.")
        except sqlite3.Error as e:
            print(f"Error creating favorites table: {e}")

    def add_kaomoji(self, kaomoji, tags=None):
        try:
            self.cursor.execute("INSERT INTO kaomoji (expression) VALUES (?)", (kaomoji,))
            self.conn.commit()
            kaomoji_id = self.cursor.lastrowid
            print(f"Added kaomoji: {kaomoji} with ID: {kaomoji_id}")

            if tags:
                self.add_tags(kaomoji_id, tags)

            return True
        except sqlite3.IntegrityError:
            print(f"Kaomoji '{kaomoji}' already exists in the database.")
            return False
        except sqlite3.Error as e:
            print(f"Error adding kaomoji: {e}")
            return False

    def add_tags(self, kaomoji_id, tag_names):
        try:
            for tag_name in tag_names:

                self.cursor.execute("SELECT id FROM tags WHERE kaomoji_id = ? AND tag_name = ?", (kaomoji_id, tag_name))
                existing_tag = self.cursor.fetchone()

                if not existing_tag:
                    self.cursor.execute("INSERT INTO tags (kaomoji_id, tag_name) VALUES (?, ?)", (kaomoji_id, tag_name))
                    self.conn.commit()
                    print(f"Added tag '{tag_name}' for kaomoji ID {kaomoji_id}")
                else:
                    print(f"Tag '{tag_name}' already exists for kaomoji ID {kaomoji_id}. Skipping.")

            return True

        except sqlite3.Error as e:
            print(f"Error adding tags: {e}")
            return False

    def add_tag(self, kaomoji_id, tag_name):
        return self.add_tags(kaomoji_id, [tag_name])

    def remove_kaomoji(self, kaomoji):
        try:
            self.cursor.execute("DELETE FROM tags WHERE kaomoji_id = (SELECT id FROM kaomoji WHERE expression = ?)",
                                (kaomoji,))
            self.conn.commit()

            self.cursor.execute("DELETE FROM kaomoji WHERE expression = ?", (kaomoji,))
            if self.cursor.rowcount > 0:
                self.conn.commit()
                print(f"Removed kaomoji: {kaomoji}")
                return True
            else:
                print(f"Kaomoji '{kaomoji}' not found in the database.")
                return False
        except sqlite3.Error as e:
            print(f"Error removing kaomoji: {e}")
            return False

    def get_all_kaomoji(self, sort_by_date=True, search_tags=None, show_favorites=False):
        try:
            sql = """
                SELECT DISTINCT k.expression
                FROM kaomoji k
                LEFT JOIN tags t ON k.id = t.kaomoji_id
                LEFT JOIN favorites f ON k.id = f.kaomoji_id
            """
            params = []
            where_clauses = []

            if search_tags:
                tag_placeholders = ",".join(["?"] * len(search_tags))
                sql += f" WHERE t.tag_name IN ({tag_placeholders})"
                params.extend(search_tags)

            if show_favorites:
                if search_tags:
                    sql += " AND f.kaomoji_id IS NOT NULL"
                else:
                    sql += " WHERE f.kaomoji_id IS NOT NULL"

            sql += " GROUP BY k.expression"

            if sort_by_date:
                sql += " ORDER BY k.created_at DESC"

            self.cursor.execute(sql, params)
            kaomoji_list = [row[0] for row in self.cursor.fetchall()]
            return kaomoji_list
        except sqlite3.Error as e:
            print(f"Error getting all kaomoji: {e}")
            return []

    def get_tags_for_kaomoji(self, kaomoji):
        try:
            self.cursor.execute("""
                SELECT t.tag_name
                FROM tags t
                JOIN kaomoji k ON t.kaomoji_id = k.id
                WHERE k.expression = ?
            """, (kaomoji,))
            tags = [row[0] for row in self.cursor.fetchall()]
            return tags
        except sqlite3.Error as e:
            print(f"Error getting tags for kaomoji: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def edit_tags(self, kaomoji, new_tags):
        try:
            # Get kaomoji ID
            self.cursor.execute("SELECT id FROM kaomoji WHERE expression = ?", (kaomoji,))
            result = self.cursor.fetchone()
            if not result:
                print(f"Kaomoji '{kaomoji}' not found.")
                return False
            kaomoji_id = result[0]

            # Delete existing tags
            self.cursor.execute("DELETE FROM tags WHERE kaomoji_id = ?", (kaomoji_id,))
            self.conn.commit()

            # Add new tags
            if new_tags:
                self.add_tags(kaomoji_id, new_tags)

            print(f"Edited tags for kaomoji '{kaomoji}' to: {new_tags}")
            return True

        except sqlite3.Error as e:
            print(f"Error editing tags: {e}")
            return False

    def is_favorite(self, kaomoji_id): #NEW
        try:
            self.cursor.execute("SELECT kaomoji_id FROM favorites WHERE kaomoji_id = ?", (kaomoji_id,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Error checking if kaomoji is favorite: {e}")
            return False

    def add_to_favorites(self, kaomoji_id): #NEW
        try:
            self.cursor.execute("INSERT INTO favorites (kaomoji_id) VALUES (?)", (kaomoji_id,))
            self.conn.commit()
            print(f"Added kaomoji with ID {kaomoji_id} to favorites.")
            return True
        except sqlite3.IntegrityError:
            print(f"Kaomoji with ID {kaomoji_id} is already in favorites.")
            return False
        except sqlite3.Error as e:
            print(f"Error adding kaomoji to favorites: {e}")
            return False

    def remove_from_favorites(self, kaomoji_id): #NEW
        try:
            self.cursor.execute("DELETE FROM favorites WHERE kaomoji_id = ?", (kaomoji_id,))
            self.conn.commit()
            print(f"Removed kaomoji with ID {kaomoji_id} from favorites.")
            return True
        except sqlite3.Error as e:
            print(f"Error removing kaomoji from favorites: {e}")
            return False
