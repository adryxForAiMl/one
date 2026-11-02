# Quadcopter Physics & Equations of Motion

AeroSim computes the non-linear rigid body dynamics of a multirotor in 6 degrees of freedom (6-DOF).

## 1. Translational Dynamics
The acceleration in the local inertial NED frame is given by:

$$m \ddot{\mathbf{p}} = \mathbf{F}_{\text{thrust}} + \mathbf{F}_{\text{gravity}} + \mathbf{F}_{\text{drag}}$$

Where:
- $m$: Total vehicle mass (1.35 kg)
- $\mathbf{F}_{\text{gravity}} = [0, 0, -m g]^T$ with $g = 9.81 \text{ m/s}^2$
- $\mathbf{F}_{\text{drag}} = -C_d (\mathbf{v} - \mathbf{v}_{\text{wind}}) \|\mathbf{v} - \mathbf{v}_{\text{wind}}\|$
- $\mathbf{F}_{\text{thrust}}$ is rotated from the body frame to the world frame by the rotation matrix $R(\phi, \theta, \psi)$.

## 2. Rotational Dynamics
Using Euler's equations of rotational motion:

$$\mathbf{I} \dot{\boldsymbol{\omega}} + \boldsymbol{\omega} \times (\mathbf{I} \boldsymbol{\omega}) = \boldsymbol{\tau}_{\text{control}} - C_{\text{rot}} \boldsymbol{\omega}$$

Where:
- $\mathbf{I} = \text{diag}(I_{xx}, I_{yy}, I_{zz})$ is the inertia tensor
- $\boldsymbol{\tau}_{\text{control}} = [\tau_{\text{roll}}, \tau_{\text{pitch}}, \tau_{\text{yaw}}]^T$

## 3. Quad-X Motor Mixing Matrix
For an X configuration with arm length $d$:
- $\tau_{\text{roll}} = \frac{d}{\sqrt{2}} (-T_1 + T_2 - T_3 + T_4)$
- $\tau_{\text{pitch}} = \frac{d}{\sqrt{2}} (T_1 + T_2 - T_3 - T_4)$
- $\tau_{\text{yaw}} = c_{\tau} (T_1 - T_2 - T_3 + T_4)$
- Total Thrust $T_{\text{total}} = T_1 + T_2 + T_3 + T_4$

## 4. Motor Dynamics
Each motor is modeled as a first-order lag with maximum RPM $\Omega_{\text{max}}$:

$$\dot{\Omega}_i = \frac{1}{\tau_m} (\Omega_{\text{target}, i} - \Omega_i)$$

$$\text{Thrust } T_i = k_T \left(\frac{\Omega_i}{\Omega_{\text{max}}}\right)^2$$
