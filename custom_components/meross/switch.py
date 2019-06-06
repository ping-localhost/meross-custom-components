import json
import logging

from homeassistant.components.switch import SwitchDevice
from meross_iot.cloud.devices.power_plugs import GenericPlug

from custom_components.meross import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Add the Meross entities"""
    if discovery_info is None:
        return

    meross = hass.data[DOMAIN]  # meros: Meross
    for device in meross.get_devices(force_update=True):
        if device is None:
            continue

        hardware = device.get_sys_data()['all']['system']['hardware']

        _LOGGER.info('Loading Meross device for: %s' % json.dumps(hardware))
        if hardware['type'] == 'mss425e':
            channel_number = 0
            for channel in device.get_channels():
                """Add the whole plug as a normal switch"""
                if not channel:
                    meross.add_entity(MerossSwitch(device, device.name, 'switch'))
                    continue

                """Deal with the channels"""
                channel_number += 1
                meross.add_entity(Mss425eChannelSwitch(device, channel, channel_number))
        else:
            meross.add_entity(MerossSwitch(device, 'Meross.{}'.format(device.uuid), 'switch'))

    async_add_entities(meross.get_entities(), update_before_add=False)


class MerossSwitch(SwitchDevice):
    def __init__(self, device, name: str, device_type: str):
        self._device = device
        self._device_id = device.uuid
        self._name = name
        self._enabled = False
        self._device_type = device_type

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

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
    def channel_number(self) -> int:
        return 0

    @property
    def should_poll(self) -> bool:
        """We receive events so we can use those"""
        return False

    @property
    def type(self) -> str:
        """Return the name of the type."""
        return self._device_type

    @property
    def device_id(self) -> str:
        """Returns the device ID."""
        return self._device_id

    def turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._enabled = True
        self.device() and self.device().turn_on()
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self._enabled = False
        self.device() and self.device().turn_off()
        self.schedule_update_ha_state()

    def device(self) -> GenericPlug:
        return self._device

    def update_status(self) -> None:
        self._enabled = self.device().get_status()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self._device_id = self.device_id

        status = self.device().get_status()
        if status is not None:
            self._enabled = status


class Mss425eChannelSwitch(MerossSwitch):
    def __init__(self, device: GenericPlug, channel, channel_number: int):
        super().__init__(device, channel['devName'], channel['type'])

        self._channel = channel
        self._channel_number = channel_number

    @property
    def is_on(self) -> bool:
        return self._enabled

    @property
    def unique_id(self) -> str:
        return "{}-{}".format(self.device().uuid, self._channel_number)

    @property
    def channel_number(self) -> int:
        return self._channel_number

    def device(self) -> GenericPlug:
        return self._device

    def turn_on(self, **kwargs) -> None:
        self._enabled = True
        self.device().turn_on_channel(self._channel_number)
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        self._enabled = False
        self.device().turn_off_channel(self._channel_number)
        self.schedule_update_ha_state()

    def update_status(self) -> None:
        self._enabled = self.device().get_status(self._channel_number)

    async def async_added_to_hass(self) -> None:
        for channel in self.device().get_sys_data()['all']['digest']['togglex']:
            if self._channel_number == channel['channel']:
                self._enabled = channel['onoff'] == 1
