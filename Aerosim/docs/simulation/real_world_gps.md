# Real-World GPS Satellite Navigation in AeroSim

AeroSim bridges the simulation coordinate frame with global Earth coordinates using the **WGS-84 World Geodetic System**.

## Coordinate Transformations

### 1. NED (North-East-Down) to WGS-84 GPS
Local simulation coordinates are mapped from North ($x$), East ($y$), and Down ($-z$) relative to a Home Origin $(\phi_0, \lambda_0, h_0)$:

$$\Delta \phi = \frac{x}{R_M + h_0}, \quad \Delta \lambda = \frac{y}{(R_N + h_0) \cos \phi_0}$$

Where $R_M$ is the meridian radius of curvature and $R_N$ is the prime vertical radius of curvature.

### 2. Great-Circle Haversine Distance
The distance $d$ between two global coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ is:

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos \phi_1 \cos \phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2 R_{\text{earth}} \text{atan2}(\sqrt{a}, \sqrt{1-a})$$

## Preset Real-World Locations
- 🇮🇳 New Delhi (India Gate): 28.6129° N, 77.2295° E, Alt 215m
- 🇮🇳 Mumbai (Marine Drive): 18.9220° N, 72.8347° E, Alt 14m
- 🇮🇳 Bengaluru (Electronic City): 12.8452° N, 77.6602° E, Alt 900m
- 🇺🇸 San Francisco (Golden Gate): 37.8024° N, -122.4646° E, Alt 15m
- 🇦🇪 Dubai (Marina): 25.0772° N, 55.1330° E, Alt 8m
- 🇨🇭 Swiss Alps (Interlaken): 46.6863° N, 7.8632° E, Alt 566m
- 🇯🇵 Tokyo (Tokyo Bay): 35.6264° N, 139.7744° E, Alt 6m
