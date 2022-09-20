#!/usr/bin/env python3

import smbus
import time
import os
import datetime
import RPi.GPIO as GPIO

addr = 0x10 # Ups i2c address
bus = smbus.SMBus(1) # i2c-1
usb_5v = 17  # GPIO-input for main power status
GPIO.setmode(GPIO.BCM)
GPIO.setup(usb_5v, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Main power "check"

start_time = datetime.datetime.now()  # Develop only


def read_ups() -> list:
	try:
		vcellH = bus.read_byte_data(addr,0x03)
		vcellL = bus.read_byte_data(addr,0x04)
		socH = bus.read_byte_data(addr,0x05)
		socL = bus.read_byte_data(addr,0x06)
	except:
		return 0, 0, 0  # Last zero = Develop only ('debug')

	cell_voltage = (((vcellH&0x0F)<<8)+vcellL)*1.25 # Cell voltage mA
	cell_voltage = round(cell_voltage)
	cell_percent = ((socH<<8)+socL)*0.003906 # Electric quantity in percentage (%)
	cell_percent = round(cell_percent, 1)

	debug = str(vcellH) + "\t" + str(vcellL) + "\t" + str(socH) + "\t" + str(socL)  # Develop only
	return cell_voltage, cell_percent, debug


def check_main_power() -> bool:
	power_state = GPIO.input(usb_5v)
	return bool(power_state)


def save_power_outage(main_power_state: bool, batt_percent: str, low_pwr_halt=False) -> None:
	now = datetime.datetime.now()
	date = now.strftime("%d.%m.%Y")
	time = now.strftime("%H:%M:%S")

	with open("pwr_fault.log", "a") as f:
		if not main_power_state:  # Write power outage start time
			power_off_time = str(date) + "\t" + str(time) + "\t"
			f.write(power_off_time)
		elif main_power_state:  # Write power outage end time
			power_on_time =  str(time) + "\t" + str(batt_percent) + " %\n"
			f.write(power_on_time)


def save_ups_log(batt_volt, batt_percent, debug) -> None:
	date_now = datetime.datetime.now().strftime('%H:%M:%S')
	with open("ups.log", "a") as f:
		batt_status = str(date_now) + "\t" + str(batt_percent) + "\t" + str(batt_volt)
		f.write(batt_status + "\t" + debug + "\n")


def main():
	old_power_state = True

	while(True):
		batt_volt, batt_percent, debug = read_ups()

		print("**** DFRobot UPS test ****")
		print("cell_voltage:", batt_volt, "mV")
		print("cell_percent:", batt_percent, "%")
		run_time = datetime.datetime.now()-start_time
		print(f"Aikaa kulunut: {run_time}")  # Develop only
		print()

		main_power_state = check_main_power()
		# If main power state change -> Save power outage start/end time
		if main_power_state != old_power_state:
			old_power_state = not old_power_state  # Change 0->1 and 1->0
			save_power_outage(main_power_state, batt_percent)
		if not main_power_state or batt_percent <= 95:
			save_ups_log(batt_volt, batt_percent, debug)

		try:
			time.sleep(5)
		except KeyboardInterrupt:
			GPIO.cleanup()
			break
		os.system("clear")

if __name__ == "__main__":
	main()
