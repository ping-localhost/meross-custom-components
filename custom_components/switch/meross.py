"""
Adds support for Meross Smart products.
"""
import json
import logging
from functools import partial

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

REQUIREMENTS = ['https://github.com/ping-localhost/MerossIot/archive/support-for-mss425e.zip#meross-iot==0.1.1.3']

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
    httpHandler = MerossHttpClient(email, password)
    
    devices = []
    for supported_device in httpHandler.list_supported_devices():
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
                devices.append(MerossMss425eSwitch(supported_device, channel, channel_number, unique_id))
        else:
            _LOGGER.error('Unmapped device found! %s', model)
        
    async_add_entities(devices, update_before_add=True)

class MerossSwitch(SwitchDevice):
    def __init__(self, name, type, device, unique_id):
        self._name = name
        self._type = type
        self._enabled = False
        self._device = device
        self._unique_id = unique_id
        self._icon = 'mdi:usb' if type.lower() == 'usb' else 'mdi:power-socket'

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
        return self._type

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
        return self._icon

class MerossMss425eSwitch(MerossSwitch):
    def __init__(self, device, channel, channel_number, unique_id):
        super().__init__(channel['devName'], channel['type'], device, unique_id)

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

