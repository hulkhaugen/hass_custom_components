# Oslo Børs fond sensor

The `ob_fond` sensor platform uses [Oslo Børs](https://www.oslobors.no/) API to monitor funds.

## Installation
In your config folder, there should be a subfolder named `custom_components`. If not, you need to create it. Make a new subfolder named `ob_fond` and copy the files from this repository to that folder: `config/custom_components/ob_fond`.

## Configuration
To enable the `ob_fond` platform, add content such as this example to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: ob_fond
    funds:
      - fund: DK-GLBIX.OSE  # DNB Global Indeks A
        currency: "kr"
      - fund: DK-NORIX.OSE  # DNB Norge Indeks A
      - fund: SP-STBFE.OSE  # Storebrand Fornybar Energi
    scan_interval: 00:15
```

### funds `map, required`
List of funds you want to monitor

### fund `string, required`
Specific funds you want to monitor. The values are taken from the fund's page at [Oslo Børs](https://www.oslobors.no/).
For example DNB Norge Indeks A has the url https://www.oslobors.no/markedsaktivitet/#/details/DK-NORIX.OSE/overview. In that url, use the DK-NORIX.OSE.

### currency `string, optional, default=NOK`
Customize the unit of measurement for the, for instance "kr" instead of the default "NOK"

### scan_interval `time, optional, default=00:10`
Set how often you want the data to refresh. Default is 10 minutes.

## Example
![More info dialogue box](ob_fond_example_more_info.png)
