CREATE TABLE USERS (
  ID INTEGER PRIMARY KEY AUTOINCREMENT,
  IP             TEXT    NOT NULL,
  NB_CONNECTIONS INT     DEFAULT 0
);

