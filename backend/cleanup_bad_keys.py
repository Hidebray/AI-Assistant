import sqlite3
prod_db = r'C:\Users\daihi\AppData\Roaming\com.aaa.app\database\app_data.db'
conn = sqlite3.connect(prod_db)
cursor = conn.cursor()

# Clear the doubly-encrypted gemini_key (cannot be recovered without .env key in prod binary)
cursor.execute("UPDATE user_settings SET setting_value = '' WHERE setting_key = 'llm.gemini_key'")
cursor.execute("UPDATE user_settings SET setting_value = 'http://localhost:11434' WHERE setting_key = 'llm.ollama_url'")
conn.commit()

# Verify final state
cursor.execute('SELECT setting_key, setting_value FROM user_settings ORDER BY setting_key')
rows = cursor.fetchall()
conn.close()

print('Final state of AppData DB settings:')
for k, v in rows:
    print(f'  {k}: {repr(v[:60])}')
