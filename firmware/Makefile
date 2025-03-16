BOARD=arduino:avr:uno
PORT=/dev/ttyUSB0

compile:
	arduino-cli compile --fqbn $(BOARD) tesla-seat-controller.ino

upload: compile
	arduino-cli upload -p $(PORT) --fqbn $(BOARD)
