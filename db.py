import sqlite3

def init_db():
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS facts (date TEXT PRIMARY KEY,content TEXT NOT NULL)''')
    conn.commit
    conn.close
     


def get_fact(date):
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM facts WHERE date = ?", (date,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0].splitlines()
    else:
        return None
    
def save_fact(date, facts):
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO facts (date, content) VALUES (?, ?)", (date, facts))
    conn.commit()
    conn.close()