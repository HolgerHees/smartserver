#!/bin/bash
#Change directory to where the script resides.
BASEDIR=$(dirname $0)
cd $BASEDIR
#######################

#getting the image URL
#img="$(curl https://www.nationalgeographic.com/photography/photo-of-the-day/ -s | grep -oP '(?<="twitter:image:src" content=")\K[^"]*')"

xml="$(curl 'https://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=de-DE' -s)"

date="$(echo $xml | grep -oP '<enddate>(.*)</enddate>' | cut -d '>' -f 2 | cut -d '<' -f 1)"
url="$(echo $xml | grep -oP '<urlBase>(.*)</urlBase>' | cut -d '>' -f 2 | cut -d '<' -f 1)"
headline="$(echo $xml | grep -oP '<headline>(.*)</headline>' | cut -d '>' -f 2 | cut -d '<' -f 1)"
copyright="$(echo $xml | grep -oP '<copyright>(.*)</copyright>' | cut -d '>' -f 2 | cut -d '<' -f 1)"
copyrightUrl="$(echo $xml | grep -oP '<copyrightlink>(.*)</copyrightlink>' | cut -d '>' -f 2 | cut -d '<' -f 1)"
url="https://www.bing.de"$url"_1920x1080.jpg"

#echo $url;
#echo $headline;
#echo $copyright;
#echo $copyrightUrl;
#exit;

filename=$(basename -- "$url")
filename="${filename%.*}"
name="${filename%%_*}"

targetName="{{htdocs_path}}img/potd/"$date"_"$name".jpg"

#url="$(curl 'https://www.bing.com/HPImageArchive.aspx?format=xml&idx=0&n=1&mkt=de-DE' -s | grep -oP '<urlBase>(.*)</urlBase>' | cut -d '>' -f 2 | cut -d '<' -f 1)"
#img="https://www.bing.de"$url"_1920x1200.jpg"

#check to see if there is any wallpaper to download
if [ ! -f "$targetName" ]
then
    curl -s -L -o $targetName $url
    
    if [ -s "$targetName" ]
    then
        convert "$targetName" -set comment "$headline" "$targetName"
        convert "$targetName" -resize 1920x "{{htdocs_path}}img/potd/todayLandscape.jpg"
        convert "$targetName" -resize x1920 "{{htdocs_path}}img/potd/todayPortrait.jpg"
        
        echo "$headline" > "{{htdocs_path}}img/potd/todayTitle.txt"

        convert "{{htdocs_path}}img/potd/todayLandscape.jpg" -gravity Center -crop 1920x1080+0+0 -quality 80% "{{htdocs_path}}img/potd/todayLandscape.jpg"
        convert "{{htdocs_path}}img/potd/todayPortrait.jpg" -gravity Center -crop 1080x1920+0+0 -quality 80% "{{htdocs_path}}img/potd/todayPortrait.jpg"
    else
        echo "Downloaded file is empty"
    fi 
#else
	#echo "File already exists"
fi 
