import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import discovery
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import track_time_interval
from meross_iot.api import AuthenticatedPostException

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['meross_iot', 'paho-mqtt']

DOMAIN = 'meross'
DATA_MEROSS = 'data_meross'
DATA_DEVICES = 'data_devices'
MEROSS_DEVICE_TYPE = 'switch'

SIGNAL_DELETE_ENTITY = 'meross_delete'
SIGNAL_UPDATE_ENTITY = 'meross_update'

SERVICE_FORCE_UPDATE = 'force_update'
SERVICE_PULL_DEVICES = 'pull_devices'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up The MerossIot Component."""
    from meross_iot.api import MerossHttpClient

    username = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]

    hass.data[DATA_MEROSS] = MerossHttpClient(email=username, password=password)
    hass.data[DOMAIN] = {'entities': {}}

    def load_devices():
        try:
            data = {'extra': {}, 'model': 'Android,Android SDK built for x86_64', 'system': 'Android',
                    'uuid': '493dd9174941ed58waitForOpenWifi', 'vendor': 'Meross', 'version': '6.0'}
            hass.data[DATA_MEROSS]._authenticated_post('https://iot.meross.com/v1/log/user', params_data=data)
        except AuthenticatedPostException:
            _LOGGER.warning("Meross: We have lost our connection/auth! Reconnecting...")
            hass.data[DATA_MEROSS] = MerossHttpClient(email=username, password=password)
            hass.data[DOMAIN] = {'entities': {}}
            hass.data[DATA_DEVICES] = {}

        for device in hass.data[DATA_MEROSS].list_supported_devices():
            hass.data[DATA_DEVICES][device.device_id()] = device

        """Load new devices by device_list."""
        device_type_list = {}
        for device in hass.data[DATA_DEVICES].values():
            if device.device_id() not in hass.data[DOMAIN]['entities']:
                if MEROSS_DEVICE_TYPE not in device_type_list:
                    device_type_list[MEROSS_DEVICE_TYPE] = []

                device_type_list[MEROSS_DEVICE_TYPE].append(device.device_id())
                hass.data[DOMAIN]['entities'][device.device_id()] = None

        for component_type, device_ids in device_type_list.items():
            discovery.load_platform(hass, component_type, DOMAIN, {'device_ids': device_ids}, config)

    load_devices()

    def poll_devices_update(event_time):
        """Check if accesstoken is expired and pull device list from server."""
        _LOGGER.debug("Pull devices from Meross.")

        try:
            data = {'extra': {}, 'model': 'Android,Android SDK built for x86_64', 'system': 'Android',
                    'uuid': '493dd9174941ed58waitForOpenWifi', 'vendor': 'Meross', 'version': '6.0'}
            hass.data[DATA_MEROSS]._authenticated_post('https://iot.meross.com/v1/log/user', params_data=data)
        except AuthenticatedPostException:
            _LOGGER.warning("Meross: We have lost our connection/auth! Reconnecting...")
            hass.data[DATA_MEROSS] = MerossHttpClient(email=username, password=password)
            hass.data[DOMAIN] = {'entities': {}}
            hass.data[DATA_DEVICES] = {}

        # Add new discover device.
        load_devices()

        # Delete not exist device.
        for dev_id in list(hass.data[DOMAIN]['entities']):
            if dev_id not in hass.data[DATA_DEVICES].keys():
                dispatcher_send(hass, SIGNAL_DELETE_ENTITY, dev_id)
                hass.data[DOMAIN]['entities'].pop(dev_id)

    track_time_interval(hass, poll_devices_update, timedelta(minutes=5))

    hass.services.register(DOMAIN, SERVICE_PULL_DEVICES, poll_devices_update)

    def force_update():
        """Force all devices to pull data."""
        dispatcher_send(hass, SIGNAL_UPDATE_ENTITY)

    hass.services.register(DOMAIN, SERVICE_FORCE_UPDATE, force_update)

    return True
