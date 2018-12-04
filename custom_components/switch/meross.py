"""
Adds support for Meross Smart products.
"""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from meross_iot.supported_devices.power_plugs import Mss425e

REQUIREMENTS = ['meross_iot==0.1.2.0']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch from config."""
    from meross_iot.api import MerossHttpClient

    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)

    _LOGGER.debug("Initializing the Meross component")
    meross = MerossHttpClient(email, password)

    devices = []
    for supported_device in meross.list_supported_devices():
        hardware = supported_device.get_sys_data()['all']['system']['hardware']
        model = hardware['type']

        if model == 'mss425e':
            channel_number = 0
            for channel in supported_device.get_channels():
                # The first channel should be ignored for now
                if not channel:
                    continue

                channel_number += 1

                unique_id = "{}-{}".format(hardware['uuid'], channel_number)
                devices.append(MerossMss425eSwitch(supported_device, channel, unique_id, channel_number))
        else:
            _LOGGER.error('Unmapped device found! %s', model)

    async_add_entities(devices, True)


class MerossSwitch(SwitchDevice):
    _enabled = False

    def __init__(self, device, name: str, device_type: str, unique_id: str):
        self._device = device
        self._name = name
        self._device_type = device_type
        self._unique_id = unique_id

    @property
    def should_poll(self):
        """Poll this switch."""
        return True

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def type(self):
        """Return the name of the type."""
        return self._device_type

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._enabled

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon to use for device."""
        return 'mdi:usb' if self._device_type.lower() == 'usb' else 'mdi:power-socket'

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        raise NotImplementedError()

    def turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        raise NotImplementedError()


class MerossMss425eSwitch(MerossSwitch):
    def __init__(self, device: Mss425e, channel, unique_id: str, channel_number: int):
        super().__init__(device, channel['devName'], channel['type'], unique_id)

        self._channel = channel
        self._channel_number = channel_number

        self.update()

    def turn_on(self, **kwargs):
        self._device.turn_on_channel(self._channel_number)
        self._enabled = True

    def turn_off(self, **kwargs):
        self._device.turn_off_channel(self._channel_number)
        self._enabled = False

    def update(self):
        for channel in self._device.get_sys_data()['all']['digest']['togglex']:
            if self._channel_number == channel['channel']:
                self._enabled = channel['onoff'] == 1
