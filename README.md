# Internet Of Things Platform
[Micropython](https://github.com/micropython/micropython) based IOT platform is a set of useful tools and utilities to build open source firmware for various devices like LED strip controllers / wall switches / temperature and humidity sensors.

----
### NOTE: development in progress
----

P.S. documentation writing in progress... :)

## Supported devices
1. [Open Source Neopixel ESP8266 based controller](https://easyeda.com/kr.belyalov/WS2812b_led_strip_controller-5b6d9e5de0324d9a89108fcd10161d9e)
2. Soon :)

## Ubuntu
### Build
1. Install required packages
```bash
$ sudo apt-get update
$ sudo apt-get install -y docker.io git python python-yaml esptool
```
2. Clone project (be sure to use `--recursive`):
```bash
$ git clone --recursive https://github.com/belyalov/iot-platform.git
```

3. Enter into project
```bash
$ cd iot-platform/
```

4. Build desired device! :)
```bash
# ./build.py build <device folder>
$ sudo ./build.py build devices/open_neopixel_controller/
```
Firmware is ready!

### Flash firmware
To flash your device with compiled firmware:
```bash
$ esptool --port <UART PORT> --baud 460800 write_flash -fm dout 0 ./_build_neopixel/esp8266/firmware-combined.bin
```