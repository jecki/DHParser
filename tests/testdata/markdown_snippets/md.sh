#/usr/bin/bash

fullname=$(basename "$1")
extension="${fullname##*.}"
filename="${fullname%.*}"

if [ $extension = "md" ] || [ $extension = "markdown" ]; then

    markdown $1 >tmp.html
    cat head.tmpl tmp.html tail.tmpl >$filename".html"
    rm tmp.html

    markdown_py $1 >tmp.html
    cat head.tmpl tmp.html tail.tmpl >$filename"_py.html"
    rm tmp.html

else
    echo "Wrong extension '"$extension"'! Should be 'md' or 'markdown'."
    exit 1
fi
