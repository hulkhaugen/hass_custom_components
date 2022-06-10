"""Data from Morningstar"""
import asyncio
from datetime import timedelta
import logging

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_CURRENCY,
    CONF_SCAN_INTERVAL
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by Morningstar"
CONF_FUNDS = "funds"
DOMAIN = "morningstar"

DEFAULT_CURRENCY = "kr"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

URL = "https://www.morningstar.no/no/funds/snapshot/snapshot.aspx?id={}"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FUNDS): vol.All(cv.ensure_list),
        vol.Optional(CONF_CURRENCY, default=DEFAULT_CURRENCY): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Morningstar sensor."""
    _LOGGER.info("Setting up sensor")
    session = async_get_clientsession(hass)
    funds = config.get(CONF_FUNDS, [])
    unit_of_measurement = config.get(CONF_CURRENCY)

    for fund in funds:
        try:
            _LOGGER.info("Configuring fund %s", fund)
            if " " not in fund:
                async_add_entities([MorningstarSensor(session, fund, unit_of_measurement)], True)
            else:
                _LOGGER.error("Values for 'funds:' can not contain spaces, found '%s'", fund)
        except ValueError:
            _LOGGER.error("Error loading fund %s, please check config", fund)

    _LOGGER.info("Setup of Morningstar is complete")


class MorningstarSensor(Entity):
    """Representation of Morningstar sensor."""

    def __init__(self, session, fund, unit_of_measurement):
        """Initialize Morningstar sensor."""
        self._fund = fund
        self._session = session
        self._unit_of_measurement = unit_of_measurement
        self._state = None
        self._name = ""
        self._icon = "mdi:timer-sand-empty"
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def fund(self):
        """Return the url of the sensor."""
        return self._fund

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the device."""
        return self._attrs

    @property
    def icon(self):
        """Return icon to use based on performance."""
        return self._icon

    async def async_update(self):
        """Get the latest data from the source and updates the state."""
        try:
            with async_timeout.timeout(10):
                response = await self._session.get(URL.format(self._fund))
            _LOGGER.debug("Response from Morningstar: %s", response.status)
            html = await response.text()
            #_LOGGER.debug(html)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Unable to load data from Morningstar")
            return

        soup = BeautifulSoup(html, "html.parser")
        stats = soup.find("table", attrs={"class": "overviewKeyStatsTable"})
        historical = soup.find("table", attrs={"class": "overviewTrailingReturnsTable"})

        try:
            self._attrs["Dato"] = historical.find("td", attrs={"class": "heading date"}).text
            self._attrs["1 dag"] = float(stats.select("tr:nth-of-type(3) > td.text")[0].text.replace("%\n", "").replace(",", "."))
            historical = [[td.text for td in tr.select('td')] for tr in historical.select('tr')][1:]
            historical = {item[0]: float(item[1].replace(',', '.')) for item in historical if item[1] != '-'}
            self._attrs.update(historical)
            self._name = soup.h1.text
            self._state = float(stats.select("tr:nth-of-type(2) > td.text")[0].text[4:].replace(",", "."))
            self._icon = 'mdi:trending-up' if self._attrs["1 dag"] > 0 else 'mdi:trending-down' if self._attrs["1 dag"] < 0 else 'mdi:trending-neutral'
            _LOGGER.info("Successfully scraped '%s' data from Morningstar", self._name)
        except IndexError:
            _LOGGER.error("Unable to extract data from Morningstar")
            return
