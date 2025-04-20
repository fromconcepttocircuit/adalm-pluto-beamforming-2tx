# 📡 ADALM-Pluto Beamforming Demo

This project demonstrates real-time **RF beamforming** using two ADALM-Pluto SDRs. By enabling dual TX channels on one Pluto and using the second Pluto as a receiver, this Python script sweeps the transmit phase and plots received power—allowing you to **visualize the beam steering effect** in a simple phased array.

[![Watch the video](https://img.youtube.com/vi/YOUR_VIDEO_ID_HERE/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE)

---

## 🚀 Features

- Visual demonstration of beamforming using Python + ADALM-Pluto
- Supports **One-Shot** and **Continuous** phase sweep modes
- Real-time plots:
  - FFT of received signal
  - Integrated received power vs. TX phase
- Automatic calculation of:
  - Peak response direction
  - Half-Power Beam Width (HPBW) in phase and angular space

---

## 🧠 What You'll Learn

- How beamforming steers radio waves using phase control
- Practical use of dual TX channels on ADALM-Pluto for phased array demos
- Signal visualization techniques using PyQtGraph
- Integration of pyadi-iio with SDR hardware

---

## 🛠️ Requirements

- 2x [ADALM-Pluto SDRs](https://www.analog.com/en/design-center/evaluation-hardware-and-software/eval-adalm-pluto.html)
- Pluto firmware supporting dual TX/RX (see [Customizing Guide](https://wiki.analog.com/university/tools/pluto/users/customizing))
- Python 3.7+
- Python packages:
  - `numpy`
  - `pyqtgraph`
  - `adi` (from [pyadi-iio](https://github.com/analogdevicesinc/pyadi-iio))

Install dependencies:
```bash
pip install numpy pyqtgraph adi
```

---

## 📋 How It Works

1. **Pluto #1 (Transmitter):**  
   - Sends a baseband tone from two TX channels.
   - Channel 1’s phase is swept from -180° to +180°.

2. **Pluto #2 (Receiver):**  
   - Measures the received signal.
   - An FFT is performed to extract power at the tone frequency.

3. **GUI Interface:**
   - Real-time plots of FFT spectrum and amplitude vs. phase.
   - Calculations of beam direction and HPBW.

---

## 🧪 Demo

Run the script:

```bash
python pluto_beamforming.py
```

Use the **"One Shot"** button for a single sweep or **"Continuous"** to loop through all phases.

---

## 📎 Notes

- Ensure both Plutos are reachable on your network and have static IPs set to `192.168.2.1` and `192.168.2.2`.
- You must enable dual TX/RX mode on the transmitter Pluto using:
  ```bash
  fw_setenv attr_name compatible
  fw_setenv attr_val ad9361
  fw_setenv compatible ad9361
  fw_setenv mode 2r2t
  reboot
  ```

For more, see the [official Analog Devices customization guide](https://wiki.analog.com/university/tools/pluto/users/customizing).

---

## 📄 License

This project is open-source and licensed under the MIT License.

## 🙌 Contributions and Feedback

If you try this project and have feedback or improvements, **feel free to open an issue or submit a pull request**. Let's make SDR more accessible together!

---

## 🔗 Connect

- **YouTube Channel**: [From Concept To Circuit](https://www.youtube.com/@fromconcepttocircuit)
- **GitHub**: [https://github.com/fromconcepttocircuit](https://github.com/fromconcepttocircuit)
- More RF & SDR projects coming soon!

---
