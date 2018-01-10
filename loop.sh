#!/bin/bash

set echo

while read p; do
  if [ "$p" = "EOF" ]; then
     exit
  fi

  echo $p

  echo $p > doi_list.txt

  python articles.py

  mv result6.jl `tr '/' '-' <<< "$p"`.json

done <master_list.txt

#Clean up
rm -f doi_list.txt
rm -f result6.jl
