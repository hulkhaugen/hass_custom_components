"""Data from Morningstar"""
import asyncio
import logging
from datetime import timedelta

import aiohttp
import async_timeout
import voluptuous as vol
from bs4 import BeautifulSoup

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_CURRENCY, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by Morningstar"
CONF_FUNDS = "funds"
CONF_LT_FUNDS = "lt_funds"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
DOMAIN = "morningstar"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        # Figure out a way to require only one, but both can be used simultanoiusly
        vol.Optional(CONF_FUNDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_LT_FUNDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_CURRENCY, default="0"): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    }
)


async def async_scrape(session: object, fund: str, url: str) -> BeautifulSoup:
    """Download data from Morningstar and parse it with BeautifulSoup."""
    try:
        with async_timeout.timeout(10):
            response = await session.get(url.format(fund))
    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.warning("Unable to scrape data for %s", fund)
        return None
    html = await response.text()
    _LOGGER.info("Response from Morningstar for %s: %s", fund, response.status)
    return BeautifulSoup(html, "html.parser")


async def async_morningstar(session: object, fund: str) -> dict:
    """Initiate the scraper and process the data."""
    url = "https://www.morningstar.no/no/funds/snapshot/snapshot.aspx?id={}"
    try:
        soup = await async_scrape(session, fund, url)
        name = soup.h1.text
        keys = soup.find("table", attrs={"class": "overviewKeyStatsTable"})
        hist = soup.find("table", attrs={"class": "overviewTrailingReturnsTable"})
        stat = keys.select("tr:nth-of-type(2) > td.text")[0].text[4:].replace(",", ".")
        unit = keys.select("tr:nth-of-type(2) > td.text")[0].text[:3]
        date = hist.find("td", attrs={"class": "heading date"}).text
        oday = float(
            keys.select("tr:nth-of-type(3) > td.text")[0]
            .text.replace(",", ".")
            .replace("%\n", "")
        )
        icon = (
            "mdi:trending-up"
            if oday > 0
            else "mdi:trending-down"
            if oday < 0
            else "mdi:trending-neutral"
        )
        attr = {ATTR_ATTRIBUTION: ATTRIBUTION, "Dato": date, "1 dag": f"{oday:.2f} %"}
        hist = [[td.text for td in tr.select("td")] for tr in hist.select("tr")][1:]
        hist = {
            item[0]: f"{float(item[1].replace(',', '.')):.2f} %"
            for item in hist
            if item[1] != "-"
        }
        attr.update(hist)
        attr["URL"] = url.format(fund)
        _LOGGER.info("%s successfully scraped from Morningstar", name)
        return {"name": name, "stat": stat, "unit": unit, "icon": icon, "attr": attr}
    except AttributeError:
        _LOGGER.warning("Unable to extract data from Morningstar for %s", fund)
        return None


async def async_morningstar_lt(session: object, fund: str) -> dict:
    """Initiate the scraper and process the data."""
    url = "https://lt.morningstar.com/cahq7idbwv/snapshot/snapshot.aspx?id={}"
    try:
        soup = await async_scrape(session, fund, url)
        name = soup.h1.text
        stat = soup.select("#KeyStatsLatestNav td")[0].text[4:].replace(",", ".")
        unit = soup.select("#KeyStatsLatestNav td")[0].text[:3]
        pcts = soup.select("#TrailingReturns > table > tbody > tr > td.colSecurity")
        span = soup.select("#TrailingReturns > table > tbody > tr > th")
        date = soup.select("#KeyStatsLatestNav > th > span")[0].text
        oday = float(pcts[1].text.replace(",", "."))
        icon = (
            "mdi:trending-up"
            if oday > 0
            else "mdi:trending-down"
            if oday < 0
            else "mdi:trending-neutral"
        )
        attr = {ATTR_ATTRIBUTION: ATTRIBUTION, "Dato": date}
        hist = {span[i].text: pcts[i].text + " %" for i in range(len(pcts))}
        attr.update(hist)
        attr["URL"] = url.format(fund)
        _LOGGER.info("%s successfully scraped from Morningstar LT", name)
        return {"name": name, "stat": stat, "unit": unit, "icon": icon, "attr": attr}
    except (IndexError, AttributeError):
        _LOGGER.warning("Unable to extract data from Morningstar LT for %s", fund)
        return None


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Morningstar sensor."""
    _LOGGER.info("Setting up sensors")
    session = async_get_clientsession(hass)
    funds = config[CONF_FUNDS]
    lt_funds = config[CONF_LT_FUNDS]
    unit = config.get(CONF_CURRENCY)
    entities = []
    for fund in funds:
        data = await async_morningstar(session, fund)
        if data:
            entities.append(MorningstarSensor(data, fund, unit, True))
    for lt_fund in lt_funds:
        data = await async_morningstar_lt(session, lt_fund)
        if data:
            entities.append(MorningstarSensor(data, lt_fund, unit, False))
    async_add_entities(entities)


class MorningstarSensor(Entity):
    """Initiate the scraper and process the data."""

    def __init__(self, data, fund, unit, morn):
        self._attr = data["attr"]
        self._icon = data["icon"]
        self._name = data["name"]
        self._stat = data["stat"]
        self._unit = data["unit"] if unit == "0" else unit
        self._fund = fund
        self._morn = morn

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID for the sensor."""
        return self._fund

    @property
    def state(self):
        """Return sensor value."""
        return self._stat

    @property
    def unit_of_measurement(self):
        """Return the currency for the sensor."""
        return self._unit

    @property
    def icon(self):
        """Return the sensor icon."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes."""
        return self._attr

    async def async_update(self):
        """Update sensor data."""
        session = async_get_clientsession(self.hass)
        if self._morn:
            data = await async_morningstar(session, self._fund)
        else:
            data = await async_morningstar_lt(session, self._fund)
        if data:
            self._attr = data["attr"]
            self._icon = data["icon"]
            self._name = data["name"]
            self._stat = data["stat"]
        else:
            _LOGGER.warning("Failed to update %s", self._name)
