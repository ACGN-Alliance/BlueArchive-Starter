# use nuitka to package the project to executable file
nuitka3 --mingw64 --windows-disable-console --standalone \
--show-progress --show-memory --plugin-enable=qt-plugins --plugin-enable=pylint-warnings --recurse-all \
--recurse-not-to= --output-dir=out \
main.py