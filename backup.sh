#!/bin/bash
#by jachermocilla@gmail.com

DBPATH=./app/sql
PDFPATH=./app/static/pdf
PDFDB=$DBPATH/pdf.db
USERSDB=$DBPATH/users.db


echo "Creating a backup..."
BACKUP="tr-searcher-backup-$(date '+%F_%H-%M-%S').tar.gz"

