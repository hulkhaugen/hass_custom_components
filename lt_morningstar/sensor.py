"""Data from Morningstar (LT)"""
import asyncio
from datetime import timedelta
import logging

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (ATTR_ATTRIBUTION, CONF_CURRENCY, CONF_SCAN_INTERVAL)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = 'Data provided by Morningstar'
CONF_FUNDS = 'funds'
DEFAULT_CURRENCY = 'kr'
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
DOMAIN = 'lt_morningstar'
URL = 'https://lt.morningstar.com/cahq7idbwv/snapshot/snapshot.aspx?id={}'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FUNDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_CURRENCY, default=DEFAULT_CURRENCY): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
    }
)


async def async_scape(sess, fund):
    try:
        with async_timeout.timeout(10):
            response = await sess.get(URL.format(fund))
        _LOGGER.info('Response from Morningstar (LT): %s', response.status)
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.info('Unable to scrape data from Morningstar (LT) for %s', fund)
        return

    try:
        name = soup.h1.text
        stat = soup.select('#KeyStatsLatestNav td')[0].text.replace(',', '.')[4:]
        pcts = soup.select('#TrailingReturns > table > tbody > tr > td.colSecurity')
        span = soup.select('#TrailingReturns > table > tbody > tr > th')
        oday = float(pcts[1].text.replace(',', '.'))
        icon = 'mdi:trending-up' if oday > 0 else 'mdi:trending-down' if oday < 0 else 'mdi:trending-neutral'
        attr = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            'Dato': soup.select('#KeyStatsLatestNav > th > span')[0].text
        }
        hist = {span[i].text: pcts[i].text + ' %' for i in range(len(pcts))}
        attr.update(hist)
        attr['URL'] = URL.format(fund)
        data = {'name': name, 'uniq': fund, 'stat': stat, 'icon': icon, 'attr': attr}
        _LOGGER.info('%s Successfully scraped from Morningstar (LT)', name)
        return data
    except (IndexError, AttributeError):
        _LOGGER.warning('Unable to extract data from Morningstar for %s', fund)
        return


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor."""
    _LOGGER.info('Setting up sensors')
    sess = async_get_clientsession(hass)
    funds = config.get(CONF_FUNDS, [])
    unit = config.get(CONF_CURRENCY)
    for fund in funds:
        async_add_entities([MorningstarLtSensor(sess, fund, unit)], True)
        _LOGGER.info('Setup of %s complete', fund[-10:])


class MorningstarLtSensor(Entity):
    """Representation of the sensor."""

    def __init__(self, sess, fund, unit):
        """Initialize the sensor."""
        self._sess = sess
        self._fund = fund
        self._unit = unit
        self._data = None
        self._name = None
        self._uniq = None
        self._stat = None
        self._icon = None
        self._attr = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._uniq

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._stat

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return icon of the sensor."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the sensor."""
        return self._attr

    async def async_update(self):
        """Updates the sensor data."""
        self._data = await async_scape(self._sess, self._fund)
        try:
            self._name = self._data['name']
            self._uniq = self._data['uniq']
            self._stat = self._data['stat']
            self._icon = self._data['icon']
            self._attr = self._data['attr']
            _LOGGER.info('Update of %s complete', self._name)
        except TypeError:
            _LOGGER.info('Update failed')
