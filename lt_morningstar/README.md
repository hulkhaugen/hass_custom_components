# NOTE:
This intagration has been depricated as it has been integrated into the main Morningstar sensor. Please use the [Morningstar](https://github.com/hulkhaugen/hass_custom_components/tree/main/morningstar) integration instead.

# Morningstar (LT) fund sensor

This sensor, the *Morningstar Integrated Web Tools* sensor platform uses the [lt.morningstar.com](https://lt.morningstar.com/) website to scrape fund data. This specific version is for unique funds such as pension funds that are not available on the regular Morningstar website and are not searchable. You'll find the links for these types of funds with your bank, broker or similar. If you're looking for a *Morningstar* sensor for regular traded funds, check out the [Morningstar](https://github.com/hulkhaugen/hass_custom_components/tree/main/morningstar) sensor.

<img src="https://github.com/hulkhaugen/hass_custom_components/raw/main/lt_morningstar/lt_morningstar_sensor.jpg" width="360" height="780">

## Installation
In your config folder, there should be a subfolder named `custom_components`. If not, you need to create it. Make a new subfolder named `lt_morningstar` and copy the files from this repository to that folder: `config/custom_components/lt_morningstar`.

## Configuration
To enable the `lt_morningstar` platform, add content like this example to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: lt_morningstar
    funds:
      - F00000N52D  # Pensjonsprofil 50
      - F00000N52F  # Pensjonsprofil 80
      - F00000N52G  # Pensjonsprofil 100
    scan_interval: 00:10
    currency: "NOK"
```

### funds `list, required`
List of funds you want to monitor. Get the link to your funds, and copy the part of the url that comes after `id=` or `SecurityToken=`, it will look something like `F00000N52F`
For example *DNB Pensjonsprofil 100* has the url https://lt.morningstar.com/1vonrmqpe9/snapshot/snapshot.aspx?SecurityToken=F00000N52G%5d2%5d1%5dFOALL%24%24ALL_3642&ClientFund=1&LanguageId=nb-NO&CurrencyId=NOK. In that url, use the `F00000N52G` part.

### currency `string, optional, default=kr`
Customize the unit of measurement, for instance "NOK" instead of the default "kr"

### scan_interval `time, optional, default=00:30`
Set how often you want the data to refresh. Default is 30 minutes.
