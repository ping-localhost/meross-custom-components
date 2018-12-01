# Custom components for Home Assistant
## Meross Smart Device Component

This component exposes support Meross Smart Devices to your Home Assistant instance. It requires `meross-iot` to work.

**Currently supported devices**:
- [Smart Wi-Fi Surge Protector - MSS425e](http://www.meross.com/products/home_automation/smart_wi_fi_surge_protect/30.html)

#### Configuration variables:
**email** (Required): Your e-mail address for your Meross account<br />
**password** (Required): Your password for your Meross account<br />
  
#### Example:
```
switch:
  - platform: meross
    email: e@mail.com
    password: !secret meross_password
```

