from datetime import timedelta
import json
import logging
import urllib.request
import urllib.error

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_CURRENCY,
    # CONF_PREFIX,
    CONF_SCAN_INTERVAL
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_FUND = "fund"
CONF_FUNDS = "funds"

ATTRIBUTION = "Fund data provided by Oslo Børs (Oslo Stock Exchange)"

# DEFAULT_PREFIX = "fond"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)

FUND_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FUND): cv.string,
        vol.Optional(CONF_CURRENCY): cv.string
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FUNDS): vol.All(cv.ensure_list, [FUND_SCHEMA]),
        # vol.Optional(CONF_PREFIX, default=DEFAULT_PREFIX): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
    }
)

API_URL = (
    "https://www.oslobors.no/ob/servlets/components?filter=ITEM_SECTOR==s{}&source=feed.omff.FUNDS&columns=" +
    "SECURITYNAME+as+LONG_NAME,PRICE,DATE,PRICECHANGEPCT,RET1WEEK,RET1M,RET3M,RET6M,RETY2D," +
    "RETGAVG1YR,RETGAVG2YR,RETGAVG3YR,RETGAVG4YR,RETGAVG5YR,RETGAVG7YR,RETGAVG10YR,RETGAVG20YR," +
    "MANAGEMENTFEE,MAXREDEMPTIONFEE,MAXSALECHARGE,BENCHMARKNAME,QUOTATIONCURRENCY"
)


def api_request(query):
    """Setup the API query engine."""
    try:
        with urllib.request.urlopen(API_URL.format(query)) as api_response:
            return json.loads(api_response.read())
    except urllib.error.HTTPError:
        _LOGGER.error("HTTP Error requesting %s, please check spelling.", query)
        return


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the OB_Fond component. """
    funds = config.get(CONF_FUNDS, [])

    if not funds:
        err_msg = "No funds configured."
        hass.component.persistent_notification.create(err_msg, "Sensor ob_fond")
        _LOGGER.warning(err_msg)
        return

    sensors = []
    for fund in funds:
        try:
            _LOGGER.debug("Configuring fund %s", fund[CONF_FUND])
            if " " not in fund[CONF_FUND]:
                if api_request(fund[CONF_FUND]):
                    sensors.append(OBFondSensor(fund))
            else:
                _LOGGER.error("Values for 'fund:' can not contain spaces, found '%s'", fund[CONF_FUND])
        except ValueError:
            _LOGGER.error("Error loading fund %s, please check config", fund[CONF_FUND])

    add_entities(sensors, True)
    _LOGGER.info("Setup of funds complete")


class OBFondSensor(Entity):
    """Representation of a Oslo Børs Fond sensor."""

    def __init__(self, fund):
        self._fund = fund[CONF_FUND]
        # self._prefix = config.get(CONF_PREFIX)
        self._unit_of_measurement = fund.get(CONF_CURRENCY, "kr")
        self._api_data = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._api_data["rows"][0]["values"]["LONG_NAME"]

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._api_data["rows"][0]["key"]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def state_attributes(self):
        """Return the state attributes."""
        osedate = self._api_data["rows"][0]["values"]["DATE"]
        date = f"{osedate[6:8]}.{osedate[4:6]}.{osedate[0:4]}"

        attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "Dato": date,
            "Forvaltningshonorar": str(self._api_data["rows"][0]["values"]["MANAGEMENTFEE"]) + " %",
            "Kjøpsavgift": str(self._api_data["rows"][0]["values"]["MAXREDEMPTIONFEE"]) + " %",
            "Salgsavgift": str(self._api_data["rows"][0]["values"]["MAXSALECHARGE"]) + " %",
            "Referanseindeks": self._api_data["rows"][0]["values"]["BENCHMARKNAME"],
            "Intradag": str(self._api_data["rows"][0]["values"]["PRICECHANGEPCT"]) + " %"
        }

        apikeys = (
            "RET1WEEK", "RET1M", "RET3M", "RET6M", "RETY2D", "RETGAVG1YR", "RETGAVG2YR",
            "RETGAVG3YR", "RETGAVG4YR", "RETGAVG5YR", "RETGAVG7YR", "RETGAVG10YR", "RETGAVG20YR"
            )
        attr = (
            "Uke", "Måned", "3 Måneder", "6 Måneder", "Hittil i år",
            "1 år", "2 år", "3 år", "4 år", "5 år", "7 år", "10 år", "20 år"
            )

        for index, data in enumerate(apikeys):
            if self._api_data["rows"][0]["values"][data]:
                attributes[attr[index]] = str(self._api_data["rows"][0]["values"][data]) + " %"

        return attributes

    @property
    def state(self):
        """Return the state of the device."""
        return round(self._api_data["rows"][0]["values"]["PRICE"], 2)

    @property
    def icon(self):
        """Return icon to use based on preformance."""
        iconvalue = self._api_data["rows"][0]["values"]["PRICECHANGEPCT"]
        if iconvalue > 0:
            return "mdi:arrow-top-right-thick"
        elif iconvalue < 0:
            return "mdi:arrow-bottom-right-thick"
        elif iconvalue == 0:
            return "mdi:arrow-right-thick"
        else:
            return "mdi:alert-circle"

    def update(self):
        _LOGGER.debug("Requesting new data for %s", self._fund)
        api_data = api_request(self._fund)
        self._api_data = api_data
        _LOGGER.info(
            "Data updated for fund %s (%s)", self._fund, self._api_data["rows"][0]["values"]["LONG_NAME"]
            )
