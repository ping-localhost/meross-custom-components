# Custom components for Home Assistant
## Meross Smart Device Component

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

