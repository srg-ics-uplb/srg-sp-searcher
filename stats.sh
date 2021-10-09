#!/bin/bash
#by jachermocilla@gmail.com

ACCESS_LOG=access_for_stats.log

TOTAL_PDF_DOWNLOADS=`cat $ACCESS_LOG | grep pdf | awk -F ' ' '{print $7}' | wc -l`
echo "Total PDF Downloads: $TOTAL_PDF_DOWNLOADS"

UNIQUE_VISITORS=`cat $ACCESS_LOG | grep pdf | awk -F ' ' '{print $1}' | uniq | wc -l`
echo "Number of unique visitors: $UNIQUE_VISITORS"

echo "Number of Downloads Per Report:"
cat $ACCESS_LOG | grep pdf | awk -F ' ' '{print $7}' | sort | uniq -c | sort -nr

echo "Number of Downloads per IP Address:"
cat $ACCESS_LOG | grep pdf | awk -F ' ' '{print $1}' | sort | uniq -c | sort -nr

echo "Occurence of Search Keywords:"
cat $ACCESS_LOG | grep -e"/search?s" | awk -F ' ' '{print $7}' | grep ^/search? | awk -F '=' '{print $2}' | sort | uniq -c
