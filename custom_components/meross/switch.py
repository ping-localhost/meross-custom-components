import json
import logging

from homeassistant.components.switch import SwitchDevice
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from meross_iot.supported_devices.power_plugs import Mss425e, Device

from . import DATA_DEVICES, DOMAIN, SIGNAL_DELETE_ENTITY, SIGNAL_UPDATE_ENTITY

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Meross Switch device."""
    if discovery_info is None:
        return

    meross_devices = hass.data[DATA_DEVICES]

    devices = []
    for dev_id in discovery_info.get('device_ids'):
        device = meross_devices[dev_id]
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

                devices.append(Mss425eChannelSwitch(device, channel, channel_number))
        else:
            devices.append(MerossSwitch(device, 'Meross.{}'.format(device.device_id()), 'switch'))

    add_entities(devices)


class MerossSwitch(SwitchDevice):
    _enabled: bool = False

    def __init__(self, device, name: str, device_type: str):
        self._device = device
        self._name: str = name
        self._device_type: str = device_type
        self._device_id: str = device.device_id()

    @property
    def should_poll(self) -> bool:
        """Poll this switch."""
        return True

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
        return self.hass.data[DATA_DEVICES][self.device_id]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        device_id = self.device_id

        self.update()

        self.hass.data[DOMAIN]['entities'][device_id] = self.entity_id
        async_dispatcher_connect(self.hass, SIGNAL_DELETE_ENTITY, self._delete_callback)
        async_dispatcher_connect(self.hass, SIGNAL_UPDATE_ENTITY, self._update_callback)

    @callback
    def _delete_callback(self, device_id) -> None:
        """Remove this entity."""
        if device_id == self.unique_id:
            self.hass.async_create_task(self.async_remove())

    @callback
    def _update_callback(self) -> None:
        """Call update method."""
        self.async_schedule_update_ha_state(True)


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
        return self.hass.data[DATA_DEVICES][self.device_id]

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
