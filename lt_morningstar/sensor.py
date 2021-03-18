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
    CONF_RESOURCE,
    CONF_SCAN_INTERVAL
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by Morningstar"

DEFAULT_CURRENCY = "kr"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=20)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RESOURCE): cv.url,
        vol.Optional(CONF_CURRENCY, default=DEFAULT_CURRENCY): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Morningstar sensor."""
    _LOGGER.info("Setting up sensor")
    session = async_get_clientsession(hass)
    resource = config.get(CONF_RESOURCE)
    unit_of_measurement = config.get(CONF_CURRENCY)

    async_add_entities([MorningstarSensor(session, resource, unit_of_measurement)], True)
    _LOGGER.info("Setup complete")


class MorningstarSensor(Entity):
    """Representation of Morningstar sensor."""

    def __init__(self, session, resource, unit_of_measurement):
        """Initialize Morningstar sensor."""
        self._resource = resource
        self._session = session
        self._state = None
        self._name = ""
        self._icon = "mdi:timer-sand-empty"
        self._unit_of_measurement = unit_of_measurement
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def resource(self):
        """Return the url of the sensor."""
        return self._resource

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return self._attrs

    @property
    def icon(self):
        """Return icon to use based on performance."""
        return self._icon

    async def async_update(self):
        """Get the latest data from the source and updates the state."""
        try:
            with async_timeout.timeout(10, loop=self.hass.loop):
                response = await self._session.get(self._resource)
            _LOGGER.debug("Response from Morningstar: %s", response.status)
            html = await response.text()
            #_LOGGER.debug(html)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Unable to load data from Morningstar")
            return

        soup = BeautifulSoup(html, "html.parser")

        try:
            self._attrs["Dato"] = soup.select("#KeyStatsLatestNav > th > span")[0].text
            attributes = {
                "Måned": soup.select("td.number.colSecurity")[1].text,
                "3 måneder": soup.select("td.number.colSecurity")[2].text,
                "6 måneder": soup.select("td.number.colSecurity")[3].text,
                "Hittil i år": soup.select("td.number.colSecurity")[0].text,
                "1 år": soup.select("td.number.colSecurity")[4].text,
                "3 år": soup.select("td.number.colSecurity")[5].text,
                "5 år": soup.select("td.number.colSecurity")[6].text,
                "10 år": soup.select("td.number.colSecurity")[7].text
            }
            attributes = {k: v.replace(",", ".") for k, v in attributes.items()}
            attributes = {k: v + " %" for k, v in attributes.items()}
            title = soup.h1.string
            value = soup.select("#KeyStatsLatestNav td")[0].text.replace("NOK ", "").replace(",", ".")
            iconvalue = float(soup.select("td.number.colSecurity")[1].text.replace(",", "."))
            _LOGGER.info("Successfully scraped '%s' data from Morningstar", title)
        except IndexError:
            _LOGGER.error("Unable to extract data from Morningstar")
            return

        self._state = value
        self._name = title
        self._attrs.update(attributes)
        if iconvalue > 0:
            self._icon = "mdi:arrow-top-right-thick"
        elif iconvalue < 0:
            self._icon = "mdi:arrow-bottom-right-thick"
        elif iconvalue == 0:
            self._icon = "mdi:arrow-right-thick"
        else:
            self._icon = "mdi:alert-circle"
