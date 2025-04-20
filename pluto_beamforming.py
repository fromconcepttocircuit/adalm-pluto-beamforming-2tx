#!/usr/bin/env python3
"""
Beamforming demo with ADALM‑Pluto
  · One‑Shot and Continuous sweep modes
  · –3 dB half‑power beam‑width (HPBW) in phase and in spatial angle
  · Peak marker, vertical line, and read‑out
"""

import numpy as np
import adi
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# ---- Qt dashed‑line compatibility (Qt‑5 vs Qt‑6) --------------------------
try:    DASH = QtCore.Qt.DashLine
except AttributeError:
    DASH = QtCore.Qt.PenStyle.DashLine
# ---------------------------------------------------------------------------


def main():
    # ---------- User parameters ----------
    samp_rate        = 2e6
    f_tone           = 500e3
    N                = 4096
    phase_step       = 2            # deg / update
    update_interval  = 40           # ms
    integration_win  = 10           # FFT bins ± around peak
    PAD_DB           = 1.0          # raise magenta label by this (dB)
    spacing_ratio    = 0.5          # d / λ  (0.5 ⇒ elements λ/2 apart)

    # ---------- SDR setup ----------
    sdr_tx = adi.ad9361(uri="ip:192.168.2.1")
    sdr_tx.sample_rate            = int(samp_rate)
    sdr_tx.tx_enabled_channels    = [0, 1]   ### 1
    sdr_tx.tx_rf_bandwidth        = int(1e6)
    sdr_tx.tx_lo                  = int(2.4e9)
    sdr_tx.tx_hardwaregain_chan0  = -40
    sdr_tx.tx_hardwaregain_chan1  = -40
    sdr_tx._rxadc.set_kernel_buffers_count(1)
    sdr_tx.tx_cyclic_buffer       = True

    sdr_rx = adi.ad9361(uri="ip:192.168.2.2")
    sdr_rx.sample_rate            = int(samp_rate)
    sdr_rx.rx_enabled_channels    = [0]
    sdr_rx.rx_rf_bandwidth        = int(1e6)
    sdr_rx.rx_lo                  = int(2.4e9)
    sdr_rx.rx_buffer_size         = 2 ** 12
    sdr_rx._rxadc.set_kernel_buffers_count(1)
    sdr_rx.gain_control_mode      = "manual"
    sdr_rx.rx_gain                = -30
    try:
        sdr_rx._ctrl.attrs["rf_dc_offset_tracking_en"].value = "1"
    except KeyError:
        try:
            sdr_rx._ctrl.attrs["bb_dc_offset_tracking_en"].value = "1"
        except KeyError:
            print("Using software DC offset correction")

    # ---------- Wavelength & element spacing ----------
    c      = 3e8
    fc     = sdr_tx.tx_lo          # carrier ≈ LO
    lam    = c / fc
    d      = spacing_ratio * lam   # element spacing (m)

    # ---------- Baseband tone ----------
    t = np.arange(N) / samp_rate
    base_waveform = 2**14 * 0.5 * np.exp(1j * 2 * np.pi * f_tone * t)  ### 2
    sdr_tx.tx([base_waveform, base_waveform]) ### 3

    # ---------- GUI ----------
    app = QtWidgets.QApplication([])
    win = QtWidgets.QWidget()
    vbox = QtWidgets.QVBoxLayout(); win.setLayout(vbox)

    # Buttons
    hbox = QtWidgets.QHBoxLayout()
    btn_one = QtWidgets.QPushButton("One Shot")
    btn_cont = QtWidgets.QPushButton("Continuous")
    hbox.addWidget(btn_one); hbox.addWidget(btn_cont)
    vbox.addLayout(hbox)

    # FFT plot
    fft_w   = pg.GraphicsLayoutWidget()
    fft_plot = fft_w.addPlot(title="Received Signal FFT")
    fft_plot.setLabel('left',  "Magnitude (linear)")
    fft_plot.setLabel('bottom',"Frequency (Hz)")
    fft_curve  = fft_plot.plot(pen='y')
    pk_marker  = pg.ScatterPlotItem(size=12, brush=pg.mkBrush('r'))
    fft_plot.addItem(pk_marker)
    pk_text    = pg.TextItem(color='r', anchor=(0,1))
    fft_plot.addItem(pk_text)
    vbox.addWidget(fft_w)

    # Amplitude‑vs‑Phase plot
    amp_w   = pg.GraphicsLayoutWidget()
    amp_plot = amp_w.addPlot(title="Integrated Amplitude vs. TX Phase")
    amp_plot.setLabel('left',  "Integrated Amplitude (dB)")
    amp_plot.setLabel('bottom',"TX Phase (°)")
    amp_curve = amp_plot.plot(pen='b', symbol='o')
    vbox.addWidget(amp_w)

    win.show()

    # ---------- Sweep state ----------
    cur_phase = -180
    ph_hist, amp_hist = [], []
    mode = 'one_shot'

    # graphics handles to clear on restart
    beam_line = beam_label = None
    max_line = max_marker = max_label = None

    # ---------- Helper: annotate HPBW & max point ----------
    # … everything above is unchanged …

    def annotate_results():
        nonlocal beam_line, beam_label, max_line, max_marker, max_label
        amps = np.array(amp_hist)
        phases = np.array(ph_hist)
        if amps.size < 5:
            return

        idx_max = np.argmax(amps)
        peak_db = float(amps[idx_max])
        peak_phi = float(phases[idx_max])
        half_db = peak_db - 3

        # −3 dB crossings
        left = phases[0]
        for i in range(idx_max - 1, -1, -1):
            if amps[i] < half_db:
                left = np.interp(half_db, [amps[i], amps[i + 1]],
                                 [phases[i], phases[i + 1]])
                break
        right = phases[-1]
        for i in range(idx_max + 1, len(amps)):
            if amps[i] < half_db:
                right = np.interp(half_db, [amps[i - 1], amps[i]],
                                  [phases[i - 1], phases[i]])
                break
        hpbw_phase = right - left

        # spatial HPBW
        s_left = np.clip((np.deg2rad(left) * lam) / (2 * np.pi * d), -1, 1)
        s_right = np.clip((np.deg2rad(right) * lam) / (2 * np.pi * d), -1, 1)
        theta_l = np.degrees(np.arcsin(s_left))
        theta_r = np.degrees(np.arcsin(s_right))
        hpbw_theta = theta_r - theta_l

        # clear old graphics
        for itm in (beam_line, beam_label, max_line, max_marker, max_label):
            if itm: amp_plot.removeItem(itm)

        # HPBW dashed line & label
        beam_line = amp_plot.plot([left, right], [half_db, half_db],
                                  pen=pg.mkPen('g', width=2, style=DASH))
        beam_label = pg.TextItem(
            f"HPBW: {hpbw_phase:.0f}° φ\n≈ {hpbw_theta:.0f}° θ",
            color='g', anchor=(1, 1.2))  # right‑aligned, under line
        amp_plot.addItem(beam_label)
        beam_label.setPos(left, half_db)

        # Max‑point marker, vertical line, label (below curve)
        min_db = float(np.min(amps))
        max_line = amp_plot.plot([peak_phi, peak_phi], [min_db, peak_db],
                                 pen=pg.mkPen('m', width=1))
        max_marker = pg.ScatterPlotItem([peak_phi], [peak_db],
                                        size=10, brush=pg.mkBrush('m'))
        amp_plot.addItem(max_marker)

        max_label = pg.TextItem(f"φ={peak_phi:.0f}°\nA={peak_db:.1f} dB",
                                color='m', anchor=(0.5, 1.2))  # centre, below
        amp_plot.addItem(max_label)
        max_label.setPos(peak_phi+ 9*PAD_DB, peak_db - 3*PAD_DB)  # lowered

    # … everything below is unchanged …

    # ---------- Main update loop ----------
    def update():
        nonlocal cur_phase
        # TX with phase offset
        sdr_tx.tx_destroy_buffer()
        sdr_tx.tx([base_waveform,
                   base_waveform * np.exp(1j*np.deg2rad(cur_phase))]) ### 4

        # Flush then read RX
        for _ in range(20):
            sdr_rx.rx()
        samples = sdr_rx.rx() - np.mean(sdr_rx.rx())
        samples /= 2**11

        # FFT
        win_fn = np.hanning(len(samples))
        fftd   = np.fft.fft(samples * win_fn) / np.sum(win_fn)
        mag    = np.abs(np.fft.fftshift(fftd))
        freq   = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/samp_rate))

        fft_curve.setData(freq, mag)
        idx_pk  = np.argmax(mag)
        pk_f    = float(freq[idx_pk])
        pwr_lin = np.sqrt(np.sum(mag[max(0, idx_pk-integration_win):
                                     idx_pk+integration_win+1]**2))
        pk_marker.setData([pk_f], [pwr_lin])
        pk_text.setText(f"{pk_f:.1f} Hz\n{pwr_lin:.1f}")
        pk_text.setPos(pk_f, pwr_lin)

        # record sweep point
        ph_hist.append(cur_phase)
        amp_hist.append(20*np.log10(pwr_lin))
        amp_curve.setData(ph_hist, amp_hist)

        # advance phase
        cur_phase += phase_step
        if cur_phase > 180:
            annotate_results()                      # sweep finished
            if mode == 'continuous':
                QtCore.QTimer.singleShot(update_interval, start_sweep)
            return
        else:
            QtCore.QTimer.singleShot(update_interval, update)

    # ---------- Control helpers ----------
    def start_sweep():
        nonlocal cur_phase, ph_hist, amp_hist
        nonlocal beam_line, beam_label, max_line, max_marker, max_label
        cur_phase = -180
        ph_hist.clear(); amp_hist.clear()
        for itm in (beam_line, beam_label, max_line, max_marker, max_label):
            if itm: amp_plot.removeItem(itm)
        beam_line = beam_label = max_line = max_marker = max_label = None
        QtCore.QTimer.singleShot(0, update)

    def one_shot():
        nonlocal mode
        mode = 'one_shot'
        start_sweep()

    def continuous():
        nonlocal mode
        mode = 'continuous'
        start_sweep()

    btn_one.clicked.connect(one_shot)
    btn_cont.clicked.connect(continuous)

    app.exec()


if __name__ == "__main__":
    main()
