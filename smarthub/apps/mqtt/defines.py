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

# field used to map zigbee devices to MQTT device
ZIGBEE_DEVICE_IDENTIFIER_FIELD = "ieee_address"
