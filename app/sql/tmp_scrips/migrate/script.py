import sqlite3

DB_TABLES = {
  "pdfs"      : "PDF",
  "freq"      : "FREQ",
  "status"    : " ",
  "logs"      : "LOGS"
}

def arr_to_str_w_quot(inputArr):
  outputStr = ""
  for elem in inputArr:
    outputStr = outputStr + "'" + str(elem).replace("'", '&apos;') + "', "
  return outputStr[:-2]

def arr_to_str(inputArr):
  outputStr = ""
  for elem in inputArr:
    outputStr = outputStr + str(elem) + ", "
  return outputStr[:-2]

def clear_db(db, old_tables):
  conn = sqlite3.connect(db)
  cursor = conn.cursor()

  cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
  filteredCursor = filter(lambda table : table[0] != 'sqlite_sequence', cursor.fetchall())

  tables = map(lambda a : a[0], filteredCursor)
  for table in tables:
    if table in old_tables:
      conn.execute(f'DELETE FROM {table}')
      conn.commit()

  conn.close()

def read_db(db):
  conn = sqlite3.connect(db)
  cursor = conn.cursor()
  cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
  filteredCursor = filter(lambda table : table[0] != 'sqlite_sequence', cursor.fetchall())
  
  tables = map(lambda a : a[0], filteredCursor)
  db_data = {}
  for table in tables:
    db_data[table] = {}
    cursor.execute(f'SELECT * FROM {table}')
    columns = list(map(lambda a : a[0], cursor.description))
    db_data[table]['columns'] = columns
    db_data[table]['rows'] = []

    for row in cursor.fetchall():
      data = {}
      for i in range(0, len(columns)):
        data[columns[i]] = row[i]
      db_data[table]['rows'].append(data)
  
  conn.close()
  return db_data

def run():
  old_db = read_db('./old/pdf.db')
  clear_db('./new/pdf.db', list(old_db.keys()))
  new_db = read_db('./new/pdf.db')

  # put data from old db old_db into dictionary new_db
  for table in old_db.keys():
    if table in new_db.keys():
      for row in old_db[table]['rows']:
        new_pdf = { "metadata":  {}}
        for column in old_db[table]['columns']:
          if column in new_db[table]['columns']:
            new_pdf[column] = row[column]
          else:
            new_pdf['metadata'][column] = row[column]
        new_pdf['STATUS'] = 2
        new_db[table]['rows'].append(new_pdf)

  conn = sqlite3.connect('./new/pdf.db')

  # insert pdfs and word frequency in dictionary new_db into database
  for table in new_db:
    if table in old_db.keys():
      for row in new_db[table]['rows']:
        row_columns = []
        row_values = []

        for column in new_db[table]['columns']:
          if column in row.keys() and row[column] is not None:
            row_columns.append(column)
            row_values.append(row[column])

        sql = f"INSERT INTO {table} ({arr_to_str(row_columns)}) VALUES ({arr_to_str_w_quot(row_values)})"
        conn.execute(sql)
        conn.commit()

  conn.close()

run()