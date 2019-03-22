import json
import logging

from homeassistant.components.switch import SwitchDevice
from meross_iot.supported_devices.power_plugs import Mss425e, Device

from custom_components.meross import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Add the Sonoff Switch entities"""
    if discovery_info is None:
        return

    entities = []
    for device in hass.data[DOMAIN].get_devices(force_update=True):
        if device is None:
            continue

        hardware = device.get_sys_data()['all']['system']['hardware']
        model = hardware['type']

        _LOGGER.info('Loading Meross device for: ', json.dumps(hardware))

        if model == 'mss425e':
            channel_number = 0
            for channel in device.get_channels():
                if not channel:
                    continue

                channel_number += 1

                entities.append(Mss425eChannelSwitch(device, channel, channel_number))
        else:
            entities.append(MerossSwitch(device, 'Meross.{}'.format(device.device_id()), 'switch'))

    async_add_entities(entities, update_before_add=False)


class MerossSwitch(SwitchDevice):
    def __init__(self, device, name: str, device_type: str):
        self._device = device
        self._name = name
        self._device_type = device_type
        self._device_id = device.device_id()
        self._enabled = False

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def type(self) -> str:
        """Return the name of the type."""
        return self._device_type

    @property
    def is_on(self) -> bool:
        return self._enabled

    @property
    def icon(self) -> str:
        """Return the icon to use for device."""
        if self.type.lower() == 'usb':
            return 'mdi:usb'
        elif self.type.lower() == 'switch':
            return 'mdi:power-socket'
        else:
            return 'mdi:flash'

    @property
    def device_id(self) -> str:
        """Returns the device ID."""
        return self._device_id

    def turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self.device() and self.device().turn_on()

    def turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self.device() and self.device().turn_off()

    def update(self) -> None:
        """Update the entity"""
        if self.device() is None:
            return

        status = self.device().get_status()
        if status is not None:
            self._enabled = status

    def set_state(self, enabled) -> None:
        self._enabled = enabled

    def device(self) -> Device:
        return self._device

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self._device_id = self.device_id

        self.update()


class Mss425eChannelSwitch(MerossSwitch):
    def __init__(self, device: Mss425e, channel, channel_number: int):
        super().__init__(device, channel['devName'], channel['type'])

        self._channel = channel
        self._channel_number = channel_number

    @property
    def is_on(self) -> bool:
        return self._enabled

    @property
    def unique_id(self) -> str:
        return "{}-{}".format(self.device().device_id(), self._channel_number)

    def device(self) -> Mss425e:
        return self._device

    def turn_on(self, **kwargs) -> None:
        self.device() and self.device().turn_on_channel(self._channel_number)
        self._enabled = True

    def turn_off(self, **kwargs) -> None:
        self.device() and self.device().turn_off_channel(self._channel_number)
        self._enabled = False

    def update(self) -> None:
        for channel in self.device().get_sys_data()['all']['digest']['togglex']:
            if self._channel_number == channel['channel']:
                self._enabled = channel['onoff'] == 1
