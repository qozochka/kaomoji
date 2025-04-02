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

    def get_all_kaomoji(self, sort_by_date=True, search_tags=None):
        try:
            sql = """
                SELECT DISTINCT k.expression  -- Используем DISTINCT для устранения дубликатов
                FROM kaomoji k
                LEFT JOIN tags t ON k.id = t.kaomoji_id
            """
            params = []

            if search_tags:
                sql += " WHERE t.tag_name IN (" + ",".join(["?"] * len(search_tags)) + ")"
                params.extend(search_tags)

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
