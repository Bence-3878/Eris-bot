import mysql.connector                          # MySQL kliens importálása

leveldb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="alma",
    database="discord_bot",
    port=3306,
    auth_plugin='mysql_native_password'
)

leveldb2 = mysql.connector.connect(
    host="localhost",
    user="root",
    password="alma",
    database="discord_bot2",
    port=3306,
    auth_plugin='mysql_native_password'
)

cursor = leveldb.cursor()
cursor2 = leveldb2.cursor()

cursor.execute("SELECT * FROM servers")
result = cursor.fetchall()

for row in result:
    cursor2.execute("INSERT INTO servers (id, welcome_ch, level_up_ch) "
                    "VALUES (%s, %s, %s)", (row[0],row[1],row[2]))
    leveldb2.commit()

cursor.execute("SELECT * FROM server_users")
result = cursor.fetchall()

for row in result:
    cursor2.execute("INSERT INTO server_users (user_id, server_id, user_xp_text, level_text) "
                    "VALUES (%s, %s, %s, %s)", (row[0],row[1],row[2],row[3]))
    leveldb2.commit()

