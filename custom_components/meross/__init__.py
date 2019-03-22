import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.async_ import run_coroutine_threadsafe

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['meross_iot', 'paho-mqtt']

DOMAIN = 'meross'
SCAN_INTERVAL = timedelta(seconds=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up The MerossIot Component."""

    hass.data[DOMAIN] = Meross(config)

    for component in ['switch']:
        load_platform(hass, component, DOMAIN, {}, config)

    def update_devices(event_time):
        """Refresh"""
        _LOGGER.debug("Updating devices status")

        run_coroutine_threadsafe(hass.data[DOMAIN].async_update(), hass.loop)

    async_track_time_interval(hass, update_devices, SCAN_INTERVAL)

    return True


class Meross():
    def __init__(self, config):
        from meross_iot.api import MerossHttpClient

        self._username = config.get(DOMAIN, {}).get(CONF_USERNAME, '')
        self._password = config.get(DOMAIN, {}).get(CONF_PASSWORD, '')

        self._client = MerossHttpClient(email=self._username, password=self._password)
        self._devices = self._client.list_supported_devices()

    def update_devices(self):
        self._devices = self._client.list_supported_devices()

        return self._devices

    def get_devices(self, force_update=False):
        if force_update:
            return self.update_devices()

        return self._devices

    def get_device(self, device_id):
        for device in self.get_devices():
            if device.device_id() == device_id:
                return device

    async def async_update(self):
        return self.update_devices()
