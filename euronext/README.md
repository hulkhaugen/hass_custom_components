# Euronext fund sensor

The `euronext` sensor uses the [euronext](https://live.euronext.com/nb) website to collect fund data.

## Installation
In your config folder, there should be a subfolder named `custom_components`. If not, you need to create it. Make a new subfolder named `euronext` and copy the files from this repository to that folder: `config/custom_components/euronext`.

## Configuration
To enable the `euronext` platform, add content like this example to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: euronext
    currency: "NOK"
    funds:
      - no0010582984.dkglbix-womf  # DNB Global Indeks A
      - no0010801855.dkmiljn-womf  # DNB Miljøinvest N
      - no0010582976.dknorix-womf  # DNB Norge Indeks A
      - no0010337678.dinotec-womf  # DNB Teknologi A
    scan_interval: 00:10
```

### funds `list, required`
List of funds you want to monitor. The values are taken from the fund's page at [euronext](https://live.euronext.com/nb).
For example DNB Norge Indeks A has the url https://live.euronext.com/nb/product/funds/no0010582976.dknorix-womf/dnb-norge-indeks-a/dk-norix. In that url, use the `no0010582976.dknorix-womf` part.

### currency `string, optional`
Customize the unit of measurement, for instance "kr" instead of what is scraped from the relevant fund, typically "NOK".

### scan_interval `time, optional, default=00:15`
Set how often you want the data to refresh. Default is 15 minutes.
