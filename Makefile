.phony: run clean togif

run:
	echo "running script"
	python3 snowflake.py

clean:
	echo "cleaning svg"
	rm *.svg
	echo "cleaning gifs"
	rm *.gif

togif:
	echo "using imagemagick convert"
	convert -delay 100 -loop 0 *.svg snowflake.gif
