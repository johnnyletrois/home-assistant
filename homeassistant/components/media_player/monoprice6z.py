"""
Support for interfacing with Monoprice Six Zone WHA controller.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.russound_rnet/
"""
import logging

import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET,
    SUPPORT_SELECT_SOURCE, MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_HOST, CONF_PORT, STATE_OFF, STATE_ON, CONF_NAME)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = [
    'https://github.com/johnnyletrois/monoprice6z/archive/0.0.1.zip'
    '#monoprice6z==0.0.1']

_LOGGER = logging.getLogger(__name__)

CONF_ZONES = 'zones'
CONF_SOURCES = 'sources'

SUPPORT_MONOPRICE = SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | \
                     SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE

ZONE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

SOURCE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_PORT): cv.port,
    vol.Required(CONF_ZONES): vol.Schema({cv.positive_int: ZONE_SCHEMA}),
    vol.Required(CONF_SOURCES): vol.All(cv.ensure_list, [SOURCE_SCHEMA]),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Monoprice platform."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    #keypad = config.get('keypad', '70')

    if host is None or port is None:
        _LOGGER.error("Invalid config. Expected %s and %s",
                      CONF_HOST, CONF_PORT)
        return False

    from monoprice6z import monoprice6z

    mono = monoprice6z.Monoprice(host, port)
    mono.connect()

    #sources = []
    #for source in config[CONF_SOURCES]:
    #    sources.append(source['name'])

    if mono.is_connected():
        for zone_id, extra in config[CONF_ZONES].items():
            add_devices([MonopriceDevice(
                hass, mono, sources, zone_id, extra)])
    else:
        _LOGGER.error('Not connected to %s:%s', host, port)


# pylint: disable=abstract-method, too-many-public-methods,
# pylint: disable=too-many-instance-attributes, too-many-arguments
class MonopriceDevice(MediaPlayerDevice):
    """Representation of a Monoprice device."""

    def __init__(self, hass, mono, sources, zone_id, extra):
        """Initialise the Monoprice device."""
        self._name = extra['name']
        self._mono = mono
        self._state = STATE_OFF
        self._sources = sources
        self._zone_id = zone_id
        self._volume = 0

    @property
    def name(self):
        """Return the name of the zone."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_MONOPRICE

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._volume = volume * 100
        self._mono.set_volume('1', self._zone_id, self._volume)

    def turn_on(self):
        """Turn the media player on."""
        self._mono.set_power('1', self._zone_id, '1')
        self._state = STATE_ON

    def turn_off(self):
        """Turn off media player."""
        self._mono.set_power('1', self._zone_id, '0')
        self._state = STATE_OFF

    def mute_volume(self, mute):
        """Send mute command."""
        self._mono.toggle_mute('1', self._zone_id)

    def select_source(self, source):
        """Set the input source."""
        if source in self._sources:
            index = self._sources.index(source)+1
            self._mono.set_source('1', self._zone_id, index)

    @property
    def source_list(self):
        """List of available input sources."""
        return self._sources
