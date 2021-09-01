"""Constants used by modules within the MQTT app"""
CACHE_KEY_PREFIX = "mqtt"

# when parsing messages - ignore fields below (i.e. these changing will not invoke event triggers)
MESSAGE_FIELDS_TO_IGNORE = [
    "last_seen",
    # "linkquality",
    # "voltage",
]

# MQTT topic which lists all devices connected to the broker
MQTT_DEVICE_LIST_TOPIC = "zigbee2mqtt/bridge/devices"

# messages from the topics below will be ignored - mainly system messages
MQTT_TOPIC_IGNORE_LIST = [
    "zigbee2mqtt/bridge/info",
    "zigbee2mqtt/bridge/logging",
    "zigbee2mqtt/bridge/groups",
    # "zigbee2mqtt/bridge/config",
]

# the device topic that set's device state - do not include prefix/trailing slash
#   (e.g. [base_topic]/[device_identifer]/[set_state_endpoint])
MQTT_DEVICE_STATE_ENDPOINT = "set"

# command that changes device state
MQTT_STATE_COMMAND = "state"
# value of state command to invoke device toggle (on-to-off/off-to-on)
MQTT_STATE_TOGGLE_VALUE = "TOGGLE"

# field used to map zigbee devices to MQTT device
ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"
