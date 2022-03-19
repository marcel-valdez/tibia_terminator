# Required libraries

## OCR Scanning

```
sudo apt-get install libleptonica-dev libtesseract-dev tesseract-ocr pipenv
```

Other ways to install pipenv: https://pypi.org/project/pipenv/#Installation

## Python Packages

```
pipenv install
```

## How to bring it up

<!-- TODO: Upload tibia configuration somewhere and make them available
     Import *these* Tibia configuration settings.
-->


1. Set environment variables

```
TIBIA_PID=<the tibia PID>
TERMINATOR_PATH=<directory path where Tibia Terminator is located>
```

2. Configure Tibia Terminator

```
cd "${TERMINATOR_PATH}"

pipenv shell

sudo -E $(which python3.8) -m tibia_terminator.tools.app_config_manager \
 "${TERMINATOR_PATH}/tibia_terminator/app_config.json" \
 find_addresses \
 --tibia_window_config "${TERMINATOR_PATH}/char_configs/tibia_window_config.json" \
 --hotkeys_config "${TERMINATOR_PATH}/char_configs/hotkeys_config.json" \
 --pid ${TIBIA_PID}
```


3. Execute Tibia Terminator

```
cd "${TERMINATOR_PATH}"

pipenv shell

sudo -E $(type -p python3.8) -m tibia_terminator start \
  --app_config_path "$(TERMINATOR_PATH)/tibia_terminator/app_config.json" \
  --char_configs_path "${TERMINATOR_PATH}/char_configs/" \
  --tibia_window_config_path "${TERMINATOR_PATH}/char_configs/tibia_window_config.json" \
  --debug_level 1 \
  ${TIBIA_PID}
```
