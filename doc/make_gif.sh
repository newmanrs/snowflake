
echo $SHELL
echo ${pwd}
echo $1
# -Delay centiseconds (100 = 1s)
# -loop 0 infinite loops
# use all pngs generated in above directory.
# requires imagemagick installation if convert not found
convert -delay 100 -loop 0 *.svg snowflake.gif

