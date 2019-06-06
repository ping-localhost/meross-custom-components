import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import load_platform
from meross_iot.cloud.devices.power_plugs import GenericPlug
from meross_iot.manager import MerossManager
from meross_iot.meross_event import MerossEventType

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['meross_iot']

DOMAIN = 'meross'
SCAN_INTERVAL = timedelta(seconds=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up The MerossIot Component."""
    hass.data[DOMAIN] = Meross(config)

    for component in ['switch']:
        load_platform(hass, component, DOMAIN, {}, config)

    return True


class Meross():
    from custom_components.meross.switch import MerossSwitch

    def __init__(self, config):
        self._email = config.get(DOMAIN, {}).get(CONF_EMAIL, '')
        self._password = config.get(DOMAIN, {}).get(CONF_PASSWORD, '')

        self._client = MerossManager(meross_email=self._email, meross_password=self._password)
        self._devices = self._client.get_devices_by_kind(GenericPlug)
        self._entities = []

        self._client.register_event_handler(self.event_handler)
        self._client.start()

    def add_entity(self, meross_switch: MerossSwitch):
        self._entities.count(meross_switch) == 0 and self._entities.append(meross_switch)

    def remove_entity(self, meross_switch: MerossSwitch):
        self._entities.count(meross_switch) != 0 and self._entities.remove(meross_switch)

    def get_entities(self):
        return self._entities

    def update_devices(self):
        self._devices = self._client.get_devices_by_kind(GenericPlug)

        return self._devices

    def get_entity(self, device_id, channel_number=0):
        for device in self._entities:
            if device.device_id != device_id:
                continue

            if channel_number == 0:
                return device

            if device.channel_number == channel_number:
                return device

    def get_devices(self, force_update=False):
        if force_update:
            return self.update_devices()

        return self._devices

    def event_handler(self, event):
        if event.event_type == MerossEventType.DEVICE_ONLINE_STATUS:
            _LOGGER.debug("Device online status changed: %s went %s" % (event.device.name, event.status))
            pass
        elif event.event_type == MerossEventType.DEVICE_SWITCH_STATUS:
            _LOGGER.debug("Switch state changed: Device %s (channel %d)" % (event.device.name, event.channel_id))
            device = self.get_entity(event.device.uuid, event.channel_id)
            if device is None:
                return

            device.update_status()
            device.schedule_update_ha_state()
        elif event.event_type == MerossEventType.CLIENT_CONNECTION:
            _LOGGER.debug("Connection change has happened: %s" % event.status)
        else:
            _LOGGER.debug("Unknown event: %s" % event.event_type)
