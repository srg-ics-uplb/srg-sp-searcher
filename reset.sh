echo "!!!WARNING!!!"
echo "This will erase the database and the uploaded PDFs!"
echo "Press CTRL+c to cancel or ENTER to continue."
read

DBPATH=./app/sql
PDFPATH=./app/pdf
PDFDB=$DBPATH/pdf.db
USERSDB=$DBPATH/users.db

echo -n "Creating database..."

[[ -f $PDFDB ]] && rm $PDFDB
[[ -f $USERSDB ]] && rm $USERSDB
sqlite3 $PDFDB < $DBPATH/pdf.sql
sqlite3 $USERSDB < $DBPATH/users.sql
echo "done."

echo -n "Deleting PDFs..."
[[ ! -z "$(ls -A $PDFPATH)" ]] && rm $PDFPATH/*
echo "done."


