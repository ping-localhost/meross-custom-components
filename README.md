# Meross Smart Device Component

This component exposes support Meross Smart Devices to your Home Assistant instance.

**Currently supported devices**:
- [Smart Wi-Fi Surge Protector - MSS425e](http://www.meross.com/products/home_automation/smart_wi_fi_surge_protect/30.html)
- All other plugs should be supported as well

## Requirements
This component is using a release candidate off `meross-iot`  by [Alberto Geniola](https://github.com/albertogeniola/MerossIot).
- On [Hassio](https://www.home-assistant.io/hassio/) (i.e., Home Assistant for Raspberry pi) the requirements will be installed automatically
    - Be sure to copy the `manifest.json`, otherwise Hassio doesn't know what to install
- On other [Home Assistant](https://www.home-assistant.io/getting-started/) installations the dependencies need to be installed [manually](https://github.com/albertogeniola/MerossIot#installation). 

## Configuration variables:
Just add your credentials to `configuration.yaml`, both of these are mandatory:
- **email** (Required): Your e-mail address for your Meross account<br />
- **password** (Required): Your password for your Meross account<br />

### Example:
``` yaml
meross:
  email: e@mail.com
  password: !secret meross_password
```

## Performances
This component is event-based (thanks to the new event handler), so it should be pretty instant. However, there are a few caveats: 
1. Adding/removing a device from your Meross account won't be detected until after a reboot.
2. Other things I haven't thought of yet.
 
I'll try and resolve #1 in the near future, but I don't have any other Meross devices so it's a bit hard. 
If you find any issues I haven't mentioned in the list, please let me know.
