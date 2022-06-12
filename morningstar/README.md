# Morningstar fund sensor

The `morningstar` sensor platform uses the [morningstar.no](https://www.morningstar.no/no/) website to scrape fund data.

## Installation
In your config folder, there should be a subfolder named `custom_components`. If not, you need to create it. Make a new subfolder named `morningstar` and copy the files from this repository to that folder: `config/custom_components/morningstar`.

## Configuration
To enable the `morningstar` platform, add content like this example to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: morningstar
    funds:
      - F00000JORS  # DNB Global Indeks A
      - F00000JORR  # DNB Norge Indeks A
      - F0GBR04NGU  # DNB Teknologi A
    scan_interval: 00:10
    currency: "NOK"
```

### funds `list, required`
List of funds you want to monitor. The values are taken from the fund's page at [morningstar.no](https://www.morningstar.no/no/).
For example DNB Norge Indeks A has the url https://www.morningstar.no/no/funds/snapshot/snapshot.aspx?id=F00000JORR. In that url, use the `F00000JORR` part.

### currency `string, optional, default=kr`
Customize the unit of measurement, for instance "NOK" instead of the default "kr"

### scan_interval `time, optional, default=00:30`
Set how often you want the data to refresh. Default is 30 minutes.

## Example: Simple
![More info dialogue box](morningstar_example_more_info.png)

## Example: Complex
![More info dialogue box](morningstar_example_complex.png)

Setting up one or more accounts, customizing icon color (requires [card-mod](https://github.com/thomasloven/lovelace-card-mod)) based on performance, custom secondary info (requires [secondaryinfo-entity-row](https://github.com/custom-cards/secondaryinfo-entity-row) and [card-tools](https://github.com/thomasloven/lovelace-card-tools)) and automatic notifications on account updates. These mods are best installed using [HACS](https://hacs.xyz/).

```yaml
# Example configuration.yaml
sensor:
  - platform: morningstar
    funds:
      - F00000JORS  # DNB Global Indeks A
      - F0GBR04NGU  # DNB Teknologi A
    scan_interval: 00:15

input_text:
  ask_dnb_global_indeks_a:
    name: "ASK DNB Global Indeks A"
    initial: 123.4567
  ask_dnb_teknologi_a:
    name: "ASK DNB Teknologi A"
    initial: 250.0000

template:
  - sensor:
    - name: "Aksjesparekonto"
      unique_id: "ask_account"
      unit_of_measurement: "kr"
      state: "{{('{0:.2f}'.format(
        (states('input_text.ask_dnb_global_indeks_a')|float * states('sensor.dnb_global_indeks_a')|float) +
        (states('input_text.ask_dnb_teknologi_a')|float * states('sensor.dnb_teknologi_a')|float)
        ))}}"
      attributes:
        DNB Global Indeks A: "{{ state_attr('sensor.dnb_global_indeks_a', '1 dag') }}"
        DNB Teknologi A: "{{ state_attr('sensor.dnb_teknologi_a', '1 dag') }}"

automation:
  - id: fondskonto
    alias: "Fondskontoer - oppdatering"
    trigger:
    - platform: state
      entity_id: sensor.fond_ask
    mode: restart
    action:
    - delay: "00:15:00"
    - service: notify.html5_pixel_4a
      data:
        title: Fondskontoer
        message: "Aksjesparekonto: {{ states('sensor.aksjesparekonto') }} kr

          DNB Global Indeks: {{ state_attr('sensor.dnb_global_indeks_a', '1 dag') }} %

          DNB Teknologi A: {{ state_attr('sensor.dnb_teknologi_a', '1 dag') }} %"
        data:
          tag: morningstar-update
          url: https://www.morningstar.no/no/portfoliomanager/portfolio.aspx
```
```yaml
# Example lovlace card configuration
title: Fond
type: entities
entities:
  - entity: sensor.aksjesparekonto
    secondary_info: last-changed
  - entity: sensor.dnb_global_indeks_a
    type: custom:secondaryinfo-entity-row
    secondary_info: '[[ {entity}.attributes.Dato ]], [[ {entity}.attributes.1 dag ]] %'
    card_mod:
      style: |
        :host {
          --paper-item-icon-color:
            {% if state_attr(config.entity,'icon') == "mdi:trending-up" %}
              var(--label-badge-green)
            {% elif state_attr(config.entity,'icon') == "mdi:trending-down" %}
              var(--label-badge-red)
            {% else %}
              var(--paper-item-icon-color)
            {% endif %}
            ;
        }
  - entity: sensor.dnb_teknologi_a
    type: custom:secondaryinfo-entity-row
    secondary_info: '[[ {entity}.attributes.Dato ]], [[ {entity}.attributes.1 dag ]] %'
    card_mod:
      style: |
        :host {
          --paper-item-icon-color:
            {% if state_attr(config.entity,'icon') == "mdi:trending-up" %}
              var(--label-badge-green)
            {% elif state_attr(config.entity,'icon') == "mdi:trending-down" %}
              var(--label-badge-red)
            {% else %}
              var(--paper-item-icon-color)
            {% endif %}
            ;
        }
```
