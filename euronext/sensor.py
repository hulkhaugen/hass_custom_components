"""Data from Euronext"""
import asyncio
import datetime
import logging

from bs4 import BeautifulSoup
import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_CURRENCY, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
CONF_FUNDS = "funds"
DEFAULT_SCAN_INTERVAL = datetime.timedelta(minutes=15)
DOMAIN = "euronext"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FUNDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_CURRENCY): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    }
)


async def async_api_call(session: object, fund: str):
    data = "theme_name=euronext_live"
    head = {"content-type": "application/x-www-form-urlencoded; charset=UTF-8"}
    html_url = f"https://live.euronext.com/en/ajax/getDetailedQuote/{fund}"
    try:
        async with async_timeout.timeout(10):
            async with session.post(html_url, data=data, headers=head) as html:
                html_text = await html.text()
    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.warning("Unable to scrape data for %s", fund)
        return None
    return BeautifulSoup(html_text, "html.parser")


async def async_get_process_data(session: object, fund: str) -> dict:
    html = await async_api_call(session, fund.upper())
    if not html:
        _LOGGER.info("Failed to retreive data for %s", fund)
        return None
    try:
        """Processing the data to be used"""
        name = html.strong.text
        state = html.find(id="header-instrument-price").text.replace(",", "")
        unit = html.find(id="header-instrument-currency").text.strip()
        # state = "{:.2f}".format(round(float(price), 2))
        date = html.find("div", class_="bg-brand-sky-blue").find("div").find_all("div")
        date = date[1].get_text(strip=True).replace("/", ".")
        day = float(html.find("span", class_="text-ui-grey-1 mr-2").text[1:-2])
        unique = fund.lower()
        url = f"https://live.euronext.com/nb/product/funds/{unique}"
        icon = (
            "mdi:trending-up"
            if day > 0
            else "mdi:trending-down"
            if day < 0
            else "mdi:trending-neutral"
        )
        attr = {
            ATTR_ATTRIBUTION: "Data provided by Euronext",
            # "Pris": price,
            "Dato": date,
            "Endring 1 dag": day,
            "URL": url,
        }
        data = {
            "name": name,
            "unit": unit,
            "state": state,
            "unique": unique,
            "icon": icon,
            "attr": attr,
        }
        _LOGGER.info("Successfully processed data for %s", name)
        return data
    except (IndexError, AttributeError):
        _LOGGER.warning("Unable to process data for %s", fund)
        return None


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("Setting up sensors")
    session = async_get_clientsession(hass)
    funds = config.get(CONF_FUNDS, [])
    currency = config.get(CONF_CURRENCY)
    for fund in funds:
        data = await async_get_process_data(session, fund)
        if not data:
            _LOGGER.error("Failed to setup %s", fund)
            continue
        unit = currency or data["unit"]
        async_add_entities([EuronextLiteSensor(data, fund, unit)])
        _LOGGER.info("Setup of %s complete", data["name"])


class EuronextLiteSensor(Entity):
    """Representation of the sensor."""

    def __init__(self, data: dict, fund: str, unit: str):
        self._attr = data["attr"]
        self._icon = data["icon"]
        self._name = data["name"]
        self._state = data["state"]
        self._unique = data["unique"]
        self._fund = fund
        self._unit = unit

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def icon(self):
        return self._icon

    @property
    def extra_state_attributes(self):
        return self._attr

    async def async_update(self):
        """Update the sensor if weekday between 8:00-23:00."""
        session = async_get_clientsession(self.hass)
        now = datetime.datetime.now()
        if now.weekday() < 5 and 8 <= now.hour < 23:
            data = await async_get_process_data(session, self._fund)
            try:
                self._name = data["name"]
                self._unique = data["unique"]
                self._state = data["state"]
                self._icon = data["icon"]
                self._attr = data["attr"]
                _LOGGER.info("Update of %s complete", self._name)
            except TypeError:
                _LOGGER.warning("Update failed")
