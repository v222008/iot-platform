# Internet Of Things Platform
[Micropython](https://github.com/micropython/micropython) based IOT platform is a set of useful tools and utilities to build open source firmware for various devices like LED strip controllers / wall switches / temperature and humidity sensors.

----
### NOTE: Currently project is in development stage, this is not even Alpha version.
----

P.S. documentation writing in progress... :)

## Supported devices
1. [Open Source Neopixel ESP8266 based controller](https://easyeda.com/kr.belyalov/WS2812b_led_strip_controller-5b6d9e5de0324d9a89108fcd10161d9e)
2. [Open Source In-Wall 2SSR Switch](https://easyeda.com/kr.belyalov/wall_switch)
3. (Magic LED controller coming soon)
4. (ESP8266 Weather Station coming soon)

## Ubuntu
### Build
1. Install required packages
```bash
$ sudo apt-get update
$ sudo apt-get install -y docker.io git python3 python3-yaml esptool
```
2. Clone project (be sure to use `--recursive`):
```bash
$ git clone --recursive https://github.com/belyalov/iot-platform.git
```

3. Enter into project
```bash
$ cd iot-platform/
```

4. Add yourself to docker group (you don't want to run it from `root`, likely)
```bash
# Add current user to "docker" group
sudo usermod -a -G docker $USER

# You've been added to group, but, you current session will not be updated
# So you need to relogin / open new session, like:
su - $USER
```

4. Build desired device! :)
```bash
# ./build.py build <device folder>
# Open Source Neopixel Controller
$ ./build.py build devices/open_neopixel_controller/

# Open Source In-Wall SSR Switch
$ ./build.py build devices/open_wifi_switch/
```
Firmware is ready!

### Flash firmware
To flash your device with compiled firmware:
```bash
# Open Source Neopixel
$ esptool --port <UART PORT> --baud 460800 write_flash -fm dout 0 ./_build_neopixel/open_neopixel_controller.bin

# Open Source In-Wall switch
$ esptool --port <UART PORT> --baud 460800 write_flash -fm dout 0 ./_build_wifi_switch/open_wifi_switch.bin
```